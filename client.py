import pygame, socket, selectors, random, json, sys
from pygame_elements import *
from client_config import *
from sockets import *
from gamestate import *

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
	draw_text(window, "enter your name", TEXT_COLOR, LOG_RECT, font)
	font = pygame.font.Font(pygame.font.get_default_font(), 10)
	username_box = InputBox(window, NAME_ENTRY_RECT, BGCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font)
	username_box.draw()
	pygame.display.flip()
	while True:
		clock.tick(LOBBY_RATE)
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
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font, player_name)
	chatbar.draw()
	startbutton = Button(window, CREATE_GAME_RECT, ACTIVE_STARTBUTTON_COLOR, INACTIVE_STARTBUTTON_COLOR, TEXT_COLOR, font, "Create lobby")
	startbutton.draw()
	lobbylist = TextList(window, LOBBYLIST_RECT, BGCOLOR, BGCOLOR, TEXT_COLOR, font)
	pygame.display.flip()
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			if msg.startswith("GLOBAL:"):
				chatbar.add_message(msg[7:])
				chatbar.draw()
				pygame.display.update(chatbar.rect)
			elif msg.startswith("+LOBBY:"):
				lobbylist.add(msg[7:])
				lobbylist.draw()
				pygame.display.update(lobbylist.rect)
			elif msg.startswith("-LOBBY:"):
				lobbylist.remove_by_content(msg[7:])
				lobbylist.draw(lobbylist.rect)
				pygame.display.update(lobbylist.rect)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
				entry = chatbar.handle_event(event)
				if entry: sock.send(encode("GLOBAL:"+player_name+":"+entry))
				if startbutton.handle_event(event):
					sock.send(encode("CREATE"))
					window.fill((0,0,0))
					result = lobby(player_name)
					print(result)
					chatbar.draw()
					startbutton.draw()
					lobbylist.draw()
					pygame.display.flip()
					# Reload the global lobby somehow when it's over
				pygame.display.update((chatbar.rect, startbutton.rect))
			if event.type == pygame.MOUSEMOTION:
				startbutton.handle_event(event)
				pygame.display.update(startbutton.rect)

def lobby(host_name):
	global player_name, sock, selector, window, font, clock
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font, player_name)
	chatbar.draw()
	startbutton = Button(window, START_GAME_RECT, ACTIVE_STARTBUTTON_COLOR, INACTIVE_STARTBUTTON_COLOR, TEXT_COLOR, font, "Launch mission!")
	startbutton.draw()
	playerlist = TextList(window, LOBBY_PLAYERLIST_RECT, BGCOLOR, BGCOLOR, TEXT_COLOR, font)
	playerlist.add(host_name)
	if host_name != player_name: playerlist.add(player_name)
	playerlist.draw()
	pygame.display.flip()
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			if msg.startswith("LOCAL:"):
				chatbar.add_message(msg[6:])
				chatbar.draw()
				pygame.display.update(chatbar.rect)
			elif msg.startswith("-LOBBY:"+host_name):
				# The lobby closed :(
				window.fill((0,0,0))
				return
			elif msg == "START":
				window.fill((0,0,0))
				return play(playerlist.message_list)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
				entry = chatbar.handle_event(event)
				if entry: sock.send(encode("LOCAL:"+player_name+":"+entry))
				if startbutton.handle_event(event): sock.send(encode("START"))
				pygame.display.update((chatbar.rect, startbutton.rect))
			if event.type == pygame.MOUSEMOTION:
				startbutton.handle_event(event)
				pygame.display.update(startbutton.rect)


def play(players):
	global player_name, sock, selector, window, font, clock
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font, player_name)
	chatbar.draw()
	pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	playerlist = TextList(window, GAME_PLAYERLIST_RECT, PANEL_COLOR, PANEL_COLOR, TEXT_COLOR, font)
	# Repopulate the player list.
	for player in players:
		if player != player_name: playerlist.add(player)
	playerlist.draw()
	gamestate = Gamestate(playerlist.message_list+[player_name])
	gamestate.init_station(gamestate.mission.starting_station)
	offset = [0, 0]
	draw_gamestate(window, gamestate, offset)
	pygame.display.flip()
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			print(msg)
			if msg.startswith("LOCAL:"):
				chatbar.add_message(msg[6:])
				chatbar.draw()
				pygame.display.update(chatbar.rect)
			if msg.startswith("SPAWN ENEMIES:"):
				enemy_json = json.loads(msg[14:])
				gamestate.insert_enemies(enemy_json)
				draw_gamestate(window, gamestate, offset)
				pygame.display.flip()
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type == pygame.KEYDOWN:
				entry = chatbar.handle_event(event)
				if entry: sock.send(encode("LOCAL:"+player_name+":"+entry))
				pygame.display.update(chatbar.rect)
			if event.type == pygame.MOUSEBUTTONDOWN:
				chatbar.handle_event(event)
				if GAME_WINDOW_RECT.collidepoint(event.pos):
					pos = reverse_calc_pos(event.pos, offset)
					select_pos(gamestate, pos)
				pygame.display.update((chatbar.rect, PANEL_RECT))

def select_pos(gamestate, clickpos):
	"""select_pos takes a gameboard logical position and finds the object on it, then calls fill_panel."""
	entity = gamestate.occupied(list(clickpos))
	if entity: fill_panel(entity)
	else: pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)

def fill_panel(object):
	"""fills the panel with information about the given object."""
	#First, clear it.
	pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	draw_text(window, object.type, TEXT_COLOR, PANEL_NAME_RECT, font)
	if hasattr(object, 'hull'): draw_bar(window, PANEL_HULL_RECT, TEXT_COLOR, HULL_COLOR, HULL_DAMAGE_COLOR, object.maxhull, object.hull)
	if hasattr(object, 'shield') and object.maxshield > 0: draw_bar(window, PANEL_SHIELD_RECT, TEXT_COLOR, SHIELD_COLOR, SHIELD_DAMAGE_COLOR, object.maxshield, object.shield)

def draw_gamestate(window, gamestate, offset):
	"""The offset is where the player is scrolled to."""
#def draw_grid(window, GAME_WINDOW_RECT, tilesize):
	for x in range(GAME_WINDOW_RECT.left+TILESIZE[0], GAME_WINDOW_RECT.right, TILESIZE[0]):
		pygame.draw.line(window, GRID_COLOR, (x, GAME_WINDOW_RECT.top), (x, GAME_WINDOW_RECT.bottom), 1)
	for y in range(GAME_WINDOW_RECT.top+TILESIZE[1], GAME_WINDOW_RECT.bottom, TILESIZE[1]):
		pygame.draw.line(window, GRID_COLOR, (GAME_WINDOW_RECT.left, y), (GAME_WINDOW_RECT.right, y), 1)
#def draw_entity():
	for entity in gamestate.station:
		window.blit(IMAGE_DICT[entity.type], calc_pos(entity.pos,offset))
	for entity in gamestate.enemy_ships:
		window.blit(IMAGE_DICT[entity.type], calc_pos(entity.pos,offset))
	for entity in gamestate.allied_ships:
		window.blit(IMAGE_DICT[entity.type], calc_pos(entity.pos,offset))
	for entity in gamestate.asteroids:
		window.blit(IMAGE_DICT[entity.type], calc_pos(entity.pos,offset))

def calc_pos(pos, offset):
	"""calc_pos converts a gameboard logical position to a pixel position on screen."""
	return ((pos[0]+offset[0])*TILESIZE[0]+GAME_WINDOW_RECT.left, (pos[1]+offset[1])*TILESIZE[1])

def reverse_calc_pos(pos, offset):
	"""reverse_calc_pos converts a pixel position on screen to a gameboard logical position."""
	return (int((pos[0]-GAME_WINDOW_RECT.left)/TILESIZE[0])-offset[0], int(pos[1]/TILESIZE[1])-offset[1])


if __name__ == '__main__': main()
