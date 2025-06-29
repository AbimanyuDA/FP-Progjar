import pygame
from player import Player

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game Animasi Ksatria")

BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

try:
    background_image = pygame.image.load('assets/images/bg.png').convert()
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
except pygame.error as e:
    print(f"Error loading background image: {e}")
    background_image = None

# --- Inisialisasi Pemain ---
KNIGHT_ANIMATION_FOLDER = 'assets/images/knight'

player = Player(100, 100, KNIGHT_ANIMATION_FOLDER)

# --- Inisialisasi Dinding ---
walls = []

# 4 Corner Walls
walls.append(pygame.Rect(0, 0, 10, SCREEN_HEIGHT))
walls.append(pygame.Rect(SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT))
walls.append(pygame.Rect(0, 0, SCREEN_WIDTH, 10))
walls.append(pygame.Rect(0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10))

# Extra Walls
scaling_factor = 2.307
walls.append(pygame.Rect(130*scaling_factor, 0, 5*scaling_factor, 45*scaling_factor))
walls.append(pygame.Rect(130*scaling_factor, 45*scaling_factor, 98*scaling_factor, 5*scaling_factor))
walls.append(pygame.Rect(145*scaling_factor, 103*scaling_factor, 115*scaling_factor, 5*scaling_factor))
walls.append(pygame.Rect(0, 210*scaling_factor, 160*scaling_factor, 5*scaling_factor))

clock = pygame.time.Clock()
FPS = 60

running = True
while running:
    dt = clock.tick(FPS) / 1000.0 # Delta time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update(dt, walls)

    if background_image:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(BLACK)

    # Gambar dinding
    # for wall in walls:
    #     pygame.draw.rect(screen, BLUE, wall)

    # Gambar pemain
    player.draw(screen)

    pygame.display.flip()

pygame.quit()