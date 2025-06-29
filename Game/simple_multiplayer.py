import pygame
import sys
import json
import socket

# Simple multiplayer client tanpa dependencies berat
def simple_multiplayer_client():
    print("Simple Knight Multiplayer Client")
    print("=" * 35)
    
    # Test server connection
    server_ip = input("Server IP [127.0.0.1]: ").strip() or "127.0.0.1"
    server_port = 8889
    
    print(f"Testing connection to {server_ip}:{server_port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((server_ip, server_port))
        sock.sendall(b"get_players\r\n")
        response = sock.recv(1024)
        sock.close()
        print(f"✓ Server responded: {response.decode().strip()}")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("Start server first with: python server_thread_http.py")
        return
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Simple Knight Client")
    clock = pygame.time.Clock()
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    # Player state
    player_id = input("Player ID: ").strip() or "test_player"
    player_x = 300
    player_y = 300
    player_health = 6
    
    print(f"Starting as player: {player_id}")
    print("Controls: Arrow keys = Move, ESC = Quit")
    
    def send_command(command):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((server_ip, server_port))
            sock.sendall(f"{command}\r\n".encode())
            response = sock.recv(1024)
            sock.close()
            return response.decode().strip()
        except:
            return None
    
    def update_server():
        state = {
            "x": player_x,
            "y": player_y,
            "health": player_health,
            "facing_right": True,
            "is_attacking": False,
            "is_hit": False
        }
        command = f'set_player_state {player_id} {json.dumps(state)}'
        return send_command(command)
    
    def get_other_players():
        result = send_command("get_players")
        if result:
            try:
                data = json.loads(result)
                return data.get('players', [])
            except:
                pass
        return []
    
    running = True
    frame_count = 0
    
    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Handle input
        keys = pygame.key.get_pressed()
        speed = 200 * dt
        
        if keys[pygame.K_LEFT]:
            player_x -= speed
        if keys[pygame.K_RIGHT]:
            player_x += speed
        if keys[pygame.K_UP]:
            player_y -= speed
        if keys[pygame.K_DOWN]:
            player_y += speed
        
        # Keep in bounds
        player_x = max(25, min(575, player_x))
        player_y = max(25, min(575, player_y))
        
        # Update server every 10 frames
        if frame_count % 10 == 0:
            update_server()
        
        # Get other players every 30 frames
        other_players = []
        if frame_count % 30 == 0:
            other_players = get_other_players()
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw player (green circle)
        pygame.draw.circle(screen, GREEN, (int(player_x), int(player_y)), 20)
        
        # Draw other players (blue circles)
        for i, other_id in enumerate(other_players):
            if other_id != player_id:
                x = 100 + (i * 100) % 500
                y = 100
                pygame.draw.circle(screen, BLUE, (x, y), 15)
        
        # Draw UI
        # Health bar
        for i in range(player_health):
            pygame.draw.rect(screen, RED, (20 + i*25, 20, 20, 20))
        
        # Player count
        player_count_text = len(other_players)
        for i in range(min(player_count_text, 10)):
            pygame.draw.rect(screen, WHITE, (20 + i*10, 50, 8, 8))
        
        pygame.display.flip()
    
    # Cleanup
    send_command(f"remove_player {player_id}")
    pygame.quit()
    print(f"Player {player_id} disconnected")

if __name__ == "__main__":
    simple_multiplayer_client()
