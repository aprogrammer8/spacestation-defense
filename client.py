# TODO: turn this into a real system for receiving messages (we'll need to buffer the bytes and use delimiters, I imagine)
def disp_message(sock):
	print(sock.recv(3))

# Initialization
import pygame, socket, selectors, random
from client_config import *
pygame.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode((1800, 1000))

## TODO: load images and sound files or something
## TODO: initialize the display with a random background image

print("Connecting to server at", server) #TODO: this should eventually be a message on screen
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False)
selector = selectors.DefaultSelector()
selector.register(sock, selectors.EVENT_READ, disp_message)
sock.connect_ex(server)


while True:
	clock.tick(100)
	events = selector.select(0)
	for key, _ in events:
		callback = key.data
		callback(key.fileobj)
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
			print("A pressed")
