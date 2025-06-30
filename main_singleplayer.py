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
    
    # Select difficulty
    difficulty = select_difficulty(screen)

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
                    is_remote=False, is_ai=False)

    # --- AI Enemy ---
    ai_enemy = Player(id='2', x=400, y=400, 
                      animation_folder=KNIGHT_ANIMATION_FOLDER, 
                      client_interface=dummy_client, 
                      is_remote=False, is_ai=True)
    ai_enemy.display_name = "AI Enemy"
    ai_enemy.set_ai_difficulty(difficulty)  # Set the selected difficulty

    all_players = [player, ai_enemy]

    # Game Over Variables
    start_time = pygame.time.get_ticks()
    game_over = False
    game_over_time = None
    player_score = 0
    ai_score = 0

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
                    ai_enemy.respawn(x=400, y=400)
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
            ai_score += 1
            game_over = True
            game_over_time = pygame.time.get_ticks()
            
        # Check if AI is dead
        if ai_enemy.health <= 0 and not game_over:
            player_score += 1
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
            if p.is_ai:
                draw_ai_status(screen, p)
            p.draw_enemy_health_bar(screen)  # This will only draw for remote players
        
        # Draw the main player's health bar
        player.draw_health(screen)

        # Draw the score
        draw_score(screen, player_score, ai_score)

        # Draw controls info
        draw_controls_info(screen)
        
        # Draw score
        draw_score(screen, player_score, ai_score)

        # Game Over Screen
        if game_over:
            font = pygame.font.SysFont("Arial", 48)
            score_font = pygame.font.SysFont("Arial", 28)
            
            # Determine winner
            if player.health <= 0:
                text = font.render("AI WINS!", True, (255, 100, 100))
                winner_text = score_font.render("You were defeated!", True, (255, 150, 150))
            else:
                text = font.render("YOU WIN!", True, (100, 255, 100))
                winner_text = score_font.render("AI defeated!", True, (150, 255, 150))
            
            survival_time = (game_over_time - start_time) // 1000
            time_text = score_font.render(f"Battle Time: {survival_time} seconds", True, (255, 255, 255))
            score_text = score_font.render(f"Score - Player: {player_score} | AI: {ai_score}", True, (255, 255, 255))
            respawn_text = score_font.render("Press R to restart battle", True, (200, 200, 0))
            menu_text = score_font.render("Press ESC for main menu", True, (150, 150, 255))

            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 100))
            screen.blit(winner_text, (WIDTH//2 - winner_text.get_width()//2, HEIGHT//2 - 60))
            screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2 - 20))
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 + 10))
            screen.blit(respawn_text, (WIDTH//2 - respawn_text.get_width()//2, HEIGHT//2 + 50))
            screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 90))

        draw_controls_info(screen)  # Draw controls information
        draw_ai_status(screen, ai_enemy)  # Draw AI status

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

def draw_ai_status(screen, ai_player):
    """Draw AI status information"""
    if not ai_player.is_ai:
        return
        
    font = pygame.font.SysFont("Arial", 14)
    status_text = f"AI: {ai_player.ai_state.upper()}"
    
    # Choose color based on AI state
    color_map = {
        "idle": (200, 200, 200),
        "chase": (255, 255, 0),
        "attack": (255, 0, 0),
        "flee": (0, 255, 255)
    }
    color = color_map.get(ai_player.ai_state, (255, 255, 255))
    
    status_surface = font.render(status_text, True, color)
    status_rect = status_surface.get_rect(center=(ai_player.rect.centerx, ai_player.rect.top - 25))
    screen.blit(status_surface, status_rect)

def select_difficulty(screen):
    """Select AI difficulty level"""
    font_title = pygame.font.SysFont("Arial", 48, bold=True)
    font_option = pygame.font.SysFont("Arial", 36, bold=True)
    font_instruction = pygame.font.SysFont("Arial", 20)
    
    selected_option = 1  # Default to normal (0=easy, 1=normal, 2=hard)
    options = ["EASY", "NORMAL", "HARD"]
    descriptions = [
        "AI is slower and less aggressive",
        "Balanced AI behavior", 
        "AI is faster and more aggressive"
    ]
    
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "normal"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected_option].lower()
                elif event.key == pygame.K_ESCAPE:
                    return "normal"
        
        # Draw menu
        screen.fill((20, 20, 40))
        
        # Title
        title_text = font_title.render("SELECT DIFFICULTY", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(screen.get_width()//2, 120))
        screen.blit(title_text, title_rect)
        
        # Menu options
        for i, option in enumerate(options):
            if i == selected_option:
                color = (255, 255, 0)  # Yellow for selected
                option_text = font_option.render(f"> {option} <", True, color)
            else:
                color = (255, 255, 255)  # White for unselected
                option_text = font_option.render(option, True, color)
            
            option_rect = option_text.get_rect(center=(screen.get_width()//2, 220 + i * 60))
            screen.blit(option_text, option_rect)
            
            # Description
            if i == selected_option:
                desc_font = pygame.font.SysFont("Arial", 18)
                desc_text = desc_font.render(descriptions[i], True, (200, 200, 200))
                desc_rect = desc_text.get_rect(center=(screen.get_width()//2, 250 + i * 60))
                screen.blit(desc_text, desc_rect)
        
        # Instructions
        instruction_texts = [
            "Use UP/DOWN arrows to select difficulty",
            "Press ENTER to confirm",
            "Press ESC for default (Normal)"
        ]
        
        for i, instruction in enumerate(instruction_texts):
            instruction_surface = font_instruction.render(instruction, True, (200, 200, 200))
            instruction_rect = instruction_surface.get_rect(center=(screen.get_width()//2, 450 + i * 25))
            screen.blit(instruction_surface, instruction_rect)
        
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    
    return "normal"

def draw_score(screen, player_score, ai_score):
    """Draw the current score"""
    font = pygame.font.SysFont("Arial", 24, bold=True)
    score_text = f"Player: {player_score}  |  AI: {ai_score}"
    score_surface = font.render(score_text, True, (255, 255, 255))
    score_rect = score_surface.get_rect(center=(screen.get_width()//2, 30))
    screen.blit(score_surface, score_rect)

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
