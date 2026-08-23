import pygame
import time

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

FLOOR_Y = 450

FPS = 60

BACKGROUND_COLOR = (25, 30, 30)
GREEN = (0, 255, 0)
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
        

    def draw(self,screen):
        pygame.draw.circle(
            screen,
            (240, 220, 120),
            (self.position.x, self.position.y), self.radius
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

    pygame.draw.rect(screen, DARK_GREY, pygame.Rect(0, 0, 500, FLOOR_Y))

    pygame.draw.line(screen, LINE_COLOR, (0, FLOOR_Y), (500, FLOOR_Y), 2)

def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    

    p1 = Point(240, 100, 5)
    p2 = Point(260, 140, 5)
    points = [
        #Point(230, 100, 5),
        #Point(260, 100, 5),
        #Point(245, 140, 5),
        p1,
        p2,
    ]

    bone = Bone(p1, p2, 50)

    gravity_force = pygame.Vector2(0, 0.001)
    running = True
    while running:
        all_events = pygame.event.get()
        for event in all_events:
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(FPS)
        
        
        for point in points:
            point.apply_force(gravity_force)
            point.update(dt)
            point.solve_floor_collision()
            point.draw(screen)

        for _ in range(8):
            bone.solve()
        
        for point in points:
            point.solve_floor_collision()
        draw_world(screen)
        bone.draw(screen)
        for point in points:
            point.draw(screen)
        
        pygame.display.update()


    pygame.quit()

main()
