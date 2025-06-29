#!/usr/bin/env python3
"""
Test script untuk Knight Game Server
"""

import socket
import json
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor

class GameServerTester:
    def __init__(self, host='127.0.0.1', port=8889):
        self.host = host
        self.port = port
    
    def send_command(self, command):
        """Send command to server and get response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, self.port))
            
            # Send command
            sock.sendall(f"{command}\r\n".encode())
            
            # Receive response
            response = b""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data
                # For game commands, no HTTP headers expected
                if command.startswith(('get_', 'set_', 'remove_')):
                    break
            
            sock.close()
            return response.decode().strip()
            
        except Exception as e:
            return f"Error: {e}"
    
    def test_basic_commands(self):
        """Test basic game commands"""
        print("=== Testing Basic Game Commands ===")
        
        # Test get_players (empty)
        print("1. Testing get_players (should be empty):")
        result = self.send_command("get_players")
        print(f"   Result: {result}")
        
        # Test set_player_state
        print("\n2. Testing set_player_state:")
        player_state = {
            "x": 100,
            "y": 200,
            "facing_right": True,
            "is_attacking": False,
            "health": 6,
            "is_hit": False
        }
        command = f'set_player_state player1 {json.dumps(player_state)}'
        result = self.send_command(command)
        print(f"   Command: {command}")
        print(f"   Result: {result}")
        
        # Test get_player_state
        print("\n3. Testing get_player_state:")
        result = self.send_command("get_player_state player1")
        print(f"   Result: {result}")
        
        # Test get_players (should have player1)
        print("\n4. Testing get_players (should have player1):")
        result = self.send_command("get_players")
        print(f"   Result: {result}")
        
        # Test remove_player
        print("\n5. Testing remove_player:")
        result = self.send_command("remove_player player1")
        print(f"   Result: {result}")
        
        # Test get_players (should be empty again)
        print("\n6. Testing get_players (should be empty again):")
        result = self.send_command("get_players")
        print(f"   Result: {result}")
    
    def test_http_endpoints(self):
        """Test HTTP endpoints"""
        print("\n=== Testing HTTP Endpoints ===")
        
        endpoints = [
            "GET / HTTP/1.1\r\nHost: localhost\r\n",
            "GET /status HTTP/1.1\r\nHost: localhost\r\n", 
            "GET /health HTTP/1.1\r\nHost: localhost\r\n"
        ]
        
        for i, endpoint in enumerate(endpoints, 1):
            print(f"\n{i}. Testing {endpoint.split()[1]}:")
            result = self.send_command(endpoint)
            print(f"   Result: {result[:200]}{'...' if len(result) > 200 else ''}")
    
    def simulate_player(self, player_id, duration=10):
        """Simulate a player for load testing"""
        start_time = time.time()
        commands_sent = 0
        
        while time.time() - start_time < duration:
            try:
                # Set player state
                state = {
                    "x": int(time.time() % 600),
                    "y": int((time.time() * 2) % 600),
                    "facing_right": (int(time.time()) % 2) == 0,
                    "health": 6
                }
                command = f'set_player_state {player_id} {json.dumps(state)}'
                self.send_command(command)
                commands_sent += 1
                
                # Get player state occasionally
                if commands_sent % 5 == 0:
                    self.send_command(f"get_player_state {player_id}")
                
                time.sleep(0.1)  # 10 commands per second
                
            except Exception as e:
                print(f"Player {player_id} error: {e}")
                break
        
        # Clean up
        self.send_command(f"remove_player {player_id}")
        return commands_sent
    
    def test_load(self, num_players=5, duration=10):
        """Test server load with multiple simulated players"""
        print(f"\n=== Load Testing with {num_players} players for {duration} seconds ===")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_players) as executor:
            futures = []
            for i in range(num_players):
                future = executor.submit(self.simulate_player, f"test_player_{i}", duration)
                futures.append(future)
            
            # Wait for all players to finish
            total_commands = 0
            for future in futures:
                try:
                    commands = future.result()
                    total_commands += commands
                except Exception as e:
                    print(f"Player simulation error: {e}")
        
        actual_duration = time.time() - start_time
        print(f"Load test completed:")
        print(f"  Duration: {actual_duration:.2f} seconds")
        print(f"  Total commands: {total_commands}")
        print(f"  Commands per second: {total_commands/actual_duration:.2f}")
    
    def test_invalid_commands(self):
        """Test invalid commands"""
        print("\n=== Testing Invalid Commands ===")
        
        invalid_commands = [
            "invalid_command",
            "get_player_state",  # Missing player_id
            "set_player_state player1",  # Missing state
            "set_player_state player1 invalid_json",
            ""
        ]
        
        for i, cmd in enumerate(invalid_commands, 1):
            print(f"\n{i}. Testing invalid command: '{cmd}'")
            result = self.send_command(cmd)
            print(f"   Result: {result}")

def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8889
    
    print(f"Testing Knight Game Server on localhost:{port}")
    print("=" * 50)
    
    tester = GameServerTester(port=port)
    
    try:
        # Test server connectivity
        result = tester.send_command("get_players")
        if "Error" in result:
            print(f"Cannot connect to server: {result}")
            print("Make sure server is running with:")
            print(f"  python server_thread_http.py --port {port}")
            return
        
        # Run tests
        tester.test_basic_commands()
        tester.test_http_endpoints()
        tester.test_invalid_commands()
        
        # Ask for load test
        response = input("\nRun load test? (y/N): ").strip().lower()
        if response == 'y':
            players = input("Number of players (default 5): ").strip()
            duration = input("Duration in seconds (default 10): ").strip()
            
            players = int(players) if players else 5
            duration = int(duration) if duration else 10
            
            tester.test_load(players, duration)
        
        print("\n=== Testing Complete ===")
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
    except Exception as e:
        print(f"Testing error: {e}")

if __name__ == "__main__":
    main()
