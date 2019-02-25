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
	pygame.display.set_caption("Spacestation Defense")
	pygame.key.set_repeat(KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)
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
			if msg.startswith("LEAVE:"):
				playerlist.remove_by_content(msg[6:])
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
	# The missed_buffer is for server messages that this function missed because they arrived during an animation.
	global gamestate, offset, missed_buffer
	missed_buffer = []
	gamestate = Gamestate(players)
	gamestate.init_station(gamestate.mission.starting_station)
	display = GameDisplay(window, player_name, gamestate)
	while True:
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			handle_server_msg(msg, display)
		# Catch missed messages.
		for m in missed_buffer:
			handle_server_msg(m, display)
		missed_buffer.clear()
		for event in pygame.event.get():
			response = display.event_respond(event)
			# The repsonse is always a message to be sent to the server.
			if response: sock.send(encode(response))


def handle_server_msg(msg, display):
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
	# Unit action happening commands.
	if msg.startswith("ACTION:"):
		execute_move(msg[msg.index(':')+1:], display)


def launch_ship():
	"""Launches a ship from a Hangar."""
	pass

def execute_move(cmd, display):
	"""Takes an ACTION command from the server and executes it. It needs the offset for graphics/animation purposes."""
	print("Executing move:", cmd)
	parts = cmd.split(';')
	entity = gamestate.occupied(json.loads(parts[0]))
	actions = json.loads(parts[1])
	if not entity:
		print("Entity dead already: ", json.loads(parts[0]), ", planned actions =", actions)
		return
	entity.shield_regen()
	# Subtract power for used components.
	if type(entity) == Component and entity.powered():
		if not gamestate.station.use_power(): return
		# If a station component was selected, then this needs to be reflected on the panel.
		if type(display.selected) == Component: display.select()
	for action in actions:
		# Turning off power to auto-running components.
		if action['type'] == 'off':
			# Nothing we need to do here.
			continue
		# Shield Generators hiding their shields.
		elif action['type'] == 'hide':
			# Not yet implemented.
			continue
		# Factory assignments.
		elif action['type'] == 'build':
			entity.project = action['ship']
			entity.hangar = action['hangar']
		# Hangar launches.
		elif action['type'] == 'launch':
			gamestate.hangar_launch(entity, action['index'], action['pos'], action['rot'])
			display.full_redraw()
		# Moves.
		elif action['type'] == 'move':
			display.move(entity, action['move'])
			await_animation(display)
			# Don't process remaining actions if the ship lands in a Hangar.
			if gamestate.move(entity, action['move']) == "LANDED":
				# But we still have to deselect it. If the player could retain selection of a ship landed in a Hangar, that could cause a lot of problems.
				if display.selected == entity: display.deselect()
				break
		# Attacks.
		elif action['type'] == 'attack':
			weapon = entity.weapons[action['weapon']]
			target = gamestate.occupied(action['target'])
			# This should happen if we killed the target in a previous attack.
			if not target: continue
			# Nothing is changed in the gamestate if the attack misses.
			if not action['hit']: continue
			target.take_damage(weapon.power, weapon.type)
			# Remove dead targets.
			if target.hull <= 0:
				gamestate.remove(target)
				# Spawn salvage pile.
				gamestate.add_salvage(Salvage(target.pos, target.salvage))
				display.draw_gamestate()

		else: print(action, "is an invalid action")

	# The legality checks (besides the power check) are handled inside the method.
	if entity.type == "Factory": entity.work()

	# This hopefully won't be necessary in the end.
	display.full_redraw()


def await_animation(display):
	"""This function is used to ensure that chat and selection can still take place during animation."""
	global missed_buffer
	while display.anim.is_alive():
		clock.tick(LOBBY_RATE)
		events = selector.select(0)
		for key, _ in events:
			msg = recv_message(key.fileobj)
			print(msg)
			if msg.startswith("LOCAL:"):
				display.add_chat(msg[6:])
			else:
				missed_buffer.append(msg)
		for event in pygame.event.get():
			response = display.event_respond(event)
			# The repsonse is always a message to be sent to the server.
			if response: sock.send(encode(response))

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
