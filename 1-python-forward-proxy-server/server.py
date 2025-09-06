"""
A simple multithreaded Python forward proxy server supporting both HTTP and HTTPS (CONNECT) requests.

This module provides a TCP proxy server that listens for incoming client connections, parses HTTP/HTTPS requests,
establishes connections to target servers, and forwards data bidirectionally between clients and remote servers.

Functions:
	handle_client(client_socket: socket.socket) -> None

	forward_data(client_sock: socket.socket, remote_sock: socket.socket) -> None
		Forwards data bidirectionally between a client socket and a remote socket using two threads.

	start(host, port) -> None

Usage:
	Run this script directly to start the proxy server on the specified host and port.
"""

import socket
import threading


def handle_client(client_socket: socket.socket) -> None:
	"""
	Handles an incoming client socket connection, parses the HTTP/HTTPS request,
	establishes a connection to the target server, and forwards data between the client
	and the remote server.
	Args:
		client_socket (socket.socket): The client socket object representing the incoming connection.
	Behavior:
		- For HTTP requests, parses the request, connects to the target server on port 80,
		  forwards the request, and relays data between client and server.
		- For HTTPS (CONNECT) requests, establishes a tunnel to the target server on port 443,
		  sends a 200 Connection established response, and relays encrypted data.
		- Closes the client socket upon completion or error.
	"""
	try:
		request: bytes = client_socket.recv(4096)
		if not request:
			client_socket.close()
		request_data = request.decode('utf-8')
		print(f"Received request: \n{request_data}")

		first_line = request_data.split("\n")[0]
		method, url, _ = first_line.split()

		if method.upper() == "CONNECT":
			print("HTTPS Connection: 200")
			host_port = url.split(':')
			host = host_port[0]
			port = int(host_port[1]) if len(host_port) > 1 else 443

			remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote_socket.connect((host, port))

			client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
			forward_data(client_socket, remote_socket)
		else:
			print("HTTP Connection: 200")
			url = url.split("://")[-1]
			host = url.split('/')[0]
			port = 80

			remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote_socket.connect((host, port))
			remote_socket.sendall(request_data.encode())

			forward_data(client_socket, remote_socket)
	except Exception as e:
		print(f"Error: {e}")
	finally:
		client_socket.close()


def forward_data(client_sock: socket.socket, remote_sock: socket.socket) -> None:
	"""
	Forwards data bidirectionally between a client socket and a remote socket.
	This function creates two threads to handle simultaneous data transfer:
	one thread forwards data from the client socket to the remote socket,
	and the other thread forwards data from the remote socket to the client socket.
	Both sockets are closed after the data forwarding is complete.
	Args:
		client_sock (socket.socket): The client socket to forward data from and to.
		remote_sock (socket.socket): The remote socket to forward data from and to.
	Returns:
		None
	"""
	def forward(source: socket.socket, destination: socket.socket):
		"""
		Forwards data from the source socket to the destination socket.
		Continuously reads data from the source socket in chunks of up to 8192 bytes,
		sends the data to the destination socket, and accumulates the response.
		Stops forwarding when no more data is received or an exception occurs.
		Args:
			source (socket.socket): The socket to read data from.
			destination (socket.socket): The socket to send data to.
		"""
		response = b""
		while True:
			try:
				data = source.recv(8192)
				if not data:
					break
				response += data
				destination.sendall(data)
			except Exception:
				break
	source_handler = threading.Thread(target=forward, args=(client_sock, remote_sock))
	dest_handler = threading.Thread(target=forward, args=(remote_sock, client_sock))
	source_handler.start()
	dest_handler.start()
	source_handler.join()
	dest_handler.join()
	client_sock.close()
	remote_sock.close()

def start(host, port) -> None:
	"""
	Starts a TCP proxy server that listens for incoming client connections on the specified host and port.
	Args:
		host (str): The hostname or IP address to bind the server to.
		port (int): The port number to listen on.
	Behavior:
		- Creates a socket server that accepts incoming TCP connections.
		- For each client connection, spawns a new daemon thread to handle the client using the `handle_client` function.
		- Prints status messages for server start and accepted connections.
		- Gracefully shuts down the server on KeyboardInterrupt.
	Raises:
		None
	"""
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.bind((host, port))
	server.listen(5)
	print(f"[*] Proxy Server listening on {host}:{port}")
	try:
		while True:
			client_socket, addr = server.accept()
			print(f"[*] Accepted connection from {addr}")
			client_handler = threading.Thread(target=handle_client, args=(client_socket,), daemon=True)
			client_handler.start()
	except KeyboardInterrupt:
		pass
	finally:
		server.close()

if __name__ == '__main__':
	start('', 9919)
