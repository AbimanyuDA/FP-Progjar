#!/usr/bin/env python3
"""
Simple client untuk testing Knight Game Server
Bisa digunakan untuk simulasi pemain tanpa harus menjalankan game
"""

import socket
import json
import time
import threading
import random

class SimpleGameClient:
    def __init__(self, player_id, server_host='127.0.0.1', server_port=8889):
        self.player_id = player_id
        self.server_address = (server_host, server_port)
        self.running = False
        self.x = random.randint(50, 550)
        self.y = random.randint(50, 550)
        self.health = 6
        self.facing_right = True
        self.is_attacking = False
        
    def send_command(self, command):
        """Send command to server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(self.server_address)
            sock.sendall(f"{command}\r\n".encode())
            
            response = b""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data
                break  # For game commands
            
            sock.close()
            return response.decode().strip()
        except Exception as e:
            return f"Error: {e}"
    
    def update_state(self):
        """Update and send player state to server"""
        # Simulate movement
        self.x += random.randint(-5, 5)
        self.y += random.randint(-5, 5)
        
        # Keep within bounds
        self.x = max(0, min(600, self.x))
        self.y = max(0, min(600, self.y))
        
        # Random actions
        self.facing_right = random.choice([True, False])
        self.is_attacking = random.random() < 0.1  # 10% chance to attack
        
        # Simulate occasional damage
        if random.random() < 0.05:  # 5% chance
            self.health = max(0, self.health - 1)
        
        state = {
            'x': self.x,
            'y': self.y,
            'facing_right': self.facing_right,
            'is_attacking': self.is_attacking,
            'health': self.health,
            'is_hit': False
        }
        
        command = f'set_player_state {self.player_id} {json.dumps(state)}'
        result = self.send_command(command)
        return result
    
    def get_all_players(self):
        """Get all players from server"""
        result = self.send_command("get_players")
        try:
            data = json.loads(result)
            if data.get('status') == 'OK':
                return data.get('players', [])
        except json.JSONDecodeError:
            pass
        return []
    
    def get_other_players_state(self):
        """Get state of other players"""
        all_players = self.get_all_players()
        other_players = {}
        
        for player_id in all_players:
            if player_id != self.player_id:
                result = self.send_command(f"get_player_state {player_id}")
                try:
                    data = json.loads(result)
                    if data.get('status') == 'OK':
                        other_players[player_id] = data.get('state', {})
                except json.JSONDecodeError:
                    pass
        
        return other_players
    
    def run_simulation(self, duration=30):
        """Run client simulation"""
        print(f"Starting simulation for player {self.player_id}")
        print(f"Server: {self.server_address[0]}:{self.server_address[1]}")
        print(f"Duration: {duration} seconds")
        print("-" * 50)
        
        self.running = True
        start_time = time.time()
        update_count = 0
        
        try:
            while self.running and (time.time() - start_time) < duration:
                # Update own state
                result = self.update_state()
                update_count += 1
                
                # Every 10 updates, check other players
                if update_count % 10 == 0:
                    other_players = self.get_other_players_state()
                    print(f"[{self.player_id}] Other players: {list(other_players.keys())}")
                    print(f"[{self.player_id}] My position: ({self.x}, {self.y}), Health: {self.health}")
                
                time.sleep(0.5)  # Update twice per second
                
        except KeyboardInterrupt:
            print(f"\n[{self.player_id}] Simulation interrupted")
        finally:
            # Remove player from server
            self.send_command(f"remove_player {self.player_id}")
            print(f"[{self.player_id}] Simulation ended. Updates sent: {update_count}")

def run_multiple_clients(num_clients=3, duration=30, server_port=8889):
    """Run multiple clients simultaneously"""
    print(f"Starting {num_clients} clients for {duration} seconds")
    print("=" * 60)
    
    threads = []
    clients = []
    
    # Create clients
    for i in range(num_clients):
        client = SimpleGameClient(f"test_player_{i+1}", server_port=server_port)
        clients.append(client)
    
    # Start simulation threads
    for client in clients:
        thread = threading.Thread(target=client.run_simulation, args=(duration,))
        thread.start()
        threads.append(thread)
        time.sleep(1)  # Stagger starts
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    print("\nAll client simulations completed!")

def interactive_client():
    """Interactive client mode"""
    print("Interactive Knight Game Client")
    print("=" * 30)
    
    player_id = input("Enter player ID: ").strip()
    if not player_id:
        player_id = f"player_{random.randint(1000, 9999)}"
        print(f"Using auto-generated ID: {player_id}")
    
    server_host = input("Server host [127.0.0.1]: ").strip() or "127.0.0.1"
    server_port = input("Server port [8889]: ").strip()
    server_port = int(server_port) if server_port else 8889
    
    client = SimpleGameClient(player_id, server_host, server_port)
    
    print("\nCommands:")
    print("  update - Update player state")
    print("  players - Show all players")
    print("  state <player_id> - Show player state")
    print("  simulate <seconds> - Run auto simulation")
    print("  quit - Exit")
    print()
    
    try:
        while True:
            command = input(f"[{player_id}]> ").strip().lower()
            
            if command == "quit":
                break
            elif command == "update":
                result = client.update_state()
                print(f"State updated: ({client.x}, {client.y}), Health: {client.health}")
            elif command == "players":
                players = client.get_all_players()
                print(f"All players: {players}")
            elif command.startswith("state "):
                target_id = command.split(" ", 1)[1]
                result = client.send_command(f"get_player_state {target_id}")
                print(f"Player {target_id} state: {result}")
            elif command.startswith("simulate "):
                try:
                    duration = int(command.split(" ", 1)[1])
                    client.run_simulation(duration)
                except (ValueError, IndexError):
                    print("Usage: simulate <seconds>")
            else:
                print("Unknown command. Type 'quit' to exit.")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        client.send_command(f"remove_player {player_id}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "multi":
            num_clients = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            server_port = int(sys.argv[4]) if len(sys.argv) > 4 else 8889
            run_multiple_clients(num_clients, duration, server_port)
        elif sys.argv[1] == "single":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 8889
            client = SimpleGameClient("single_test", server_port=server_port)
            client.run_simulation(duration)
        else:
            print("Usage:")
            print("  python simple_client.py                    # Interactive mode")
            print("  python simple_client.py single [duration] [port]    # Single client")
            print("  python simple_client.py multi [clients] [duration] [port]  # Multiple clients")
    else:
        interactive_client()

if __name__ == "__main__":
    main()
