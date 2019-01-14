import socket, selectors, random, sys
from gamestate import *
from sockets import *

def main():
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	#sock.setblocking(False)
	selector = selectors.DefaultSelector()
	selector.register(sock, selectors.EVENT_READ)
	sock.connect(sys.argv[1])
	recv_message(sock)

if __name__ == '__main__': main()

#Actually, I wonder if the server should actually be blocking. What does it need to do besides run the game, litsen for player input, and send it back out?
