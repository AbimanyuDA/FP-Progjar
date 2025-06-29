import sys
import os.path
import uuid
import json
import threading
import time
from glob import glob
from datetime import datetime

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
		
		# Game state management
		self.game_players = {}  # {player_id: {state_data}}
		self.player_lock = threading.Lock()
		self.last_activity = {}  # {player_id: timestamp}
		self.player_timeout = 30  # seconds
		
		# Start cleanup thread
		self.cleanup_thread = threading.Thread(target=self._cleanup_inactive_players, daemon=True)
		self.cleanup_thread.start()
	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self,data):
		
		requests = data.split("\r\n")
		#print(requests)

		baris = requests[0]
		#print(baris)

		all_headers = [n for n in requests[1:] if n!='']

		# Check if this is a game command (not HTTP)
		if not baris.startswith('HTTP') and not baris.startswith('GET') and not baris.startswith('POST'):
			return self._handle_game_command(baris)

		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method=='POST'):
				object_address = j[1].strip()
				return self.http_post(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})
	
	def _handle_game_command(self, command_line):
		"""Handle game-specific commands"""
		command, player_id, data = self._parse_command(command_line)
		
		if command == "get_players":
			players = self.get_all_players()
			result = {
				"status": "OK",
				"players": players
			}
			return json.dumps(result).encode()
		
		elif command == "get_player_state" and player_id:
			state = self.get_player_state(player_id)
			if state is not None:
				result = {
					"status": "OK",
					"state": state
				}
			else:
				result = {
					"status": "ERROR",
					"message": "Player not found"
				}
			return json.dumps(result).encode()
		
		elif command == "set_player_state" and player_id and data:
			self.set_player_state(player_id, data)
			result = {
				"status": "OK",
				"message": "State updated"
			}
			return json.dumps(result).encode()
		
		elif command == "remove_player" and player_id:
			self.remove_player(player_id)
			result = {
				"status": "OK",
				"message": "Player removed"
			}
			return json.dumps(result).encode()
		
		else:
			result = {
				"status": "ERROR",
				"message": "Invalid command"
			}
			return json.dumps(result).encode()
	def http_get(self,object_address,headers):
		files = glob('./*')
		#print(files)
		thedir='./'
		if (object_address == '/'):
			return self.response(200,'OK','Knight Multiplayer Game Server - Ready!',dict())

		if (object_address == '/status'):
			status_info = {
				"server": "Knight Game Server",
				"active_players": len(self.game_players),
				"players": list(self.game_players.keys()),
				"timestamp": datetime.now().isoformat()
			}
			return self.response(200,'OK', json.dumps(status_info), {'Content-Type': 'application/json'})

		if (object_address == '/health'):
			return self.response(200,'OK','Server is healthy',dict())

		if (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
		if (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())

		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
		#harus membaca dalam bentuk byte dan BINARY
		isi = fp.read()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types.get(fext, 'application/octet-stream')
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)
	def http_post(self,object_address,headers):
		headers ={}
		isi = "kosong"
		return self.response(200,'OK',isi,headers)
		
	def _cleanup_inactive_players(self):
		"""Background thread to remove inactive players"""
		while True:
			try:
				current_time = time.time()
				with self.player_lock:
					inactive_players = []
					for player_id, last_time in self.last_activity.items():
						if current_time - last_time > self.player_timeout:
							inactive_players.append(player_id)
					
					for player_id in inactive_players:
						if player_id in self.game_players:
							del self.game_players[player_id]
						if player_id in self.last_activity:
							del self.last_activity[player_id]
				
				time.sleep(5)  # Check every 5 seconds
			except Exception as e:
				print(f"Cleanup thread error: {e}")
				time.sleep(5)

	def get_all_players(self):
		"""Get list of all active player IDs"""
		with self.player_lock:
			return list(self.game_players.keys())

	def get_player_state(self, player_id):
		"""Get state of specific player"""
		with self.player_lock:
			return self.game_players.get(player_id, None)

	def set_player_state(self, player_id, state):
		"""Set state of specific player"""
		with self.player_lock:
			self.game_players[player_id] = state
			self.last_activity[player_id] = time.time()

	def remove_player(self, player_id):
		"""Remove player from game"""
		with self.player_lock:
			if player_id in self.game_players:
				del self.game_players[player_id]
			if player_id in self.last_activity:
				del self.last_activity[player_id]

	def _parse_command(self, command_line):
		"""Parse game command from request line"""
		parts = command_line.strip().split(' ', 2)
		if len(parts) < 2:
			return None, None, None
		
		command = parts[0]
		if command == "get_players":
			return "get_players", None, None
		elif command == "get_player_state" and len(parts) >= 2:
			return "get_player_state", parts[1], None
		elif command == "set_player_state" and len(parts) >= 3:
			try:
				state_data = json.loads(parts[2])
				return "set_player_state", parts[1], state_data
			except json.JSONDecodeError:
				return None, None, None
		elif command == "remove_player" and len(parts) >= 2:
			return "remove_player", parts[1], None
		
		return None, None, None
#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)
	#d = httpserver.http_get('testing2.txt',{})
	#print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)















