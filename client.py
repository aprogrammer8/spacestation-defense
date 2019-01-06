# TODO: turn this into a real system for receiving messages (we'll need to buffer the bytes and use delimiters, I imagine)
def disp_message(sock):
	print(sock.recv(100))

def encode(msg):
	# \x03 is the delimiter byte.
	return bytes(msg+'\x03', 'ascii')

# Initialization
import pygame, socket, selectors, random
import text_wrap, text_input
#import gamestate
from client_config import *
pygame.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode(SCREEN_SIZE)

## TODO: load images and sound files or something
## TODO: initialize the display with a random background image


# Connecting to server and starting main game code
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False)
selector = selectors.DefaultSelector()
selector.register(sock, selectors.EVENT_READ, disp_message)
font = pygame.font.Font(pygame.font.get_default_font(), 10)
text_wrap.draw_text(window, "connecting to server at "+repr(server), (255,255,255), LOG_RECT, font)
pygame.display.flip()
sock.connect_ex(server)
# Wait for the connection
window.fill((0,0,0), LOG_RECT) # Future: draw the background image
pygame.display.update((LOG_RECT))
text_wrap.draw_text(window, "enter your name", (255,255,255), LOG_RECT, font)
font = pygame.font.Font(pygame.font.get_default_font(), 10)
username_box = text_input.InputBox(window, NAME_ENTRY_RECT, (0,0,0), (255,255,255), (0,255,0), (255,255,0), font)
username_box.draw()
pygame.display.flip()


while True:
	clock.tick(100)
	events = selector.select(0)
	for key, _ in events:
		callback = key.data
		callback(key.fileobj)
	for event in pygame.event.get():
		if event.type == pygame.QUIT: sys.exit()
		if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
			name = username_box.handle_event(event)
			if name: sock.send(encode(name))
			username_box.draw()
			pygame.display.flip()
