import pygame
import sys
from player import Player

# --- Dummy Client Interface for Offline Play ---
class DummyClientInterface:
    """A mock client interface that does nothing. 
    Allows the Player class to run without a real server connection."""
    def set_player_state(self, player_id, state):
        pass  # Do nothing

    def get_player_state(self, player_id):
        return None  # Do nothing

# --- Main Game Setup ---
def main():
    pygame.init()

    # Screen and Display
    WIDTH, HEIGHT = 600, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Knight Game - Single Player")
    clock = pygame.time.Clock()
    FPS = 60

    # Colors
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)

    # --- Assets ---
    try:
        background_image = pygame.image.load('assets/images/bg.png').convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
    except pygame.error as e:
        print(f"Error loading background image: {e}")
        background_image = None
    
    KNIGHT_ANIMATION_FOLDER = 'assets/images/knight'

    walls = []

    # 4 Corner Walls
    walls.append(pygame.Rect(0, 0, 10, HEIGHT))
    walls.append(pygame.Rect(WIDTH - 10, 0, 10, HEIGHT))
    walls.append(pygame.Rect(0, 0, WIDTH, 10))
    walls.append(pygame.Rect(0, HEIGHT - 10, WIDTH, 10))

    # Extra Walls
    scaling_factor = 2.307
    walls.append(pygame.Rect(130*scaling_factor, 0, 5*scaling_factor, 45*scaling_factor))
    walls.append(pygame.Rect(130*scaling_factor, 45*scaling_factor, 98*scaling_factor, 5*scaling_factor))
    walls.append(pygame.Rect(145*scaling_factor, 103*scaling_factor, 115*scaling_factor, 5*scaling_factor))
    walls.append(pygame.Rect(0, 210*scaling_factor, 160*scaling_factor, 5*scaling_factor))

    # --- Single Player Setup ---
    dummy_client = DummyClientInterface()
    player = Player(id='1', x=100, y=100, 
                    animation_folder=KNIGHT_ANIMATION_FOLDER, 
                    client_interface=dummy_client, 
                    is_remote=False)

    # --- Dummy Player for Testing ---
    dummy_player = Player(id='2', x=300, y=300, 
                          animation_folder=KNIGHT_ANIMATION_FOLDER, 
                          client_interface=dummy_client, 
                          is_remote=True) # is_remote is True so it doesn't take input

    all_players = [player, dummy_player]

    # --- Game Loop ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Update ---
        for p in all_players:
            # The main player's update needs the list of all players to check for hits
            p.update(dt, walls, all_players)

        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BLACK)

        # for wall in walls:
        #     pygame.draw.rect(screen, BLUE, wall)

        for p in all_players:
            p.draw(screen)
        
        # Draw the main player's health bar
        player.draw_health(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
