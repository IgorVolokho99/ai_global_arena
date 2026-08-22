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

        self.radius = 5

    def apply_force(self, force):
        self.acceleration += force

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt
        self.acceleration *= 0 
        

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
    # SOME CODE FROM DEVELOPER(IGOR)
    #ok
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    p = Point(100, 100, 8)

    gravity_force = pygame.Vector2(0, 0.001)
    running = True
    while running:
        all_events = pygame.event.get()
        for event in all_events:
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(FPS)
        
        p.update(dt)
        p.apply_force(gravity_force)
        draw_world(screen)
        p.draw(screen)
        
        pygame.display.update()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            p.apply_force(pygame.Vector2(0, 0))
        if keys[pygame.K_RIGHT]:
            p.apply_force(pygame.Vector2(0, 0))
        if keys[pygame.K_UP]:
            p.apply_force(pygame.Vector2(0, 0))


    pygame.quit()

main()
