import pygame
import sys
import socket
import logging
import json

from player import Player

from clientInterface import ClientInterface

def select_player_id_by_keyboard(screen):
    import pygame
    font = pygame.font.SysFont("Arial", 48)
    prompt_text = "Press number to select Player ID"
    error_text = ""
    selected_id = None
    running = True

    while running:
        screen.fill((30, 30, 30))
        text_surface = font.render(prompt_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 50))
        screen.blit(text_surface, text_rect)
        
        if error_text:
            error_font = pygame.font.SysFont("Arial", 24)
            error_surface = error_font.render(error_text, True, (255, 0, 0))
            error_rect = error_surface.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
            screen.blit(error_surface, error_rect)
            
        instruction_font = pygame.font.SysFont("Arial", 20)
        instruction_surface = instruction_font.render("Keys: 1, 2, 3, 4", True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 50))
        screen.blit(instruction_surface, instruction_rect)
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_id = "1"
                    running = False
                elif event.key == pygame.K_2:
                    selected_id = "2"
                    running = False
                elif event.key == pygame.K_3:
                    selected_id = "3"
                    running = False
                elif event.key == pygame.K_4:
                    selected_id = "4"
                    running = False

    return selected_id

def show_id_taken_error(screen, taken_id):
    """Show error message when ID is already taken"""
    font = pygame.font.SysFont("Arial", 36)
    error_font = pygame.font.SysFont("Arial", 24)
    
    for i in range(60):  # Show for 1 second at 60 FPS
        screen.fill((30, 30, 30))
        
        error_text = font.render(f"Player ID {taken_id} is already taken!", True, (255, 0, 0))
        error_rect = error_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 30))
        screen.blit(error_text, error_rect)
        
        retry_text = error_font.render("Please choose another ID...", True, (255, 255, 255))
        retry_rect = retry_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 20))
        screen.blit(retry_text, retry_rect)
        
        pygame.display.flip()
        pygame.time.wait(16)  # ~60 FPS

# --- Main Game Setup ---
def main():
    pygame.init()

    # Screen and Display
    WIDTH, HEIGHT = 600, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Multiplayer Knight Game")
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

    # --- Multiplayer Setup ---
    client = ClientInterface()
    
    # Try to join with selected ID, loop until successful
    player_id = None
    while player_id is None:
        selected_id = select_player_id_by_keyboard(screen)
        
        # Try to join the game
        if client.join_game(selected_id):
            player_id = selected_id
            print(f"Successfully joined as Player {player_id}")
        else:
            print(f"Failed to join as Player {selected_id}. ID may already be in use.")
            # Show error message for taken ID
            show_id_taken_error(screen, selected_id)
            # Reset client for next attempt
            client = ClientInterface()

    # Create the local player
    local_player = Player(id=player_id, x=100, y=100, 
                          animation_folder=KNIGHT_ANIMATION_FOLDER, 
                          client_interface=client, is_remote=False)

    # Dictionary to hold all players
    all_players = {player_id: local_player}

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
                    all_players[player_id].respawn(x=100, y=100)
                    client.set_player_state(player_id, all_players[player_id].get_state_dict())
                    game_over = False
                    game_over_time = None

        # --- Update Remote Players ---
        # Dapatkan daftar semua ID pemain dari server
        all_ids_from_server = client.get_all_player_ids()
        # Tambahkan pemain baru yang belum ada di 'all_players'
        for p_id in all_ids_from_server:
            if p_id not in all_players:
                print(f"New player {p_id} has joined.")
                all_players[p_id] = Player(id=p_id, x=0, y=0, 
                                           animation_folder=KNIGHT_ANIMATION_FOLDER, 
                                           client_interface=client, is_remote=True)
        
        # Hapus pemain yang keluar
        current_ids_in_game = list(all_players.keys())
        for p_id in current_ids_in_game:
            if p_id not in all_ids_from_server and p_id != player_id:
                print(f"Player {p_id} has left.")
                del all_players[p_id]

        # --- Update All Players ---
        for p in all_players.values():
            p.update(dt, walls, all_players)

        if player_id in all_players:
            all_players[player_id].check_if_hit(all_players)
            if all_players[player_id].health <= 0 and not game_over:
                game_over = True
                game_over_time = pygame.time.get_ticks()


        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BLACK)

        # for wall in walls:
        #     pygame.draw.rect(screen, BLUE, wall)

        for p in all_players.values():
            p.draw(screen)
            p.draw_name(screen)

        if player_id in all_players:
            player = all_players[player_id]
            font = pygame.font.SysFont("Arial", 20, bold=True)
            label = font.render("You", True, (255, 255, 0))
            label_rect = label.get_rect(center=(player.rect.centerx, player.rect.top - 25))
            screen.blit(label, label_rect)

        # Draw enemy health bar only for other players
        for p in all_players.values():
            if p.id != player_id:  # Only draw health bars for other players
                p.draw_enemy_health_bar(screen)

        # Draw the local player's health bar
        if player_id in all_players:
            all_players[player_id].draw_health(screen)

        pygame.display.flip()

        
        if game_over:
            font = pygame.font.SysFont("Arial", 48)
            text = font.render("GAME OVER", True, (255, 0, 0))
            score_font = pygame.font.SysFont("Arial", 28)
            survival_time = (game_over_time - start_time) // 1000
            score_text = score_font.render(f"Score: {survival_time} Second", True, (255, 255, 255))
            respawn_text = score_font.render("Press R to respawn", True, (200, 200, 0))

            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 60))
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
            screen.blit(respawn_text, (WIDTH//2 - respawn_text.get_width()//2, HEIGHT//2 + 40))

            pygame.display.flip()
            continue

    client.leave_game()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
