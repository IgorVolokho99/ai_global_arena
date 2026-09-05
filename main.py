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
        pygame.K_1: 0,       # Head
        pygame.K_2: 1,       # Chest
        pygame.K_3: 2,       # Pelvis
        pygame.K_4: 3,       # Left Elbow
        pygame.K_5: 4,       # Left Hand
        pygame.K_6: 5,       # Right Elbow
        pygame.K_7: 6,       # Right Hand
        pygame.K_8: 7,       # Left Knee
        pygame.K_9: 8,       # Left Foot
        pygame.K_0: 9,       # Right Knee
        pygame.K_MINUS: 10,  # Right Foot
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
    time_alive,
    current_fps,
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

    left_contact = "YES" if metrics["left_foot_contact"] else "NO"
    right_contact = "YES" if metrics["right_foot_contact"] else "NO"

    center_of_mass = metrics["center_of_mass"]

    draw_text(screen, font, selected_text, 10, 10)
    draw_text(screen, font, status_text, 10, 30, status_color)

    draw_text(
        screen,
        font,
        f"Time alive: {time_alive:.2f}s",
        10,
        50,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Head height: {metrics['head_height']:.1f}",
        10,
        70,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Pelvis height: {metrics['pelvis_height']:.1f}",
        10,
        90,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Torso angle: {metrics['torso_angle']:.1f}",
        10,
        110,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Standing score: {metrics['standing_score']}/5",
        10,
        130,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Left foot contact: {left_contact}",
        10,
        150,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Right foot contact: {right_contact}",
        10,
        170,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"Center mass: ({center_of_mass.x:.1f}, {center_of_mass.y:.1f})",
        10,
        190,
        DEBUG_TEXT_COLOR,
    )

    draw_text(
        screen,
        font,
        f"FPS: {current_fps:.0f}",
        10,
        210,
        DEBUG_TEXT_COLOR,
    )

    if selected_index is not None:
        selected_point = points[selected_index]

        draw_text(
            screen,
            font,
            f"Position: ({selected_point.position.x:.1f}, {selected_point.position.y:.1f})",
            10,
            230,
            DEBUG_TEXT_COLOR,
        )

        draw_text(
            screen,
            font,
            f"Velocity: ({selected_point.velocity.x:.1f}, {selected_point.velocity.y:.1f})",
            10,
            250,
            DEBUG_TEXT_COLOR,
        )

    draw_text(screen, font, "Mouse: click and drag point", 10, 400)
    draw_text(screen, font, "Keys 1-0, -: select point", 10, 420)
    draw_text(screen, font, "Arrows: apply force", 10, 440)
    draw_text(screen, font, "R: reset | L: labels on/off", 10, 460)

    if is_showing_labels:
        draw_joint_labels(screen, font, points)


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Stage 14: Foot Contact and Better Metrics")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 14)

    points, bones = create_ragdoll()

    selected_index = 0
    is_mouse_dragging = False
    is_showing_labels = True

    time_alive = 0

    gravity_force = pygame.Vector2(0, GRAVITY_Y)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        current_fps = clock.get_fps()

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
                    time_alive = 0

                if event.key == pygame.K_l:
                    is_showing_labels = not is_showing_labels

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

        if not metrics["is_fallen"]:
            time_alive += dt

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
            time_alive,
            current_fps,
        )

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()