from socket import *
import socket
import threading
import time
import sys
import logging
import http as game_http

httpserver = game_http.HttpServer()


class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		rcv=""
		while True:
			try:
				data = self.connection.recv(1024)
				if data:
					#merubah input dari socket (berupa bytes) ke dalam string
					#agar bisa mendeteksi \r\n
					d = data.decode()
					rcv=rcv+d

					if '\r\n\r\n' in rcv:
						lines = rcv.split('\r\n')
						request_line = lines[0]
						method = request_line.split()[0].upper()

						if method == 'POST':
							# Ambil Content-Length header
							content_length = 0
							for line in lines:
								if line.lower().startswith('content-length:'):
									content_length = int(line.split(':')[1].strip())
									break

							header_end = rcv.find('\r\n\r\n') + 4
							body_received = len(rcv) - header_end

							if body_received < content_length:
								continue

						#end of command, proses string
						logging.warning("data dari client: {}" . format(rcv))
						hasil = httpserver.proses(rcv)
						#hasil akan berupa bytes
						#untuk bisa ditambahi dengan string, maka string harus di encode
						hasil=hasil+"\r\n\r\n".encode()
						logging.warning("balas ke  client: {}" . format(hasil))
						#hasil sudah dalam bentuk bytes
						self.connection.sendall(hasil)
						rcv=""
						# self.connection.close()
				else:
					break
			except OSError as e:
				pass
		self.connection.close()



class Server(threading.Thread):
	def __init__(self):
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0', 8885))
		self.my_socket.listen(1)
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			logging.warning("connection from {}".format(self.client_address))

			clt = ProcessTheClient(self.connection, self.client_address)
			clt.start()
			self.the_clients.append(clt)



def main():
	logging.basicConfig(level=logging.WARNING)
	print("Server Starting...")
	svr = Server()
	svr.start()
	try:
		svr.join()
	except KeyboardInterrupt:
		print("Server stopping...")

if __name__=="__main__":
	main()