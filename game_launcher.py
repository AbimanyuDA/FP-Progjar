import pygame
import sys
import subprocess

def show_game_mode_menu():
    """Show menu to select game mode"""
    pygame.init()
    
    # Screen setup
    WIDTH, HEIGHT = 600, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Knight Game - Select Mode")
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 64, bold=True)
    font_option = pygame.font.SysFont("Arial", 36, bold=True)
    font_instruction = pygame.font.SysFont("Arial", 20)
    
    selected_option = 0  # 0 = Single Player, 1 = Multiplayer, 2 = Exit
    options = ["SINGLE PLAYER", "MULTIPLAYER", "EXIT"]
    
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
                        return "single"
                    elif selected_option == 1:
                        return "multiplayer"
                    else:
                        return "exit"
                elif event.key == pygame.K_ESCAPE:
                    return "exit"
        
        # Draw menu
        screen.fill((15, 15, 30))  # Dark background
        
        # Title
        title_text = font_title.render("KNIGHT GAME", True, (255, 215, 0))  # Gold color
        title_rect = title_text.get_rect(center=(WIDTH//2, 120))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_font = pygame.font.SysFont("Arial", 24, bold=True)
        subtitle_text = subtitle_font.render("Select Game Mode", True, (150, 150, 200))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, 170))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Menu options
        for i, option in enumerate(options):
            if i == selected_option:
                color = (255, 255, 0)  # Yellow for selected
                option_text = font_option.render(f"> {option} <", True, color)
            else:
                color = (255, 255, 255)  # White for unselected
                option_text = font_option.render(option, True, color)
            
            option_rect = option_text.get_rect(center=(WIDTH//2, 260 + i * 60))
            screen.blit(option_text, option_rect)
        
        # Instructions
        instruction_texts = [
            "Use UP/DOWN arrows to navigate",
            "Press ENTER to select",
            "Press ESC to exit"
        ]
        
        for i, instruction in enumerate(instruction_texts):
            instruction_surface = font_instruction.render(instruction, True, (200, 200, 200))
            instruction_rect = instruction_surface.get_rect(center=(WIDTH//2, 460 + i * 25))
            screen.blit(instruction_surface, instruction_rect)
        
        # Game info
        info_font = pygame.font.SysFont("Arial", 16)
        info_texts = [
            "Single Player: Play against AI",
            "Multiplayer: Play with others online"
        ]
        
        for i, info in enumerate(info_texts):
            info_surface = info_font.render(info, True, (150, 150, 150))
            info_rect = info_surface.get_rect(center=(WIDTH//2, 540 + i * 20))
            screen.blit(info_surface, info_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return "exit"

def main():
    while True:
        choice = show_game_mode_menu()
        
        if choice == "exit":
            pygame.quit()
            sys.exit()
        elif choice == "single":
            pygame.quit()
            try:
                subprocess.run([sys.executable, "main_singleplayer.py"], check=True)
            except subprocess.CalledProcessError:
                print("Error running single player mode")
            except FileNotFoundError:
                print("main_singleplayer.py not found")
            pygame.init()  # Reinitialize pygame for next iteration
        elif choice == "multiplayer":
            pygame.quit()
            try:
                subprocess.run([sys.executable, "main_multiplayer.py"], check=True)
            except subprocess.CalledProcessError:
                print("Error running multiplayer mode")
            except FileNotFoundError:
                print("main_multiplayer.py not found")
            pygame.init()  # Reinitialize pygame for next iteration

if __name__ == '__main__':
    main()
