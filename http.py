import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import json

# Dictionary to store player states
player_states = {}

class HttpServer:
	def __init__(self):
		self.types = {}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'

	# response(kode, message, messagebody, headers)
	def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.1 {} {}\r\n" . format(kode,message))
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
		content_length = 0
		for header in all_headers:
			if header.lower().startswith('content-length:'):
				try:
					content_length = int(header.split(':')[1].strip())
					break
				except (ValueError, IndexError):
					pass
		
		body = ''
		if content_length > 0:
			# Find the start of the body
			body_start = data.find('\r\n\r\n') + len('\r\n\r\n')
			if body_start > 3:
				# The body is after the headers
				# The data received by the server is a string representation of bytes, so we need to handle the escaped characters
				body_raw = data[body_start:]
				# We need to decode the escaped string
				body = bytes(body_raw, "utf-8").decode("unicode_escape")


		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			elif (method=='POST'):
				object_address = j[1].strip()
				return self.http_post(object_address, all_headers, body)

			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})


	def http_get(self,object_address,headers):
		
		# Params Handling
		parsed_url = urlparse(object_address)
		path = parsed_url.path
		query = parsed_url.query

		if (path == '/'):
			return self.response(200,'OK','Ini Adalah web Server percobaan',dict())

		elif (path == '/get_player_ids'):
			ids = list(player_states.keys())
			return self.response(200, 'OK', json.dumps({'status': 'OK', 'players': ids}), {'Content-Type': 'application/json'})

		elif (path == '/get_player_state'):
			params = parse_qs(query)
			player_id = params.get('id', [None])[0]
			player_id = int(player_id) if player_id is not None else None
			if player_id and player_id in player_states:
				return self.response(200, 'OK', json.dumps(player_states[player_id]), {'Content-Type': 'application/json'})
			return self.response(404, 'Not Found', json.dumps({'status': 'Error', 'message': 'Player not found'}), {'Content-Type': 'application/json'})

		return self.response(404, 'Not Found', 'Endpoint not found', {})

	def http_post(self,object_address,headers,body):
		parsed_url = urlparse(object_address)
		path = parsed_url.path

		"""
		Game Authentication
		Untuk registrasi player_id beserta statenya di server
		"""
		if path == '/join_game':
			body_data = json.loads(body)
			player_id = body_data.get('player_id')
			player_id = int(player_id) if player_id is not None else None
			if player_id and player_id not in player_states:
				player_states[player_id] = {
					'position': [0, 0],
					'health': 100,
					'facing_right': True,
					'is_attacking': False,
					'is_hit': False
				}
				print(f"Player {player_id} joined. State: {player_states[player_id]}")
				return self.response(200, 'OK', json.dumps({'status': 'OK'}), {'Content-Type': 'application/json'})
			elif player_id and player_id in player_states:
				print(f"Player {player_id} already exists!")
				return self.response(409, 'Conflict', json.dumps({'status': 'Error', 'message': 'Player ID already in use'}), {'Content-Type': 'application/json'})
			return self.response(400, 'Bad Request', json.dumps({'status': 'Error', 'message': 'Invalid player ID'}), {'Content-Type': 'application/json'})

		elif path == '/leave_game':
			body_data = json.loads(body)
			player_id = body_data.get('player_id')
			player_id = int(player_id) if player_id is not None else None
			if player_id and player_id in player_states:
				del player_states[player_id]
				return self.response(204, 'OK', json.dumps({'status': 'OK'}), {'Content-Type': 'application/json'})
			return self.response(400, 'Bad Request', json.dumps({'status': 'Error', 'message': 'Invalid player ID'}), {'Content-Type': 'application/json'})


		"""
		Game State Management
		Manajemen state dari masing-masing pemain
		"""
		if path == '/set_player_state':
			body_data = json.loads(body)
			player_id = body_data.get('id')
			player_id = int(player_id) if player_id is not None else None
			state_data = body_data.get('state')
			if player_id:
				player_states[player_id] = {
					'position': state_data.get('position', [0, 0]),
					'health': state_data.get('health', 100),
					'facing_right': state_data.get('facing_right', True),
					'is_attacking': state_data.get('is_attacking', False),
					'is_hit': state_data.get('is_hit', False)
				}
				return self.response(200, 'OK', json.dumps({'status': 'OK'}), {'Content-Type': 'application/json'})
			return self.response(400, 'Bad Request', json.dumps({'status': 'Error', 'message': 'Invalid player ID'}), {'Content-Type': 'application/json'})

		return self.response(404, 'Not Found', 'Endpoint not found', {})


if __name__=="__main__":
	httpserver = HttpServer()