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
	global font
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
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font, player_name)
	chatbar.draw()
	startbutton = Button(window, CREATE_GAME_RECT, ACTIVE_STARTBUTTON_COLOR, INACTIVE_STARTBUTTON_COLOR, TEXT_COLOR, font, "Create lobby")
	startbutton.draw()
	lobbylist = ButtonList(window, LOBBYLIST_RECT, BGCOLOR, BGCOLOR, TEXT_COLOR, ACTIVE_LOBBYBUTTON_COLOR, INACTIVE_LOBBYBUTTON_COLOR, font)
	pygame.display.flip()
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			if msg.startswith("GLOBAL:"):
				chatbar.add_message(msg[7:])
				pygame.display.update(chatbar.rect)
			elif msg.startswith("+LOBBY:"):
				lobbylist.add(msg[7:])
				pygame.display.update(lobbylist.rect)
			elif msg.startswith("-LOBBY:"):
				lobbylist.remove_by_content(msg[7:])
				pygame.display.update(lobbylist.rect)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type == pygame.KEYDOWN:
				entry = chatbar.handle_event(event)
				if entry: sock.send(encode("GLOBAL:"+player_name+":"+entry))
				pygame.display.update(chatbar.rect)
			if event.type == pygame.MOUSEBUTTONDOWN:
				entry = chatbar.handle_event(event)
				join = lobbylist.handle_event(event)
				if join:
					sock.send(encode("JOIN:"+join))
					window.fill((0,0,0))
					result = lobby(player_name)
					print(result)
					chatbar.draw()
					startbutton.draw()
					lobbylist.draw()
					pygame.display.flip()
					# Reload the global lobby somehow when it's over
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
				lobbylist.handle_event(event)
				for button in lobbylist.button_list: pygame.display.update(button.rect)
				startbutton.handle_event(event)
				pygame.display.update(startbutton.rect)

def lobby(host_name):
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
				pygame.display.update(chatbar.rect)
			if msg.startswith("JOIN:"):
				playerlist.add(msg[5:])
				pygame.display.update(playerlist.rect)
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
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, font, player_name)
	chatbar.draw()
	pygame.draw.rect(window, PANEL_COLOR, TOP_PANEL_RECT, 0)
	pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	playerlist = TextList(window, GAME_PLAYERLIST_RECT, PANEL_COLOR, PANEL_COLOR, TEXT_COLOR, font)
	# Repopulate the player list.
	for player in players:
		if player != player_name: playerlist.add(player)
	playerlist.draw()
	done_button = Button(window, DONE_BUTTON_RECT, ACTIVE_DONE_BUTTON_COLOR, INACTIVE_DONE_BUTTON_COLOR, TEXT_COLOR, font, "Done")
	done_button.draw()
	gamestate = Gamestate(playerlist.message_list+[player_name])
	gamestate.init_station(gamestate.mission.starting_station)
	grid_size = [int(GAME_WINDOW_RECT.w/TILESIZE[0]), int(GAME_WINDOW_RECT.h/TILESIZE[1])]
	offset = [int(grid_size[0]/2), int(grid_size[1]/2)]
	selected = None
	targeting = False
	draw_gamestate(gamestate, offset)
	pygame.display.flip()
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			print(msg)
			if msg.startswith("LOCAL:"):
				chatbar.add_message(msg[6:])
				pygame.display.update(chatbar.rect)
			if msg == "ROUND":
				gamestate.clear()
				fill_panel(selected)
				pygame.display.update(PANEL_RECT)
			if msg.startswith("SPAWN ENEMIES:"):
				enemy_json = json.loads(msg[14:])
				gamestate.insert_enemies(enemy_json)
				draw_gamestate(gamestate, offset)
				pygame.display.flip()
			if msg.startswith("ASSIGN:"):
				interpret_assign(gamestate, msg[7:])
			if msg.startswith("UNASSIGN ALL:"):
				interpret_unassign(gamestate, msg[msg.index(':')+1:])
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type == pygame.KEYDOWN:
				entry = chatbar.handle_event(event)
				if entry: sock.send(encode("LOCAL:"+player_name+":"+entry))
				pygame.display.update(chatbar.rect)
				if event.key == pygame.K_SPACE:
					# Don't interpret space as a command when the chatbar is active.
					if chatbar.entry_box.active: continue
					if selected and selected.weapons:
						# TODO: Probably play a sound and give some visual indication.
						# Clear out old targets.
						sock.send(encode("UNASSIGN ALL:" + str(selected.pos[0]) + ',' + str(selected.pos[1])))
						for weapon in selected.weapons: weapon.target = None
						fill_panel(selected)
						pygame.display.update(PANEL_RECT)
						targeting = True
				if event.key == pygame.K_ESCAPE:
					targeting = False
			if event.type == pygame.MOUSEBUTTONDOWN:
				chatbar.handle_event(event)
				if done_button.handle_event(event):
					sock.send(encode("DONE"))
					continue
				if GAME_WINDOW_RECT.collidepoint(event.pos):
					pos = reverse_calc_pos(event.pos, offset)
					if targeting:
						target = gamestate.occupied(pos)
						if not target:
							selected = None
							targeting = False
							pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
							pygame.display.update(PANEL_RECT)
							continue
						# Don't let things target themselves.
						if target == selected:
							SFX_ERROR.play()
							targeting = False
							continue
						if gamestate.in_range(selected, selected.next_weapon().type, target):
							sock.send(encode("ASSIGN:" + str(selected.pos[0]) + "," + str(selected.pos[1]) + ":" + str(selected.weapons.index(selected.next_weapon())) + ":" + str(target.pos[0]) + "," + str(target.pos[1])))
							selected.next_weapon().target = target
							if not selected.next_weapon(): targeting = False
							fill_panel(selected)
							pygame.display.update(PANEL_RECT)
						else:
							SFX_ERROR.play()
					else:
						selected = select_pos(gamestate, pos)
						pygame.display.update(PANEL_RECT)
				pygame.display.update(chatbar.rect)
			if event.type == pygame.MOUSEMOTION:
				done_button.handle_event(event)
				pygame.display.update(done_button.rect)

def select_pos(gamestate, clickpos):
	"""select_pos takes a gameboard logical position and finds the object on it, then calls fill_panel."""
	entity = gamestate.occupied(list(clickpos))
	if entity: fill_panel(entity)
	else: pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	return entity

def fill_panel(object):
	"""fills the panel with information about the given object."""
	#First, clear it.
	pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	draw_text(window, object.type, TEXT_COLOR, PANEL_NAME_RECT, font)
	draw_text(window, str(object.hull)+"/"+str(object.maxhull), TEXT_COLOR, PANEL_HULL_RECT, font)
	if hasattr(object, 'hull'): draw_bar(window, PANEL_HULL_BAR_RECT, TEXT_COLOR, HULL_COLOR, HULL_DAMAGE_COLOR, object.maxhull, object.hull)
	if hasattr(object, 'shield') and object.maxshield > 0:
		draw_text(window, shield_repr(object), TEXT_COLOR, PANEL_SHIELD_RECT, font)
		draw_bar(window, PANEL_SHIELD_BAR_RECT, TEXT_COLOR, SHIELD_COLOR, SHIELD_DAMAGE_COLOR, object.maxshield, object.shield)
	if object.weapons:
		draw_text(window, "Weapons:", TEXT_COLOR, PANEL_WEAPON_DESC_BEGIN, font)
		y = 20
		for weapon in object.weapons:
			y += draw_text(window, str(weapon), TEXT_COLOR, pygame.Rect(PANEL_WEAPON_DESC_BEGIN.x+5, PANEL_WEAPON_DESC_BEGIN.y+y, PANEL_WEAPON_DESC_BEGIN.w-7, 60), font)

def shield_repr(entity):
	string = str(entity.shield)+"/"+str(entity.maxshield)+"    + "+str(entity.shield_regen_amounts[entity.shield_regen_pointer])+" / "
	for amount in entity.shield_regen_amounts:
		string += str(amount) + "->"
	return string[:-2]

def draw_gamestate(gamestate, offset):
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
	return [int((pos[0]-GAME_WINDOW_RECT.left)/TILESIZE[0])-offset[0], int(pos[1]/TILESIZE[1])-offset[1]]

def execute_move(cmd):
	parts = cmd.split(':')
	entity = gamestate.occupied(json.loads(parts[0]))
	moves = json.loads(parts[1])
	for move in moves:
		pass # Do some animation
	targets = json.loads(parts[2])
	weapon_index = 0
	for target_coords in targets:
		# Do some animation
		# Skip weapons that weren't targeted.
		if not target_coords: continue
		target = gamestate.occupied(target_coords)
		target.take_damage(entity.weapons[weapon_index].dmg, entity.weapons[weapon_index].type)
		weapon_index += 1

if __name__ == '__main__': main()
