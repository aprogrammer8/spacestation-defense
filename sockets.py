def recv_message(sock):
	buffer = ''
	while len(buffer) == 0 or buffer[-1] != '\x03': buffer += sock.recv(1).decode('ascii')
	return buffer[:-1]

def encode(msg):
	# \x00 is the delimiter byte.
	return bytes(msg+'\x03', 'ascii')
