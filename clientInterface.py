import socket
import logging
import json
from time import sleep

class ClientInterface:
    def __init__(self, server_address=('127.0.0.1', 8885)):
        self.server_address = server_address
        self.sock = None
        self.player_id = None

    def send_command(self, command_str):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # sock.connect(self.server_address)
            logging.warning(f"Connecting to {self.server_address} to send: {command_str}")
            self.sock.sendall(command_str.encode() + "\r\n\r\n".encode())
            data_received = b""
            while True:
                data = self.sock.recv(1024)
                if data:
                    data_received += data
                    if b"\r\n\r\n" in data_received:
                        break
                else:
                    break

            parts = data_received.split(b"\r\n\r\n", 1)
            if len(parts) > 1:
              body_data = parts[1].decode()
              return json.loads(body_data)
            else:
              logging.error("Incomplete response received from server.")
              return None
            # cleaned_data = data_received.split("\r\n\r\n", 1)[0]
            # return json.loads(cleaned_data)
        except Exception as e:
            logging.error(f"Error during command execution: {e}")
            return None

    def join_game(self, player_id):
      """
      - Open socket connection
      - Register player_id to server
      """
      if self.sock:
        logging.warning("Connection already established")
        return True
      try:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server_address)
        self.player_id = player_id

        body = json.dumps({'player_id': player_id})
        command = f"POST /join_game HTTP/1.1\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        result = self.send_command(command)
        if result and result.get('status') == 'OK':
          logging.info(f"Player {player_id} joined the game successfully.")
          return True
        elif result and result.get('status') == 'Error':
          logging.error(f"Failed to join game: {result.get('message', 'Unknown error')}")
          self.sock.close()
          self.sock = None
          return False
      except Exception as e:
        logging.error(f"Error joining game: {e}")
        if self.sock:
          self.sock.close()
          self.sock = None
      return False

    def leave_game(self):
      """
      - Close socket connection
      """
      try:
        body = json.dumps({'player_id': self.player_id})
        command = f"POST /leave_game HTTP/1.1\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        result = self.send_command(command)
        if result and result.get('status') == 'OK':
          logging.info(f"Player {self.player_id} left the game successfully.")
          self.sock.close()
          self.sock = None
          return True
        return False
      except Exception as e:
        logging.error(f"Error leaving game: {e}")
      return False

    def get_all_player_ids(self):
        command = "GET /get_player_ids HTTP/1.1\r\nHost: {self.server_address[0]}"
        result = self.send_command(command)
        if result and result.get('status') == 'OK':
            return result.get('players', [])
        return []

    def get_player_state(self, player_id):
        command = f"GET /get_player_state?id={player_id} HTTP/1.1"
        return self.send_command(command)

    def set_player_state(self, player_id, state):
        body = {
            'id': player_id,
            'state': state
        }
        body = json.dumps(body)
        command = f"POST /set_player_state HTTP/1.1\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        self.send_command(command)

if __name__ == "__main__":
  client = ClientInterface()
  client.join_game(1)
  sleep(1)
  for i in range(1):
    print(client.get_all_player_ids())
    print(f"Before State: {client.get_player_state(1)}")
    state = {
      'position': [100, 200],
      'health': 20,
      'facing_right': True,
      'is_attacking': False,
      'is_hit': False
    }
    print(client.set_player_state(1, state))
    print(f"After State: {client.get_player_state(1)}")
    sleep(1)
  client.leave_game()