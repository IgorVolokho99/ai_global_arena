import csv
from datetime import datetime
from pathlib import Path

import pygame

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

FLOOR_Y = 450

FPS = 60

GRAVITY_Y = 900

DAMPING = 0.995

SUBSTEPS = 3
CONSTRAINT_ITERATIONS = 8

LEFT_WALL_X = 0
RIGHT_WALL_X = SCREEN_WIDTH

SELECT_RADIUS = 25
PULL_FORCE = 80
KEYBOARD_CONTROL_FORCE = 2500

GROUND_CONTACT_EPSILON = 2

LOG_INTERVAL_SECONDS = 0.1
LOGS_DIR = Path("logs")

MAX_EPISODE_SECONDS = 12
FALL_CONFIRM_SECONDS = 0.5
RESET_DELAY_SECONDS = 1.0

BACKGROUND_COLOR = (25, 30, 30)
DARK_GREY = (60, 60, 70)
LINE_COLOR = (200, 200, 200)

POINT_COLOR = (240, 220, 120)
SELECTED_POINT_COLOR = (255, 100, 100)
FOOT_CONTACT_COLOR = (120, 255, 160)

BONE_COLOR = (220, 220, 230)
PULL_LINE_COLOR = (255, 120, 120)
CENTER_OF_MASS_COLOR = (120, 180, 255)

TEXT_COLOR = (230, 230, 230)
DEBUG_TEXT_COLOR = (170, 220, 255)
FALLEN_TEXT_COLOR = (255, 120, 120)
STANDING_TEXT_COLOR = (120, 255, 160)
LOGGING_TEXT_COLOR = (255, 220, 120)
EPISODE_TEXT_COLOR = (220, 180, 255)


class Point:
    def __init__(self, name, x, y, radius):
        self.name = name

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)

        self.radius = radius
        self.is_touching_floor = False

    def apply_force(self, force):
        self.acceleration += force

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.velocity *= DAMPING

        self.position += self.velocity * dt

        self.acceleration *= 0

    def reset_contact_state(self):
        self.is_touching_floor = False

    def solve_world_collision(self):
        if self.position.y + self.radius >= FLOOR_Y - GROUND_CONTACT_EPSILON:
            self.is_touching_floor = True

        if self.position.y + self.radius > FLOOR_Y:
            self.position.y = FLOOR_Y - self.radius
            self.velocity.y *= -0.4
            self.velocity.x *= 0.9

            if abs(self.velocity.y) < 20:
                self.velocity.y = 0

        if self.position.x - self.radius < LEFT_WALL_X:
            self.position.x = LEFT_WALL_X + self.radius
            self.velocity.x *= -0.4

        if self.position.x + self.radius > RIGHT_WALL_X:
            self.position.x = RIGHT_WALL_X - self.radius
            self.velocity.x *= -0.4

    def draw(self, screen, is_selected=False):
        color = POINT_COLOR

        if self.name in ("Left Foot", "Right Foot") and self.is_touching_floor:
            color = FOOT_CONTACT_COLOR

        if is_selected:
            color = SELECTED_POINT_COLOR

        pygame.draw.circle(
            screen,
            color,
            (int(self.position.x), int(self.position.y)),
            self.radius,
        )

        if is_selected:
            pygame.draw.circle(
                screen,
                SELECTED_POINT_COLOR,
                (int(self.position.x), int(self.position.y)),
                self.radius + 5,
                2,
            )


class Bone:
    def __init__(self, point_a, point_b, length):
        self.point_a = point_a
        self.point_b = point_b
        self.length = length

    def solve(self):
        delta = self.point_b.position - self.point_a.position
        distance = delta.length()

        if distance == 0:
            return

        difference = (distance - self.length) / distance
        correction = delta * 0.5 * difference

        self.point_a.position += correction
        self.point_b.position -= correction

    def draw(self, screen):
        pygame.draw.line(
            screen,
            BONE_COLOR,
            self.point_a.position,
            self.point_b.position,
            4,
        )


class EpisodeManager:
    def __init__(self):
        self.episode_number = 1
        self.episode_time = 0
        self.time_alive = 0
        self.fallen_time = 0

        self.is_episode_over = False
        self.reset_delay_timer = 0

        self.last_end_reason = "None"
        self.last_summary = None

    def update(self, dt, metrics):
        if self.is_episode_over:
            self.reset_delay_timer += dt
            return None

        self.episode_time += dt

        if metrics["is_fallen"]:
            self.fallen_time += dt
        else:
            self.fallen_time = 0
            self.time_alive += dt

        if self.fallen_time >= FALL_CONFIRM_SECONDS:
            return self.end_episode("Fallen", metrics)

        if self.episode_time >= MAX_EPISODE_SECONDS:
            return self.end_episode("Time limit", metrics)

        return None

    def end_episode(self, reason, metrics):
        self.is_episode_over = True
        self.reset_delay_timer = 0
        self.last_end_reason = reason

        self.last_summary = {
            "episode_number": self.episode_number,
            "end_reason": reason,
            "episode_time": round(self.episode_time, 3),
            "time_alive": round(self.time_alive, 3),
            "standing_score": metrics["standing_score"],
            "head_height": round(metrics["head_height"], 2),
            "pelvis_height": round(metrics["pelvis_height"], 2),
            "torso_angle": round(metrics["torso_angle"], 2),
            "left_foot_contact": int(metrics["left_foot_contact"]),
            "right_foot_contact": int(metrics["right_foot_contact"]),
        }

        return self.last_summary

    def should_auto_reset(self):
        return (
            self.is_episode_over
            and self.reset_delay_timer >= RESET_DELAY_SECONDS
        )

    def restart_current_episode(self):
        self.episode_time = 0
        self.time_alive = 0
        self.fallen_time = 0

        self.is_episode_over = False
        self.reset_delay_timer = 0

        self.last_end_reason = "Restarted"

    def start_next_episode(self):
        self.episode_number += 1
        self.restart_current_episode()
        self.last_end_reason = "None"


class FrameLogger:
    def __init__(self):
        self.is_logging = False
        self.file = None
        self.writer = None
        self.file_path = None
        self.time_since_last_log = 0

    def start(self, points):
        LOGS_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = LOGS_DIR / f"ragdoll_frame_log_{timestamp}.csv"

        self.file = open(self.file_path, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=self._get_fieldnames(points),
        )

        self.writer.writeheader()

        self.is_logging = True
        self.time_since_last_log = 0

        print(f"Frame logging started: {self.file_path}")

    def stop(self):
        if self.file is not None:
            self.file.close()

        print(f"Frame logging stopped: {self.file_path}")

        self.file = None
        self.writer = None
        self.is_logging = False

    def toggle(self, points):
        if self.is_logging:
            self.stop()
        else:
            self.start(points)

    def update(self, points, metrics, episode_manager, run_time, dt):
        if not self.is_logging:
            return

        self.time_since_last_log += dt

        if self.time_since_last_log < LOG_INTERVAL_SECONDS:
            return

        self.time_since_last_log = 0

        row = self._build_row(
            points,
            metrics,
            episode_manager,
            run_time,
        )

        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        if self.is_logging:
            self.stop()

    def _get_fieldnames(self, points):
        fieldnames = [
            "run_time",
            "episode_number",
            "episode_time",
            "time_alive",
            "episode_over",
            "is_fallen",
            "standing_score",
            "head_height",
            "pelvis_height",
            "torso_angle",
            "left_foot_contact",
            "right_foot_contact",
            "center_of_mass_x",
            "center_of_mass_y",
        ]

        for point in points:
            safe_name = point.name.lower().replace(" ", "_")
            fieldnames.append(f"{safe_name}_x")
            fieldnames.append(f"{safe_name}_y")
            fieldnames.append(f"{safe_name}_vx")
            fieldnames.append(f"{safe_name}_vy")

        return fieldnames

    def _build_row(self, points, metrics, episode_manager, run_time):
        center_of_mass = metrics["center_of_mass"]

        row = {
            "run_time": round(run_time, 3),
            "episode_number": episode_manager.episode_number,
            "episode_time": round(episode_manager.episode_time, 3),
            "time_alive": round(episode_manager.time_alive, 3),
            "episode_over": int(episode_manager.is_episode_over),
            "is_fallen": int(metrics["is_fallen"]),
            "standing_score": metrics["standing_score"],
            "head_height": round(metrics["head_height"], 2),
            "pelvis_height": round(metrics["pelvis_height"], 2),
            "torso_angle": round(metrics["torso_angle"], 2),
            "left_foot_contact": int(metrics["left_foot_contact"]),
            "right_foot_contact": int(metrics["right_foot_contact"]),
            "center_of_mass_x": round(center_of_mass.x, 2),
            "center_of_mass_y": round(center_of_mass.y, 2),
        }

        for point in points:
            safe_name = point.name.lower().replace(" ", "_")
            row[f"{safe_name}_x"] = round(point.position.x, 2)
            row[f"{safe_name}_y"] = round(point.position.y, 2)
            row[f"{safe_name}_vx"] = round(point.velocity.x, 2)
            row[f"{safe_name}_vy"] = round(point.velocity.y, 2)

        return row


class EpisodeSummaryLogger:
    def __init__(self):
        LOGS_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = LOGS_DIR / f"episode_summary_{timestamp}.csv"

        self.file = open(self.file_path, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=[
                "episode_number",
                "end_reason",
                "episode_time",
                "time_alive",
                "standing_score",
                "head_height",
                "pelvis_height",
                "torso_angle",
                "left_foot_contact",
                "right_foot_contact",
            ],
        )

        self.writer.writeheader()

        print(f"Episode summary file: {self.file_path}")

    def write_summary(self, summary):
        self.writer.writerow(summary)
        self.file.flush()

    def close(self):
        self.file.close()


def create_ragdoll():
    head = Point("Head", 250, 100, 5)
    chest = Point("Chest", 250, 150, 5)
    pelvis = Point("Pelvis", 250, 210, 5)

    left_elbow = Point("Left Elbow", 215, 165, 5)
    left_hand = Point("Left Hand", 190, 205, 5)

    right_elbow = Point("Right Elbow", 285, 165, 5)
    right_hand = Point("Right Hand", 310, 205, 5)

    left_knee = Point("Left Knee", 225, 280, 5)
    left_foot = Point("Left Foot", 210, 350, 5)

    right_knee = Point("Right Knee", 275, 280, 5)
    right_foot = Point("Right Foot", 290, 350, 5)

    points = [
        head,
        chest,
        pelvis,
        left_elbow,
        left_hand,
        right_elbow,
        right_hand,
        left_knee,
        left_foot,
        right_knee,
        right_foot,
    ]

    bones = [
        Bone(head, chest, 50),
        Bone(chest, pelvis, 60),

        Bone(chest, left_elbow, 45),
        Bone(left_elbow, left_hand, 45),

        Bone(chest, right_elbow, 45),
        Bone(right_elbow, right_hand, 45),

        Bone(pelvis, left_knee, 65),
        Bone(left_knee, left_foot, 70),

        Bone(pelvis, right_knee, 65),
        Bone(right_knee, right_foot, 70),
    ]

    return points, bones


def get_point_by_name(points, name):
    for point in points:
        if point.name == name:
            return point

    return None


def draw_world(screen):
    screen.fill(BACKGROUND_COLOR)

    pygame.draw.rect(
        screen,
        DARK_GREY,
        pygame.Rect(0, FLOOR_Y, SCREEN_WIDTH, SCREEN_HEIGHT - FLOOR_Y),
    )

    pygame.draw.line(
        screen,
        LINE_COLOR,
        (0, FLOOR_Y),
        (SCREEN_WIDTH, FLOOR_Y),
        2,
    )


def find_nearest_point_index(points, mouse_position):
    mouse_vector = pygame.Vector2(mouse_position)

    nearest_index = None
    nearest_distance = SELECT_RADIUS

    for index, point in enumerate(points):
        distance = point.position.distance_to(mouse_vector)

        if distance < nearest_distance:
            nearest_index = index
            nearest_distance = distance

    return nearest_index


def get_selected_index_from_key(event_key):
    key_to_index = {
        pygame.K_1: 0,
        pygame.K_2: 1,
        pygame.K_3: 2,
        pygame.K_4: 3,
        pygame.K_5: 4,
        pygame.K_6: 5,
        pygame.K_7: 6,
        pygame.K_8: 7,
        pygame.K_9: 8,
        pygame.K_0: 9,
        pygame.K_MINUS: 10,
    }

    return key_to_index.get(event_key)


def apply_mouse_pull(points, selected_index, is_mouse_dragging):
    if selected_index is None:
        return

    if not is_mouse_dragging:
        return

    selected_point = points[selected_index]

    mouse_position = pygame.Vector2(pygame.mouse.get_pos())
    direction = mouse_position - selected_point.position

    selected_point.apply_force(direction * PULL_FORCE)


def apply_keyboard_control(points, selected_index):
    if selected_index is None:
        return

    selected_point = points[selected_index]

    keys = pygame.key.get_pressed()
    force = pygame.Vector2(0, 0)

    if keys[pygame.K_LEFT]:
        force.x -= KEYBOARD_CONTROL_FORCE

    if keys[pygame.K_RIGHT]:
        force.x += KEYBOARD_CONTROL_FORCE

    if keys[pygame.K_UP]:
        force.y -= KEYBOARD_CONTROL_FORCE

    if keys[pygame.K_DOWN]:
        force.y += KEYBOARD_CONTROL_FORCE

    selected_point.apply_force(force)


def update_physics(
    points,
    bones,
    gravity_force,
    dt,
    selected_index,
    is_mouse_dragging,
):
    sub_dt = dt / SUBSTEPS

    for _ in range(SUBSTEPS):
        for point in points:
            point.reset_contact_state()

        for point in points:
            point.apply_force(gravity_force)

        apply_mouse_pull(points, selected_index, is_mouse_dragging)
        apply_keyboard_control(points, selected_index)

        for point in points:
            point.update(sub_dt)

        for _ in range(CONSTRAINT_ITERATIONS):
            for bone in bones:
                bone.solve()

            for point in points:
                point.solve_world_collision()


def calculate_center_of_mass(points):
    total_position = pygame.Vector2(0, 0)

    for point in points:
        total_position += point.position

    return total_position / len(points)


def calculate_standing_score(points):
    head = get_point_by_name(points, "Head")
    chest = get_point_by_name(points, "Chest")
    pelvis = get_point_by_name(points, "Pelvis")

    left_foot = get_point_by_name(points, "Left Foot")
    right_foot = get_point_by_name(points, "Right Foot")

    head_height = FLOOR_Y - head.position.y
    pelvis_height = FLOOR_Y - pelvis.position.y

    torso_vector = pelvis.position - chest.position

    if torso_vector.length() == 0:
        torso_angle = 0
    else:
        torso_angle = abs(torso_vector.angle_to(pygame.Vector2(0, 1)))

    foot_contact_count = 0

    if left_foot.is_touching_floor:
        foot_contact_count += 1

    if right_foot.is_touching_floor:
        foot_contact_count += 1

    score = 0

    if head_height > 120:
        score += 1

    if pelvis_height > 70:
        score += 1

    if torso_angle < 45:
        score += 1

    if foot_contact_count > 0:
        score += 1

    if head.position.y < chest.position.y:
        score += 1

    return score


def get_body_metrics(points):
    head = get_point_by_name(points, "Head")
    chest = get_point_by_name(points, "Chest")
    pelvis = get_point_by_name(points, "Pelvis")
    left_foot = get_point_by_name(points, "Left Foot")
    right_foot = get_point_by_name(points, "Right Foot")

    center_of_mass = calculate_center_of_mass(points)

    head_height = FLOOR_Y - head.position.y
    pelvis_height = FLOOR_Y - pelvis.position.y

    torso_vector = pelvis.position - chest.position

    if torso_vector.length() == 0:
        torso_angle = 0
    else:
        torso_angle = torso_vector.angle_to(pygame.Vector2(0, 1))

    left_foot_contact = left_foot.is_touching_floor
    right_foot_contact = right_foot.is_touching_floor

    standing_score = calculate_standing_score(points)

    is_fallen = False

    if head.position.y > chest.position.y:
        is_fallen = True

    if head_height < 60:
        is_fallen = True

    if pelvis_height < 35:
        is_fallen = True

    if abs(torso_angle) > 85:
        is_fallen = True

    return {
        "head_height": head_height,
        "pelvis_height": pelvis_height,
        "torso_angle": torso_angle,
        "left_foot_contact": left_foot_contact,
        "right_foot_contact": right_foot_contact,
        "center_of_mass": center_of_mass,
        "standing_score": standing_score,
        "is_fallen": is_fallen,
    }


def draw_pull_line(screen, points, selected_index, is_mouse_dragging):
    if selected_index is None:
        return

    if not is_mouse_dragging:
        return

    selected_point = points[selected_index]
    mouse_position = pygame.mouse.get_pos()

    pygame.draw.line(
        screen,
        PULL_LINE_COLOR,
        selected_point.position,
        mouse_position,
        2,
    )


def draw_center_of_mass(screen, center_of_mass):
    pygame.draw.circle(
        screen,
        CENTER_OF_MASS_COLOR,
        (int(center_of_mass.x), int(center_of_mass.y)),
        6,
    )

    pygame.draw.line(
        screen,
        CENTER_OF_MASS_COLOR,
        (int(center_of_mass.x), int(center_of_mass.y) - 10),
        (int(center_of_mass.x), int(center_of_mass.y) + 10),
        2,
    )

    pygame.draw.line(
        screen,
        CENTER_OF_MASS_COLOR,
        (int(center_of_mass.x) - 10, int(center_of_mass.y)),
        (int(center_of_mass.x) + 10, int(center_of_mass.y)),
        2,
    )


def draw_ragdoll(screen, points, bones, selected_index):
    for bone in bones:
        bone.draw(screen)

    for index, point in enumerate(points):
        is_selected = index == selected_index
        point.draw(screen, is_selected)


def draw_joint_labels(screen, font, points):
    for index, point in enumerate(points):
        label = f"{index}: {point.name}"

        text_surface = font.render(label, True, DEBUG_TEXT_COLOR)

        screen.blit(
            text_surface,
            (
                int(point.position.x) + 8,
                int(point.position.y) - 8,
            ),
        )


def draw_text(screen, font, text, x, y, color=TEXT_COLOR):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))


def draw_ui(
    screen,
    font,
    points,
    selected_index,
    is_showing_labels,
    current_fps,
    frame_logger,
    episode_manager,
):
    metrics = get_body_metrics(points)

    if selected_index is None:
        selected_text = "Selected: None"
    else:
        selected_point = points[selected_index]
        selected_text = f"Selected: {selected_index} - {selected_point.name}"

    if metrics["is_fallen"]:
        status_text = "Status: Fallen"
        status_color = FALLEN_TEXT_COLOR
    else:
        status_text = "Status: Standing"
        status_color = STANDING_TEXT_COLOR

    if frame_logger.is_logging:
        logging_text = f"Frame logging: ON -> {frame_logger.file_path.name}"
    else:
        logging_text = "Frame logging: OFF"

    left_contact = "YES" if metrics["left_foot_contact"] else "NO"
    right_contact = "YES" if metrics["right_foot_contact"] else "NO"

    center_of_mass = metrics["center_of_mass"]

    draw_text(screen, font, selected_text, 10, 10)
    draw_text(screen, font, status_text, 10, 30, status_color)

    draw_text(
        screen,
        font,
        f"Episode: {episode_manager.episode_number}",
        10,
        50,
        EPISODE_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Episode time: {episode_manager.episode_time:.2f}/{MAX_EPISODE_SECONDS}s",
        10,
        70,
        EPISODE_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Time alive: {episode_manager.time_alive:.2f}s",
        10,
        90,
        EPISODE_TEXT_COLOR,
    )

    draw_text(screen, font, logging_text, 10, 110, LOGGING_TEXT_COLOR)

    draw_text(
        screen,
        font,
        f"Last end reason: {episode_manager.last_end_reason}",
        10,
        130,
        DEBUG_TEXT_COLOR,
    )

    if episode_manager.is_episode_over:
        draw_text(
            screen,
            font,
            "Episode over. Resetting soon...",
            10,
            150,
            FALLEN_TEXT_COLOR,
        )

    draw_text(
        screen,
        font,
        f"Standing score: {metrics['standing_score']}/5",
        10,
        175,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Head height: {metrics['head_height']:.1f}",
        10,
        195,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Pelvis height: {metrics['pelvis_height']:.1f}",
        10,
        215,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Torso angle: {metrics['torso_angle']:.1f}",
        10,
        235,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Left foot contact: {left_contact}",
        10,
        255,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Right foot contact: {right_contact}",
        10,
        275,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Center mass: ({center_of_mass.x:.1f}, {center_of_mass.y:.1f})",
        10,
        295,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"FPS: {current_fps:.0f}",
        10,
        315,
        DEBUG_TEXT_COLOR,
    )

    draw_text(screen, font, "Mouse: click and drag point", 10, 380)
    draw_text(screen, font, "Keys 1-0, -: select point", 10, 400)
    draw_text(screen, font, "Arrows: apply force", 10, 420)
    draw_text(screen, font, "R: restart | N: next episode", 10, 440)
    draw_text(screen, font, "L: labels | S: frame logging", 10, 460)

    if is_showing_labels:
        draw_joint_labels(screen, font, points)


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Stage 16: Episode System")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 14)

    points, bones = create_ragdoll()

    selected_index = 0
    is_mouse_dragging = False
    is_showing_labels = True

    run_time = 0

    gravity_force = pygame.Vector2(0, GRAVITY_Y)

    frame_logger = FrameLogger()
    episode_summary_logger = EpisodeSummaryLogger()
    episode_manager = EpisodeManager()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        current_fps = clock.get_fps()

        run_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    nearest_index = find_nearest_point_index(points, event.pos)

                    if nearest_index is not None:
                        selected_index = nearest_index
                        is_mouse_dragging = True

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_mouse_dragging = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    points, bones = create_ragdoll()
                    selected_index = 0
                    is_mouse_dragging = False
                    episode_manager.restart_current_episode()

                if event.key == pygame.K_n:
                    points, bones = create_ragdoll()
                    selected_index = 0
                    is_mouse_dragging = False
                    episode_manager.start_next_episode()

                if event.key == pygame.K_l:
                    is_showing_labels = not is_showing_labels

                if event.key == pygame.K_s:
                    frame_logger.toggle(points)

                new_selected_index = get_selected_index_from_key(event.key)

                if new_selected_index is not None:
                    selected_index = new_selected_index

        update_physics(
            points,
            bones,
            gravity_force,
            dt,
            selected_index,
            is_mouse_dragging,
        )

        metrics = get_body_metrics(points)

        episode_summary = episode_manager.update(dt, metrics)

        if episode_summary is not None:
            episode_summary_logger.write_summary(episode_summary)

        frame_logger.update(
            points,
            metrics,
            episode_manager,
            run_time,
            dt,
        )

        if episode_manager.should_auto_reset():
            points, bones = create_ragdoll()
            selected_index = 0
            is_mouse_dragging = False
            episode_manager.start_next_episode()

        draw_world(screen)
        draw_pull_line(screen, points, selected_index, is_mouse_dragging)
        draw_ragdoll(screen, points, bones, selected_index)
        draw_center_of_mass(screen, metrics["center_of_mass"])

        draw_ui(
            screen,
            font,
            points,
            selected_index,
            is_showing_labels,
            current_fps,
            frame_logger,
            episode_manager,
        )

        pygame.display.update()

    frame_logger.close()
    episode_summary_logger.close()
    pygame.quit()


if __name__ == "__main__":
    main()