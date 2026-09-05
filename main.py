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

BACKGROUND_COLOR = (25, 30, 30)
DARK_GREY = (60, 60, 70)
LINE_COLOR = (200, 200, 200)

POINT_COLOR = (240, 220, 120)
SELECTED_POINT_COLOR = (255, 100, 100)
BONE_COLOR = (220, 220, 230)
PULL_LINE_COLOR = (255, 120, 120)
TEXT_COLOR = (230, 230, 230)


class Point:
    def __init__(self, x, y, radius):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)

        self.radius = radius

    def apply_force(self, force):
        self.acceleration += force

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.velocity *= DAMPING

        self.position += self.velocity * dt

        self.acceleration *= 0

    def solve_world_collision(self):
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
        color = SELECTED_POINT_COLOR if is_selected else POINT_COLOR

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
    head = Point(250, 100, 5)
    chest = Point(250, 150, 5)
    pelvis = Point(250, 210, 5)

    left_elbow = Point(215, 165, 5)
    left_hand = Point(190, 205, 5)

    right_elbow = Point(285, 165, 5)
    right_hand = Point(310, 205, 5)

    left_knee = Point(225, 280, 5)
    left_foot = Point(210, 350, 5)

    right_knee = Point(275, 280, 5)
    right_foot = Point(290, 350, 5)

    point_labels = [
        "Head",
        "Chest",
        "Pelvis",
        "Left Elbow",
        "Left Hand",
        "Right Elbow",
        "Right Hand",
        "Left Knee",
        "Left Foot",
        "Right Knee",
        "Right Foot",
    ]

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

    return points, bones, point_labels


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
        pygame.K_1: 0,      # Head
        pygame.K_2: 1,      # Chest
        pygame.K_3: 2,      # Pelvis
        pygame.K_4: 3,      # Left Elbow
        pygame.K_5: 4,      # Left Hand
        pygame.K_6: 5,      # Right Elbow
        pygame.K_7: 6,      # Right Hand
        pygame.K_8: 7,      # Left Knee
        pygame.K_9: 8,      # Left Foot
        pygame.K_0: 9,      # Right Knee
        pygame.K_MINUS: 10, # Right Foot
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


def draw_ragdoll(screen, points, bones, selected_index):
    for bone in bones:
        bone.draw(screen)

    for index, point in enumerate(points):
        is_selected = index == selected_index
        point.draw(screen, is_selected)


def draw_text(screen, font, text, x, y):
    text_surface = font.render(text, True, TEXT_COLOR)
    screen.blit(text_surface, (x, y))


def draw_ui(screen, font, selected_index, point_labels):
    if selected_index is None:
        selected_text = "Selected: None"
    else:
        selected_text = f"Selected: {point_labels[selected_index]}"

    draw_text(screen, font, selected_text, 10, 10)
    draw_text(screen, font, "Mouse: click and drag a point", 10, 30)
    draw_text(screen, font, "Keys 1-0, -: select point", 10, 50)
    draw_text(screen, font, "Arrows: apply force to selected point", 10, 70)
    draw_text(screen, font, "R: reset", 10, 90)


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Stage 12: Keyboard Control")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 16)

    points, bones, point_labels = create_ragdoll()

    selected_index = 0
    is_mouse_dragging = False

    gravity_force = pygame.Vector2(0, GRAVITY_Y)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

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
                    points, bones, point_labels = create_ragdoll()
                    selected_index = 0
                    is_mouse_dragging = False

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

        draw_world(screen)
        draw_pull_line(screen, points, selected_index, is_mouse_dragging)
        draw_ragdoll(screen, points, bones, selected_index)
        draw_ui(screen, font, selected_index, point_labels)

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()