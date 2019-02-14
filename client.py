import pygame, socket, selectors, random, json, sys
from pygame_elements import *
from client_config import *
from sockets import *
from gamestate import *
from client_display import *

def main():
	global player_name, sock, selector, window, sock, clock
	clock = pygame.time.Clock()
	player_name = ""
	window = pygame.display.set_mode(SCREEN_SIZE, depth=24)
	init_images()
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
	global player_name
	draw_text(window, "enter your name", TEXT_COLOR, LOG_RECT, FONT)
	username_box = InputBox(window, NAME_ENTRY_RECT, BGCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, FONT)
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
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, FONT, player_name)
	chatbar.draw()
	startbutton = Button(window, CREATE_GAME_RECT, ACTIVE_STARTBUTTON_COLOR, INACTIVE_STARTBUTTON_COLOR, TEXT_COLOR, FONT, "Create lobby")
	startbutton.draw()
	lobbylist = ButtonList(window, LOBBYLIST_RECT, BGCOLOR, BGCOLOR, TEXT_COLOR, ACTIVE_LOBBYBUTTON_COLOR, INACTIVE_LOBBYBUTTON_COLOR, FONT)
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
				chatbar.handle_event(event)
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
	chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, FONT, player_name)
	chatbar.draw()
	startbutton = Button(window, START_GAME_RECT, ACTIVE_STARTBUTTON_COLOR, INACTIVE_STARTBUTTON_COLOR, TEXT_COLOR, FONT, "Launch mission!")
	startbutton.draw()
	playerlist = TextList(window, LOBBY_PLAYERLIST_RECT, BGCOLOR, BGCOLOR, TEXT_COLOR, FONT, items=[player_name])
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
	global gamestate, offset
	gamestate = Gamestate(players)
	gamestate.init_station(gamestate.mission.starting_station)
	display = GameDisplay(window, player_name, gamestate)
	### Redoing
	#selected = None
	# When assigning a unit that has weapons, this is set to an int instead of True.
	#assigning = False
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			print(msg)
			if msg.startswith("LOCAL:"):
				display.chatbar.add_message(msg[6:])
				pygame.display.update(chatbar.rect)
			if msg == "ROUND":
				gamestate.upkeep(clientside=True)
				window.fill((0,0,0), GAME_WINDOW_RECT)
				display.draw_gamestate()
				panel_buttons = fill_panel(selected)
				pygame.display.flip()
			if msg.startswith("SPAWN ENEMIES:"):
				enemy_json = json.loads(msg[14:])
				gamestate.insert_enemies(enemy_json)
				display.draw_gamestate()
				pygame.display.flip()
			if msg.startswith("ASSIGN:"):
				interpret_assign(gamestate, msg[7:])
			if msg.startswith("UNASSIGN ALL:"):
				interpret_unassign(gamestate, msg[msg.index(':')+1:])
			# Unit action happening commands.
			if msg.startswith("ACTION:"):
				execute_move(msg[msg.index(':')+1:])
				panel_buttons = fill_panel(selected)
				pygame.display.update(PANEL_RECT)
		for event in pygame.event.get():
			response = display.event_respond(event)
			# The respose from the display module (if not None) is always a tuple: (type, data)
			if response:
				if response[0] == "BUTTON":
					if response[1] == "done": sock.send(encode("DONE"))
				elif response[0] == "CHAT":
					sock.send(encode(response[1]))

def select_pos(clickpos):
	"""select_pos takes a gameboard logical position and finds the object on it, then calls fill_panel and projects its planned move."""
	entity = gamestate.occupied(list(clickpos))
	if tuple(clickpos) in gamestate.salvages: salvage = gamestate.salvages[tuple(clickpos)]
	else: salvage = None
	fill_panel(entity, salvage)
	if entity: project_move(entity)
	return entity

def fill_panel(object, salvage=None, assigning=False):
	"""fills the panel with information about the given object. Returns a list of buttons on the panel that should be kept track of so they can respond."""
	# First, clear it.
	pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	# Draw info of whatever salvage is here first, so that it still gets drawn if there's no object.
	if salvage: draw_text(window, str(salvage), TEXT_COLOR, PANEL_SALVAGE_RECT, FONT)
	# This catch is here so we can call fill_panel(None) to blank it.
	if not object: return []
	draw_text(window, object.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
	if assigning: draw_text(window, "Assigning...", ASSIGNING_TEXT_COLOR, PANEL_ASSIGNING_RECT, FONT)
	else: pygame.draw.rect(window, PANEL_COLOR, PANEL_ASSIGNING_RECT, 0)
	# Hull and shield.
	draw_text(window, str(object.hull)+"/"+str(object.maxhull), TEXT_COLOR, PANEL_HULL_RECT, FONT)
	draw_bar(window, PANEL_HULL_BAR_RECT, TEXT_COLOR, HULL_COLOR, HULL_DAMAGE_COLOR, object.maxhull, object.hull)
	if object.maxshield > 0:
		draw_text(window, shield_repr(object), TEXT_COLOR, PANEL_SHIELD_RECT, FONT)
		draw_bar(window, PANEL_SHIELD_BAR_RECT, TEXT_COLOR, SHIELD_COLOR, SHIELD_DAMAGE_COLOR, object.maxshield, object.shield)
	y = 0
	if object.weapons:
		draw_text(window, "Weapons:", TEXT_COLOR, PANEL_WEAPON_DESC_BEGIN, FONT)
		y += 20
		for weapon in object.weapons:
			y += draw_text(window, str(weapon)+object.desc_target(weapon,gamestate), TEXT_COLOR, pygame.Rect(PANEL_WEAPON_DESC_BEGIN.x+5, PANEL_WEAPON_DESC_BEGIN.y+y, PANEL_WEAPON_DESC_BEGIN.w-7, 60), FONT)
	# Now draw special properties.
	if object.type == "Probe":
		rect = PANEL_SHIELD_BAR_RECT.move(0, y+30)
		draw_text(window, "Salvage: " + str(object.load) + "/" + str(PROBE_CAPACITY), TEXT_COLOR, rect, FONT)
		draw_bar(window, rect.move(0,20), TEXT_COLOR, CAPACITY_COLOR, CAPACITY_EMPTY_COLOR, PROBE_CAPACITY, object.load)
	# Station components also display the pooled power.
	if object in gamestate.station:
		draw_text(window, power_repr(), TEXT_COLOR, PANEL_POWER_RECT, FONT)
		draw_bar(window, PANEL_POWER_BAR_RECT, TEXT_COLOR, POWER_COLOR, POWER_LOW_COLOR, gamestate.station.maxpower(), gamestate.station.power)
		# Hangars show a summary of their contents when selected.
		if object.type == "Hangar":
			rect = PANEL_SHIELD_BAR_RECT.move(0, 30)
			draw_text(window, "Capacity: " + str(object.current_fill()) + "/" + str(HANGAR_CAPACITY), TEXT_COLOR, rect, FONT)
			rect.move_ip(0, 20)
			draw_bar(window, rect, TEXT_COLOR, CAPACITY_COLOR, CAPACITY_EMPTY_COLOR, HANGAR_CAPACITY, object.current_fill())
			rect.inflate_ip(0, 100)
			# Give it more space, since we're starting from the shield bar rect and this might need to be several lines long.
			# And we give it 50 extra pixels because inflate_ip expands in both directions, so it moved up by 50.
			rect.move_ip(0, 80)
			draw_text(window, "Contains: " + object.summarize_contents(), TEXT_COLOR, rect, FONT)
	return []


def fill_panel_hangar(object):
	"""An alternative to fill_panel called on a Hangar to show the details of its contents."""
	# First, clear it.
	pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
	# And I guess still bother saying it's a hangar.
	draw_text(window, object.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
	# Prepare to return a list of Buttons. We need them to persist after the panel is drawn so play() can use them.
	buttons = []
	# Give them more space, and move it back down to compensate.
	y = 50
	rect = PANEL_NAME_RECT.inflate(0, 40).move(0, 20+y)
	for ship in object.contents:
		text = ship.hangar_describe()
		# Subtracting 2 from the width because it also needs to fit inside the Button.
		h = get_height(text, rect.w-2, FONT)
		button = Button(window, pygame.Rect(rect.x, rect.y, rect.w, h+2), ACTIVE_HANGAR_BUTTON_COLOR, INACTIVE_HANGAR_BUTTON_COLOR, TEXT_COLOR, FONT, text)
		button.draw()
		buttons.append(button)
		#h = draw_text(window, ship.hangar_describe(), TEXT_COLOR, rect, FONT)
		rect.move_ip(0, h+5)
	return buttons


def shield_repr(entity):
	"""Returns a string suitable to label the shield bar on the panel."""
	string = str(entity.shield)+"/"+str(entity.maxshield)+"    + "+str(entity.shield_regen_amounts[entity.shield_regen_pointer])+" / "
	for amount in entity.shield_regen_amounts:
		string += str(amount) + "->"
	return string[:-2]

def power_repr():
	"""Returns a string suitable to label the power bar on a Station component."""
	string = str(gamestate.station.power) + "(" + str(gamestate.station.projected_power()) + ") / " + str(gamestate.station.maxpower()) + "    + " + str(POWER_GEN_SPEED * len(gamestate.station.power_generators()))
	return string

def project_move(entity):
	"""Show a yellow path from a selected Entity projecting the moves it's going to make."""
	pos = (entity.pos[0]+offset[0], entity.pos[1]+offset[1])
	for move in entity.actions:
		# Skip non-moves.
		if len(move) != 2: continue
		pos = (pos[0]+move[0], pos[1]+move[1])
		pygame.draw.rect(window, (255,255,0), (GAME_WINDOW_RECT.left+TILESIZE[0]*pos[0], GAME_WINDOW_RECT.top+TILESIZE[1]*pos[1], TILESIZE[0], TILESIZE[1]), 2)
	pygame.display.flip()

def clear_projected_move(entity):
	"""Clears the yellow projected path from an Entity while assigning move commands to it."""
	rect = pygame.Rect(entity.move_rect())
	rect = pygame.Rect(calc_pos(rect.topleft), (rect.size[0]*TILESIZE[0], rect.size[1]*TILESIZE[1]))
	window.fill((0,0,0), rect) # Temporary until we get a background image.
	draw_gamestate(rect.inflate_ip(1,1))
	pygame.display.flip()

def entity_pixel_rect(entity):
	"""Finds the rectangle that an Entity is occupying (in terms of pixels)."""
	rect = entity.rect()
	return pygame.Rect(calc_pos(rect[0:2]), (rect[2]*TILESIZE[0], rect[3]*TILESIZE[1]))

def erase(rect):
	"""Takes a pixel rect and erases only the gameboard entities on it (by redrawing the grid.)"""
	window.fill((0,0,0), rect)
	draw_grid(rect)

def launch_ship():
	"""Launches a ship from a Hangar."""
	pass

def execute_move(cmd):
	"""Takes an ACTION command from the server and executes it. It needs the offset for graphics/animation purposes."""
	print("Executing move:", cmd)
	parts = cmd.split(':')
	entity = gamestate.occupied(json.loads(parts[0]))
	actions = json.loads(parts[1])
	# Subtract power for used components.
	if type(entity) == Component and entity.powered(): gamestate.station.power -= COMPONENT_POWER_USAGE
	for action in actions:
		# Moves.
		if len(action) == 2:
			# TODO: This should be smoothly animated
			# TODO: Need to make sure stuff won't get overwritten.
			rect = entity_pixel_rect(entity)
			erase(rect)
			entity.move(action)
			# Handle player ships landing in Hangars.
			if entity.team == 'player':
				obstacle = gamestate.occupied_area(entity.spaces(), exclude=entity)
				# We assume there's only one obstacle and that it's a hangar, because if either of those is not the case then something else is wrong.
				if obstacle:
					# Land it: remove it from the list of visible allied ships, and add it to the hangar's contents.
					gamestate.allied_ships.remove(entity)
					obstacle.contents.append(entity)
					# Probably play a landing sound.
					continue
			# We redraw old stuff on the now vacated space, incase there was salvage or something.
			draw_gamestate(rect)
			window.blit(IMAGE_DICT[entity.type], calc_pos(entity.pos))
			# Probes pick up salvage when they walk over it.
			if entity.type == "Probe":
				for pos in gamestate.salvages:
					if pos == tuple(entity.pos):
						salvage = gamestate.salvages[pos]
						entity.collect(salvage)
						if salvage.amount <= 0:
							del gamestate.salvages[pos]
							draw_gamestate()
						break
			#draw_gamestate(gamestate, entity_pixel_rect(entity))
			pygame.display.flip()
			pygame.time.wait(500)
		# Attacks.
		elif len(action) == 4:
			weapon = entity.weapons[action[0]]
			target = gamestate.occupied(action[1:3])
			# This should happen if we killed the target in a previous attack.
			if not target: continue
			# TODO: Do some animation
			# Nothing is changed in the gamestate if the attack misses.
			if not action[3]: continue
			target.take_damage(weapon.power, weapon.type)
			# Remove dead targets.
			if target.hull <= 0:
				rect = entity_pixel_rect(target)
				erase(rect)
				# TODO: Animate.
				gamestate.remove(target)
				# Spawn salvage pile.
				gamestate.add_salvage(target.pos, Salvage(target.salvage))
				window.blit(IMAGE_DICT['salvage'], calc_pos(target.pos))
				pygame.display.update(rect)
		else: print(action, "is an invalid action to marshal")


def init_images():
	"""The images defined in client_config.py need to be fixed for transparency. But client_config.py can't do that, because it runs before the pygame display has been initialized. So we do it here."""
	for entity in IMAGE_DICT:
		image = pygame.image.load(IMAGE_DICT[entity]).convert()
		# Shield Generator has white that's part of the image. But it also takes up the entire thing, so it doesn't need a colorkey.
		if entity == "Shield Generator":
			pass
		else:
			image.set_colorkey((255,255,255))
		IMAGE_DICT[entity] = image

if __name__ == '__main__': main()
