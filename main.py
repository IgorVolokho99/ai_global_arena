import pygame

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

FLOOR_Y = 450

FPS = 60

BACKGROUND_COLOR = (25, 30, 30)
DARK_GREY = (60, 60, 70)
LINE_COLOR = (200, 200, 200)


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
        self.position += self.velocity * dt
        self.acceleration *= 0

    def solve_floor_collision(self):
        if self.position.y + self.radius > FLOOR_Y:
            self.position.y = FLOOR_Y - self.radius
            self.velocity.y *= -0.8
            self.velocity.x *= 0.9

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            (240, 220, 120),
            (int(self.position.x), int(self.position.y)),
            self.radius,
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
            (220, 220, 230),
            self.point_a.position,
            self.point_b.position,
            4,
        )


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


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Stage 9: Simple Skeleton")

    clock = pygame.time.Clock()

    head = Point(240, 100, 5)
    chest = Point(250, 150, 5)
    pelvis = Point(250, 210, 5)

    points = [
        head,
        chest,
        pelvis,
    ]

    bones = [
        Bone(head, chest, 50),
        Bone(chest, pelvis, 60),
    ]

    gravity_force = pygame.Vector2(0, 900)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        for point in points:
            point.apply_force(gravity_force)
            point.update(dt)

        for _ in range(8):
            for bone in bones:
                bone.solve()

        for point in points:
            point.solve_floor_collision()

        draw_world(screen)

        for bone in bones:
            bone.draw(screen)

        for point in points:
            point.draw(screen)

        pygame.display.update()

    pygame.quit()


main()
