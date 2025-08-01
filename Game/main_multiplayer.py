import pygame
import sys
import socket
import logging
import json

from player import Player

# --- ClientInterface Class (Handles Server Communication) ---
class ClientInterface:
    def __init__(self, server_address=('127.0.0.1', 8889)):  # Changed from 55555 to 8889
        self.server_address = server_address

    def send_command(self, command_str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(self.server_address)
            logging.warning(f"Connecting to {self.server_address} to send: {command_str}")
            sock.sendall(command_str.encode())
            data_received = ""
            while True:
                data = sock.recv(1024)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            cleaned_data = data_received.split("\r\n\r\n", 1)[0]
            return json.loads(cleaned_data)
        except Exception as e:
            logging.error(f"Error during command execution: {e}")
            return None
        finally:
            sock.close()

    def get_all_player_ids(self):
        command = "get_players"
        result = self.send_command(command)
        if result and result.get('status') == 'OK':
            return result.get('players', [])
        return []

    def get_player_state(self, player_id):
        command = f"get_player_state {player_id}"
        return self.send_command(command)

    def set_player_state(self, player_id, state):
        # Ubah state dict menjadi string JSON yang aman untuk URL
        state_json_string = json.dumps(state)
        command = f"set_player_state {player_id} {state_json_string}"
        self.send_command(command)

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
    print("Knight Multiplayer Game - Client")
    print("=================================")
    
    # Test server connection first
    server_ip = input("Enter server IP [127.0.0.1]: ").strip() or "127.0.0.1"
    server_port = 8889
    
    print(f"Connecting to server {server_ip}:{server_port}...")
    client = ClientInterface((server_ip, server_port))
    
    # Test connection
    try:
        test_result = client.get_all_player_ids()
        print(f"✓ Server connected successfully! Current players: {test_result}")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("Make sure server is running with: python server_thread_http.py")
        input("Press Enter to continue anyway or Ctrl+C to exit...")
    
    player_id = input("Enter your player ID (e.g., 1, 2): ").strip()
    if not player_id:
        player_id = "player1"
        print(f"Using default ID: {player_id}")
    
    print(f"Starting game as player: {player_id}")
    print("Controls: Arrow keys = Move, X = Attack, Close window = Quit")
    print("=" * 50)

    # Create the local player
    try:
        local_player = Player(id=player_id, x=100, y=100, 
                              animation_folder=KNIGHT_ANIMATION_FOLDER, 
                              client_interface=client, is_remote=False)
        print(f"✓ Player {player_id} created successfully")
    except Exception as e:
        print(f"✗ Error creating player: {e}")
        print("Check if assets/images/knight/ folder exists and contains animation files")
        input("Press Enter to exit...")
        return

    # Dictionary to hold all players
    all_players = {player_id: local_player}

    # --- Game Loop ---
    print("Starting game loop...")
    running = True
    frame_count = 0
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Game quit requested")
                running = False

        # --- Update Remote Players ---
        try:
            # Dapatkan daftar semua ID pemain dari server
            all_ids_from_server = client.get_all_player_ids()
            
            # Tambahkan pemain baru yang belum ada di 'all_players'
            for p_id in all_ids_from_server:
                if p_id not in all_players:
                    print(f"New player {p_id} has joined.")
                    try:
                        all_players[p_id] = Player(id=p_id, x=200, y=200, 
                                                   animation_folder=KNIGHT_ANIMATION_FOLDER, 
                                                   client_interface=client, is_remote=True)
                    except Exception as e:
                        print(f"Error creating remote player {p_id}: {e}")
            
            # Hapus pemain yang keluar
            current_ids_in_game = list(all_players.keys())
            for p_id in current_ids_in_game:
                if p_id not in all_ids_from_server and p_id != player_id:
                    print(f"Player {p_id} has left.")
                    del all_players[p_id]
        except Exception as e:
            if frame_count % 300 == 0:  # Print error every 5 seconds
                print(f"Server communication error: {e}")

        # --- Update All Players ---
        try:
            for p in all_players.values():
                p.update(dt, walls, list(all_players.values()))
        except Exception as e:
            print(f"Player update error: {e}")

        # --- Drawing ---
        try:
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill(BLACK)

            # Draw walls (commented out for cleaner look)
            # for wall in walls:
            #     pygame.draw.rect(screen, BLUE, wall)

            for p in all_players.values():
                p.draw(screen)

            # Draw the local player's health bar
            if player_id in all_players:
                all_players[player_id].draw_health(screen)
            
            # Draw debug info
            if frame_count % 60 == 0:  # Every second
                debug_text = f"Players: {len(all_players)}, Frame: {frame_count}"
                print(debug_text)

            pygame.display.flip()
            
        except Exception as e:
            print(f"Drawing error: {e}")
            # Fill screen with red to indicate error
            screen.fill((255, 0, 0))
            pygame.display.flip()

    print("Cleaning up...")
    try:
        # Remove player from server
        client.send_command(f"remove_player {player_id}")
        print(f"Player {player_id} removed from server")
    except:
        pass
    
    pygame.quit()
    print("Game ended")
    sys.exit()

if __name__ == '__main__':
    main()
