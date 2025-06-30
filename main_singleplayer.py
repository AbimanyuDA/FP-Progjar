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

    # Game Over Variables
    start_time = pygame.time.get_ticks()
    game_over = False
    game_over_time = None

    # --- Game Loop ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # Respawn player
                    player.respawn(x=100, y=100)
                    dummy_player.respawn(x=300, y=300)
                    game_over = False
                    game_over_time = None
                    start_time = pygame.time.get_ticks()

        # --- Update ---
        for p in all_players:
            # The main player's update needs the list of all players to check for hits
            p.update(dt, walls, all_players)

        # Check if player is dead
        if player.health <= 0 and not game_over:
            game_over = True
            game_over_time = pygame.time.get_ticks()

        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BLACK)

        # for wall in walls:
        #     pygame.draw.rect(screen, BLUE, wall)

        for p in all_players:
            p.draw(screen)
            p.draw_name(screen)
            p.draw_enemy_health_bar(screen)  # This will only draw for remote players
        
        # Draw the main player's health bar
        player.draw_health(screen)

        # Game Over Screen
        if game_over:
            font = pygame.font.SysFont("Arial", 48)
            text = font.render("GAME OVER", True, (255, 0, 0))
            score_font = pygame.font.SysFont("Arial", 28)
            survival_time = (game_over_time - start_time) // 1000
            score_text = score_font.render(f"Score: {survival_time} Seconds", True, (255, 255, 255))
            respawn_text = score_font.render("Press R to restart", True, (200, 200, 0))

            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 60))
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
            screen.blit(respawn_text, (WIDTH//2 - respawn_text.get_width()//2, HEIGHT//2 + 40))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
