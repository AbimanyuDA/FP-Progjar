import pygame
import sys
import os

def test_game_assets():
    """Test apakah semua assets game tersedia"""
    print("Testing game assets...")
    print("=" * 30)
    
    # Test pygame initialization
    try:
        pygame.init()
        print("✓ Pygame initialized")
    except Exception as e:
        print(f"✗ Pygame init failed: {e}")
        return False
    
    # Test screen creation
    try:
        screen = pygame.display.set_mode((600, 600))
        pygame.display.set_caption("Asset Test")
        print("✓ Screen created")
    except Exception as e:
        print(f"✗ Screen creation failed: {e}")
        return False
    
    # Test background image
    try:
        bg_path = 'assets/images/bg.png'
        if os.path.exists(bg_path):
            background = pygame.image.load(bg_path).convert()
            print(f"✓ Background image loaded: {bg_path}")
        else:
            print(f"✗ Background image not found: {bg_path}")
    except Exception as e:
        print(f"✗ Background loading error: {e}")
    
    # Test knight animation folder
    knight_folder = 'assets/images/knight'
    if os.path.exists(knight_folder):
        files = os.listdir(knight_folder)
        run_files = [f for f in files if 'run_anim' in f and f.endswith('.png')]
        print(f"✓ Knight folder exists: {len(files)} files total")
        print(f"✓ Animation files found: {len(run_files)} run animation frames")
        if len(run_files) > 0:
            print(f"  Sample files: {run_files[:3]}")
        else:
            print("✗ No run animation files found!")
    else:
        print(f"✗ Knight folder not found: {knight_folder}")
    
    # Test heart images
    heart_folder = 'assets/images/heart'
    if os.path.exists(heart_folder):
        heart_files = os.listdir(heart_folder)
        print(f"✓ Heart folder exists: {heart_files}")
    else:
        print(f"✗ Heart folder not found: {heart_folder}")
    
    # Test sword image
    sword_path = 'assets/images/sword.png'
    if os.path.exists(sword_path):
        print(f"✓ Sword image found: {sword_path}")
    else:
        print(f"✗ Sword image not found: {sword_path}")
    
    return True

def test_simple_game():
    """Test simple pygame window"""
    print("\nTesting simple game window...")
    print("=" * 30)
    
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Simple Test - Press ESC to exit")
    clock = pygame.time.Clock()
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    print("Window created. Press ESC to close, or close window.")
    
    running = True
    frame = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw test pattern
        frame += 1
        color_cycle = [RED, GREEN, BLUE, WHITE]
        color = color_cycle[(frame // 60) % len(color_cycle)]
        
        # Draw moving rectangle
        x = (frame * 2) % 600
        y = 300
        pygame.draw.rect(screen, color, (x, y, 50, 50))
        
        # Draw text equivalent (using rectangles)
        # "WORKING" indicator
        for i, char_color in enumerate([RED, GREEN, BLUE, WHITE, RED, GREEN, BLUE]):
            pygame.draw.rect(screen, char_color, (50 + i*20, 50, 15, 20))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("Simple test completed successfully!")

def test_knight_player():
    """Test knight player creation"""
    print("\nTesting Knight Player creation...")
    print("=" * 35)
    
    try:
        # Add current directory to path to import player
        sys.path.append('.')
        from player import Player
        
        # Dummy client interface
        class DummyClient:
            def set_player_state(self, player_id, state): pass
            def get_player_state(self, player_id): return None
        
        dummy_client = DummyClient()
        
        # Try to create player
        player = Player(
            id='test', 
            x=100, 
            y=100,
            animation_folder='assets/images/knight',
            client_interface=dummy_client,
            is_remote=False
        )
        
        print("✓ Player created successfully!")
        print(f"  Animation frames loaded: {len(player.animation_frames)}")
        print(f"  Player rect: {player.rect}")
        print(f"  Player health: {player.health}/{player.max_health}")
        
        return True
        
    except Exception as e:
        print(f"✗ Player creation failed: {e}")
        print("This might be why the game shows black screen!")
        return False

def main():
    print("Knight Game Diagnostic Tool")
    print("=" * 40)
    print("This will help diagnose why the game shows black screen")
    print()
    
    # Change to game directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run tests
    print("1. Testing game assets...")
    assets_ok = test_game_assets()
    
    if not assets_ok:
        print("\n❌ Asset test failed! Game will not work.")
        return
    
    print("\n2. Testing Knight player...")
    player_ok = test_knight_player()
    
    if not player_ok:
        print("\n❌ Player creation failed! This is likely the cause of black screen.")
        return
    
    print("\n3. All tests passed! Testing simple pygame window...")
    response = input("Show test window? (y/N): ").strip().lower()
    if response == 'y':
        test_simple_game()
    
    print("\n✅ All diagnostic tests completed!")
    print("\nIf tests passed but game still shows black screen:")
    print("1. Make sure server is running: python server_thread_http.py")
    print("2. Check if server is accessible: curl http://localhost:8889/status")
    print("3. Try single player mode: python main_singleplayer.py")
    print("4. Check console output for error messages")

if __name__ == "__main__":
    main()
