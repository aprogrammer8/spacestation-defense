"""The main client module. Run this to start the game."""

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
	# TODO: initialize the display with a random background image
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
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			print(msg)
			if msg.startswith("LOCAL:"):
				display.add_chat(msg[6:])
			if msg == "ROUND":
				gamestate.upkeep(clientside=True)
				display.full_redraw()
			if msg.startswith("SPAWN ENEMIES:"):
				enemy_json = json.loads(msg[14:])
				gamestate.insert_enemies(enemy_json)
				display.full_redraw()
			if msg.startswith("ASSIGN:"):
				interpret_assign(gamestate, msg[7:], display)
				# TODO: need a solution for notifying the Display.
			# Unit action happening commands.
			if msg.startswith("ACTION:"):
				execute_move(msg[msg.index(':')+1:], display)
				# TODO: need a solution for involving the Display in this.
		for event in pygame.event.get():
			response = display.event_respond(event)
			# The repsonse is always a message to be sent to the server.
			if response: sock.send(encode(response))


def launch_ship():
	"""Launches a ship from a Hangar."""
	pass

def execute_move(cmd, display):
	"""Takes an ACTION command from the server and executes it. It needs the offset for graphics/animation purposes."""
	print("Executing move:", cmd)
	parts = cmd.split(':')
	entity = gamestate.occupied(json.loads(parts[0]))
	actions = json.loads(parts[1])
	# Subtract power for used components.
	if type(entity) == Component and entity.powered():
		gamestate.station.power -= COMPONENT_POWER_USAGE
		# If a station component was selected, then this needs to be reflected on the panel.
		if type(display.selected) == Component: display.select()

	for action in actions:
		# Moves.
		if len(action) == 2:
			# Could I maybe encapsulate the checking of hangar landing and picking up salvage into entity.move?
			entity.move(action)
			# Handle player ships landing in Hangars.
			# XXX Animating landing will be hard.
			if entity.team == 'player':
				obstacle = gamestate.occupied_area(entity.spaces(), exclude=entity)
				# If there's an obstacle other than a Hangar, then the server sent an invalid move and that's not the client's responsibility.
				if obstacle:
					# Land it: remove it from the list of visible allied ships, and add it to the hangar's contents.
					gamestate.allied_ships.remove(entity)
					obstacle.contents.append(entity)
					# Probably play a landing sound.
					continue
			# Probes pick up salvage when they walk over it.
			if entity.type == "Probe":
				for pos in gamestate.salvages:
					if pos == tuple(entity.pos):
						salvage = gamestate.salvages[pos]
						entity.collect(salvage)
						if salvage.amount <= 0:
							del gamestate.salvages[pos]
							# TODO Make it disappear from display
						break

		# Attacks.
		elif len(action) == 4:
			# TODO Need to start some animation of some kind in a thread
			weapon = entity.weapons[action[0]]
			target = gamestate.occupied(action[1:3])
			# This should happen if we killed the target in a previous attack.
			if not target: continue
			# Nothing is changed in the gamestate if the attack misses.
			if not action[3]: continue
			target.take_damage(weapon.power, weapon.type)
			# Remove dead targets.
			if target.hull <= 0:
				gamestate.remove(target)
				# Spawn salvage pile.
				gamestate.add_salvage(target.pos, Salvage(target.salvage))
				display.draw_gamestate()
		else: print(action, "is an invalid action to marshal")

	# These hopefully won't be necessary in the end.
	display.full_redraw()
	display.select()


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
