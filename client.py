# TODO: turn this into a real system for receiving messages (we'll need to buffer the bytes and use delimiters, I imagine)
def recv_message(sock):
	return sock.recv(100)

def encode(msg):
	# \x03 is the delimiter byte.
	return bytes(msg+'\x03', 'ascii')

# Initialization
import pygame, socket, selectors, random
import text_wrap, text_input
import chat #, gamestate
from client_config import *


def main():
	global player_name, sock, selector, window, sock, font, clock
	pygame.init()
	clock = pygame.time.Clock()
	player_name = ""
	window = pygame.display.set_mode(SCREEN_SIZE)
	font = pygame.font.Font(pygame.font.get_default_font(), 10)
	## TODO: load images and sound files or something
	## TODO: initialize the display with a random background image
	# Connecting to server and starting main game code
	print("connecting to server at "+repr(server)+"...")
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setblocking(False)
	selector = selectors.DefaultSelector()
	selector.register(sock, selectors.EVENT_READ)
	sock.connect_ex(server)
	# Now that we've started the connection, we do the login.

	login_screen()
	window.fill((0,0,0))
	pygame.display.flip()
	global_lobby()


def login_screen():
	global player_name, sock, selector, window, font, clock
	text_wrap.draw_text(window, "enter your name", TEXTCOLOR, LOG_RECT, font)
	font = pygame.font.Font(pygame.font.get_default_font(), 10)
	username_box = text_input.InputBox(window, NAME_ENTRY_RECT, BGCOLOR, TEXTCOLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font)
	username_box.draw()
	pygame.display.flip()
	while True:
		clock.tick(50)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
				player_name = username_box.handle_event(event)
				if player_name:
					# In the future, check with the server that the name is available.
					sock.send(encode(player_name))
					return
				pygame.display.update(username_box.rect)

def global_lobby():
	global player_name, sock, selector, window, font, clock
	chatbar = chat.Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXTCOLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font, player_name)
	chatbar.draw()
	pygame.display.flip()
	while True:
		clock.tick(50)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			if msg.startswith("+LOBBY:"):
				lobbylist.add(msg[7:])
				lobbylist.draw()
				pygame.display.update()
			elif msg.startswith("-LOBBY:"):
				lobbylist.add(msg[7:])
				lobbylist.draw()
				pygame.display.update()
			else:
				chatbar.add_message(string(msg))
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
				chatbar.handle_event(event)
				pygame.display.update(chatbar.rect)

if __name__ == '__main__': main()
