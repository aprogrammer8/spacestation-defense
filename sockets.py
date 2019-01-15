def recv_message(sock):
	buffer = ''
	while len(buffer) == 0 or buffer[-1] != '\x00': buffer += sock.recv(100).decode('ascii')
	return buffer[:-1]

def encode(msg):
	# \x00 is the delimiter byte.
	return bytes(msg+'\x00', 'ascii')
