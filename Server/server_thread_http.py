from socket import *
import socket
import threading
import time
import sys
import logging
import argparse
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from http import HttpServer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load balancer for multiple game servers
class LoadBalancer:
	def __init__(self, servers):
		self.servers = servers  # List of (host, port) tuples
		self.current = 0
		self.lock = threading.Lock()
		self.server_health = {f"{host}:{port}": True for host, port in servers}
	
	def get_next_server(self):
		"""Round-robin load balancing"""
		with self.lock:
			# Find next healthy server
			attempts = 0
			while attempts < len(self.servers):
				server = self.servers[self.current]
				server_key = f"{server[0]}:{server[1]}"
				self.current = (self.current + 1) % len(self.servers)
				
				if self.server_health.get(server_key, True):
					return server
				attempts += 1
			
			# If no healthy servers, return first one
			return self.servers[0] if self.servers else None
	
	def mark_server_unhealthy(self, host, port):
		"""Mark server as unhealthy"""
		server_key = f"{host}:{port}"
		self.server_health[server_key] = False
		logging.error(f"Server {server_key} marked as unhealthy")
	
	def mark_server_healthy(self, host, port):
		"""Mark server as healthy"""
		server_key = f"{host}:{port}"
		self.server_health[server_key] = True
		logging.info(f"Server {server_key} marked as healthy")

# Global variables
httpserver = HttpServer()
load_balancer = None
processing_model = "thread"  # thread, process, pool


class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address, server_id="main"):
		self.connection = connection
		self.address = address
		self.server_id = server_id
		threading.Thread.__init__(self)

	def run(self):
		rcv=""
		start_time = time.time()
		try:
			while True:
				try:
					data = self.connection.recv(1024)  # Increased buffer size
					if data:
						#merubah input dari socket (berupa bytes) ke dalam string
						#agar bisa mendeteksi \r\n
						d = data.decode()
						rcv=rcv+d
						if rcv[-2:]=='\r\n':
							#end of command, proses string
							logging.info(f"[{self.server_id}] Data from {self.address}: {rcv.strip()}")
							hasil = httpserver.proses(rcv)
							
							#hasil akan berupa bytes
							#untuk bisa ditambahi dengan string, maka string harus di encode
							if not rcv.strip().startswith(('GET', 'POST', 'HTTP')):
								# Game command - no HTTP headers needed
								self.connection.sendall(hasil)
							else:
								# HTTP request - add proper ending
								hasil=hasil+"\r\n\r\n".encode()
								self.connection.sendall(hasil)
							
							processing_time = time.time() - start_time
							logging.info(f"[{self.server_id}] Processed in {processing_time:.3f}s")
							rcv=""
							break
					else:
						break
				except socket.timeout:
					logging.warning(f"[{self.server_id}] Timeout for {self.address}")
					break
				except OSError as e:
					logging.error(f"[{self.server_id}] OSError: {e}")
					break
		finally:
			self.connection.close()



class Server(threading.Thread):
	def __init__(self, host='0.0.0.0', port=8889, server_id="main", max_workers=10):
		self.host = host
		self.port = port
		self.server_id = server_id
		self.max_workers = max_workers
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.my_socket.settimeout(1.0)  # Allow graceful shutdown
		self.running = True
		
		# Thread pool for pool processing model
		if processing_model == "pool":
			self.executor = ThreadPoolExecutor(max_workers=max_workers)
		elif processing_model == "process_pool":
			self.executor = ProcessPoolExecutor(max_workers=max_workers)
		else:
			self.executor = None
			
		threading.Thread.__init__(self)

	def handle_client_pool(self, connection, address):
		"""Handle client using thread/process pool"""
		client_handler = ProcessTheClient(connection, address, self.server_id)
		client_handler.run()

	def run(self):
		try:
			self.my_socket.bind((self.host, self.port))
			self.my_socket.listen(20)  # Increased backlog
			logging.info(f"[{self.server_id}] Server started on {self.host}:{self.port} using {processing_model} model")
			
			while self.running:
				try:
					connection, client_address = self.my_socket.accept()
					connection.settimeout(30.0)  # 30 second timeout per client
					logging.info(f"[{self.server_id}] Connection from {client_address}")

					if processing_model == "thread":
						# Traditional threading model
						clt = ProcessTheClient(connection, client_address, self.server_id)
						clt.start()
						self.the_clients.append(clt)
						
					elif processing_model in ["pool", "process_pool"]:
						# Pool-based model
						if self.executor:
							future = self.executor.submit(self.handle_client_pool, connection, client_address)
						else:
							# Fallback to direct handling
							self.handle_client_pool(connection, client_address)
							
					elif processing_model == "process":
						# Process-based model (simplified)
						clt = ProcessTheClient(connection, client_address, self.server_id)
						clt.start()
						self.the_clients.append(clt)
					
					# Clean up finished threads periodically
					if len(self.the_clients) > 50:
						self.the_clients = [c for c in self.the_clients if c.is_alive()]
						
				except socket.timeout:
					continue
				except OSError as e:
					if self.running:
						logging.error(f"[{self.server_id}] Accept error: {e}")
						time.sleep(0.1)
						
		except Exception as e:
			logging.error(f"[{self.server_id}] Server error: {e}")
		finally:
			self.cleanup()

	def stop(self):
		"""Gracefully stop the server"""
		logging.info(f"[{self.server_id}] Stopping server...")
		self.running = False
		if self.executor:
			self.executor.shutdown(wait=True)

	def cleanup(self):
		"""Clean up resources"""
		try:
			self.my_socket.close()
			if self.executor:
				self.executor.shutdown(wait=False)
			logging.info(f"[{self.server_id}] Server cleanup completed")
		except:
			pass



class LoadBalancedServer:
	"""Main server that can run multiple backend servers with load balancing"""
	def __init__(self, configs):
		self.servers = []
		self.configs = configs
		global load_balancer
		
		# Create load balancer if multiple servers
		if len(configs) > 1:
			server_endpoints = [(cfg['host'], cfg['port']) for cfg in configs]
			load_balancer = LoadBalancer(server_endpoints)
		
		# Create and start servers
		for i, config in enumerate(configs):
			server = Server(
				host=config['host'], 
				port=config['port'], 
				server_id=f"server-{i+1}",
				max_workers=config.get('max_workers', 10)
			)
			self.servers.append(server)
	
	def start_all(self):
		"""Start all servers"""
		logging.info(f"Starting {len(self.servers)} server(s) with {processing_model} processing model")
		for server in self.servers:
			server.start()
		
		# Monitor servers
		try:
			while True:
				time.sleep(10)
				active_servers = sum(1 for s in self.servers if s.is_alive())
				logging.info(f"Active servers: {active_servers}/{len(self.servers)}")
				
				if active_servers == 0:
					logging.error("All servers have stopped!")
					break
					
		except KeyboardInterrupt:
			logging.info("Shutting down servers...")
			self.stop_all()
	
	def stop_all(self):
		"""Stop all servers"""
		for server in self.servers:
			server.stop()
		
		# Wait for servers to stop
		for server in self.servers:
			server.join(timeout=5)

def main():
	global processing_model
	
	parser = argparse.ArgumentParser(description='Knight Game Multiplayer Server')
	parser.add_argument('--model', choices=['thread', 'process', 'pool', 'process_pool'], 
					   default='thread', help='Processing model (default: thread)')
	parser.add_argument('--servers', type=int, default=1, 
					   help='Number of server instances (default: 1)')
	parser.add_argument('--port', type=int, default=8889, 
					   help='Starting port number (default: 8889)')
	parser.add_argument('--workers', type=int, default=10, 
					   help='Max workers for pool models (default: 10)')
	
	args = parser.parse_args()
	processing_model = args.model
	
	# Configure servers
	server_configs = []
	for i in range(args.servers):
		config = {
			'host': '0.0.0.0',
			'port': args.port + i,
			'max_workers': args.workers
		}
		server_configs.append(config)
	
	# Start load balanced server
	lb_server = LoadBalancedServer(server_configs)
	
	try:
		lb_server.start_all()
	except KeyboardInterrupt:
		logging.info("Server interrupted by user")
	finally:
		lb_server.stop_all()

if __name__=="__main__":
	main()

