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
            

def draw_world(screen):
    screen.fill(BACKGROUND_COLOR)

    pygame.draw.rect(screen, DARK_GREY, pygame.Rect(0, 0, 500, FLOOR_Y))

    pygame.draw.line(screen, LINE_COLOR, (0, FLOOR_Y), (500, FLOOR_Y), 2)

def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    points = [
        Point(230, 100, 5),
        Point(260, 100, 5),
        Point(245, 140, 5),
    ]

    gravity_force = pygame.Vector2(0, 0.001)
    running = True
    while running:
        all_events = pygame.event.get()
        for event in all_events:
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(FPS)
        draw_world(screen)
        
        for point in points:
            point.apply_force(gravity_force)
            point.update(dt)
            point.solve_floor_collision()
            point.draw(screen)
        
        pygame.display.update()


    pygame.quit()

main()
