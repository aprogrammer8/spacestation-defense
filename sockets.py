"""A couple of useful functions to make transmitting data between client and server more elegant."""

def recv_message(sock) -> str:
	"""Call on the socket when you know there's a message. This will return it."""
	buffer = ''
	while not buffer or buffer[-1] != '\x00':
		buffer += sock.recv(1).decode('ascii')
	return buffer[:-1]

def encode(msg) -> bytes:
	"""Call before sending any message to the server."""
	# \x00 is the delimiter byte.
	return bytes(msg+'\x00', 'ascii')
