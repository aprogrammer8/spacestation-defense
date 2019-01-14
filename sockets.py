# TODO: turn this into a real system for receiving messages (we'll need to buffer the bytes and use delimiters, I imagine)
def recv_message(sock):
	buffer = ''
	while len(buffer) == 0 or buffer[-1] != '\x03': buffer += sock.recv(100).decode('ascii')
	return buffer[:-1]

def encode(msg):
	# \x03 is the delimiter byte.
	return bytes(msg+'\x03', 'ascii')
