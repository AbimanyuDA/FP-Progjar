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

    # Show main menu first
    menu_choice = show_main_menu(screen)
    if menu_choice == "exit":
        pygame.quit()
        sys.exit()

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
                elif event.key == pygame.K_ESCAPE:
                    # Return to main menu
                    menu_choice = show_main_menu(screen)
                    if menu_choice == "exit":
                        running = False

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
        
        # Draw controls info
        draw_controls_info(screen)

        # Game Over Screen
        if game_over:
            font = pygame.font.SysFont("Arial", 48)
            text = font.render("GAME OVER", True, (255, 0, 0))
            score_font = pygame.font.SysFont("Arial", 28)
            survival_time = (game_over_time - start_time) // 1000
            score_text = score_font.render(f"Score: {survival_time} Seconds", True, (255, 255, 255))
            respawn_text = score_font.render("Press R to restart", True, (200, 200, 0))
            menu_text = score_font.render("Press ESC for main menu", True, (150, 150, 255))

            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 80))
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 20))
            screen.blit(respawn_text, (WIDTH//2 - respawn_text.get_width()//2, HEIGHT//2 + 20))
            screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 60))

        draw_controls_info(screen)  # Draw controls information

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def show_main_menu(screen):
    """Show main menu with Play and Exit options"""
    font_title = pygame.font.SysFont("Arial", 64, bold=True)
    font_option = pygame.font.SysFont("Arial", 36, bold=True)
    font_instruction = pygame.font.SysFont("Arial", 20)
    
    selected_option = 0  # 0 = Play, 1 = Exit
    options = ["PLAY", "EXIT"]
    
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        return "play"
                    else:
                        return "exit"
                elif event.key == pygame.K_ESCAPE:
                    return "exit"
        
        # Draw menu
        screen.fill((20, 20, 40))  # Dark blue background
        
        # Title
        title_text = font_title.render("KNIGHT GAME", True, (255, 215, 0))  # Gold color
        title_rect = title_text.get_rect(center=(screen.get_width()//2, 150))
        screen.blit(title_text, title_rect)
        
        # Menu options
        for i, option in enumerate(options):
            if i == selected_option:
                color = (255, 255, 0)  # Yellow for selected
                option_text = font_option.render(f"> {option} <", True, color)
            else:
                color = (255, 255, 255)  # White for unselected
                option_text = font_option.render(option, True, color)
            
            option_rect = option_text.get_rect(center=(screen.get_width()//2, 300 + i * 60))
            screen.blit(option_text, option_rect)
        
        # Instructions
        instruction_texts = [
            "Use UP/DOWN arrows to navigate",
            "Press ENTER to select",
            "Press ESC to exit"
        ]
        
        for i, instruction in enumerate(instruction_texts):
            instruction_surface = font_instruction.render(instruction, True, (200, 200, 200))
            instruction_rect = instruction_surface.get_rect(center=(screen.get_width()//2, 480 + i * 25))
            screen.blit(instruction_surface, instruction_rect)
        
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    
    return "exit"

def draw_controls_info(screen):
    """Draw controls information on screen"""
    font = pygame.font.SysFont("Arial", 16)
    controls = [
        "Controls:",
        "Arrow Keys - Move",
        "X - Attack",
        "R - Restart (when dead)",
        "ESC - Main Menu"
    ]
    
    for i, control in enumerate(controls):
        color = (255, 255, 255) if i == 0 else (200, 200, 200)
        if i == 0:
            font_bold = pygame.font.SysFont("Arial", 16, bold=True)
            text_surface = font_bold.render(control, True, color)
        else:
            text_surface = font.render(control, True, color)
        screen.blit(text_surface, (10, 10 + i * 20))

if __name__ == '__main__':
    # Initialize Pygame
    pygame.init()

    # Screen dimensions
    WIDTH, HEIGHT = 600, 600

    # Create the window
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Knight Game - Single Player")

    # Show the main menu
    menu_result = show_main_menu(screen)

    if menu_result == "play":
        main()
    else:
        pygame.quit()
        sys.exit()
