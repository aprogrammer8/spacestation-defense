# A client-side module that handles the display during game.

import pygame, sys
from pygame_elements import *
from client_config import *
from gamestate import *

class GameDisplay:
	"""An object that handles the screen during a game of Spacestation Defense. It abstracts so that the main module won't have to worry about pygame at all - theoretically the game could support a text-based version by only replacing this class."""
	def __init__(self, window, player_name, gamestate):
		self.window = window
		grid_size = [GAME_WINDOW_RECT.w//TILESIZE[0], GAME_WINDOW_RECT.h//TILESIZE[1]]
		self.offset = [grid_size[0]//2, grid_size[1]//2]
		self.player_name = player_name
		self.gamestate = gamestate
		self.draw_gamestate()
		self.chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, FONT, player_name)
		self.chatbar.draw()
		# Blank the panel to begin.
		pygame.draw.rect(window, PANEL_COLOR, TOP_PANEL_RECT, 0)
		pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
		# Fill out the top panel.
		self.playerlist = TextList(window, GAME_PLAYERLIST_RECT, PANEL_COLOR, PANEL_COLOR, TEXT_COLOR, FONT, [player.name for player in gamestate.players])
		self.playerlist.draw()
		self.done_button = Button(window, DONE_BUTTON_RECT, ACTIVE_DONE_BUTTON_COLOR, INACTIVE_DONE_BUTTON_COLOR, TEXT_COLOR, FONT, "Done")
		self.done_button.draw()
		# For other buttons that might be created temporarily, such as Hangar launch buttons.
		self.panel_buttons = []
		# Update display.
		pygame.display.flip()
		# Selected Entity.
		self.selected = None
		# When assigning a unit that has weapons, this is set to an int instead of True.
		self.assigning = False

	def event_respond(self, event):
		"""The basic method for receiving an event from pygame and reacting to it."""
		# In the case of mousemotion, all we need to do is check all the buttons to see if they need to be redrawn.
		# For now, mousemotion outside of the panel doesn't do anything.
		if event.type == pygame.MOUSEMOTION and TOTAL_PANEL_RECT.collidepoint(event.pos):
			rects_to_update = []
			for button in self.panel_buttons + [self.done_button]:
				if button.handle_mousemotion(event):
					rects_to_update.append(button.rect)
			pygame.display.update(rects_to_update)

		# Clicks are a little more complicated. We have to handle the callbacks of any buttons clicked, and account for clicks on the rest of the screen.
		if event.type == pygame.MOUSEBUTTONDOWN:
			# Recolor chatbar entry box if necesary.
			if self.chatbar.handle_mousebuttondown(event):
				pygame.display.update(self.chatbar.entry_box.rect)

			# Game widow click events.
			if GAME_WINDOW_RECT.collidepoint(event.pos):
				# This must be checked with "is False", because 0 would mean True for this purpose.
				pos = self.reverse_calc_pos(event.pos)
				if self.assigning is False: self.select_pos(pos)
				# The only things that can be assigned by clicking are weapons, because movement is always done with the arrow keys.
				elif self.selected.weapons:
					target = self.gamestate.occupied(pos)
					# If you try to target nothing, we assume you want to deselect the unit, since that would almost never be a mistake.
					if not target:
						self.assigning = False
						self.select_pos(pos)
					# Don't let things target themselves.
					elif target == self.selected:
						SFX_ERROR.play()
					# Valid targets.
					elif self.gamestate.in_range(self.selected, self.selected.weapons[self.assigning].type, target):
						self.selected.target(self.assigning, target.pos)
						self.assigning += 1
						if self.assigning == len(self.selected.weapons): self.assigning = 0
						self.select()
						return "ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps(self.selected.actions)
					# If the target is valid, but not reachable.
					else:
						SFX_ERROR.play()

			# Panel click events.
			else:
				# Done button.
				if self.done_button.handle_mousebuttondown(event): return "DONE"
				# Whatever other buttons are around. For the time being, this is just Hangar launch buttons.
				for button in self.panel_buttons:
					callback = button.handle_mousebuttondown(event)
					if callback:
						print("Display returning button callback:", callback)
						return callback

		# Keypresses.
		elif event.type == pygame.KEYDOWN:
			# If the chatbar is active, just pass it the input and don't bother with gamestate commands.
			if self.chatbar.entry_box.active:
				entry = self.chatbar.handle_event(event)
				pygame.display.update(self.chatbar.rect)
				if entry: return "LOCAL:" + self.player_name + ":" + entry

			# Everything else depends on something being selected, so instead of adding the condition everywhere, I just put a return here.
			elif not self.selected: return

			# Entering assignment mode.
			elif event.key == pygame.K_SPACE:
				# The players can't assign actions to enemies or to asteroids, or to units that don't have any abilities.
				if self.selected in self.gamestate.enemy_ships or self.selected in self.gamestate.asteroids or (not self.selected.weapons and not self.selected.speed):
					SFX_ERROR.play()
					return
				# TODO: Probably play a sound and give some visual indication.
				self.clear_projected_move()
				self.selected.actions = []
				if self.selected.weapons: self.assigning = 0
				else: self.assigning = True
				# TODO This needs to update the panel
				# Clear out old actions.
				return "ASSIGN:" + json.dumps(self.selected.pos) + ":[]"

			# Esc gets out of assignment mode.
			elif event.key == pygame.K_ESCAPE:
				self.assigning = False
				self.select()

			# Shift cycles weapons.
			elif self.assigning is not False and (event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT):
				self.assigning += 1
				if self.assigning == len(self.selected.weapons): self.assigning = 0

			# Q, W, and E are the unique action keys.
			elif event.key == pygame.K_q:
				# Shield Generators can turn off to save power (I would have them activate like a normal component but you almost always want them on).
				if self.selected.type == "Shield Generator":
					self.selected.actions.append(False)
					# TODO
				elif self.selected.type == "Hangar": self.fill_panel_hangar()
				else: SFX_ERROR.play()
			elif event.key == pygame.K_w:
				# Shield Generators can also consume power to regenerate, but not project their shields so they can't be damaged and interrupted.
				if self.selected.type == "Shield Generator":
					self.selected.actions.append(True)
					# TODO
				else: SFX_ERROR.play()
			elif event.key == pygame.K_e:
				# To turn the shield generator back on, we can just clear its actions.
				if self.selected.type == "Shield Generator":
					self.selected.actions = []
					#TODO
				elif self.selected.type == "Hangar": self.select()
				else: SFX_ERROR.play()

			# Movement keys.
			elif self.selected.moves_left():
				if event.key == pygame.K_UP: move = [0, -1]
				elif event.key == pygame.K_DOWN: move = [0, 1]
				elif event.key == pygame.K_LEFT: move = [-1, 0]
				elif event.key == pygame.K_RIGHT: move = [1, 0]
				else: return
				obstacle = self.gamestate.invalid_move(self.selected, move)
				if obstacle and obstacle.type != "Hangar":
					SFX_ERROR.play()
					return
				self.selected.actions.append(move)
				self.project_move()
				return "ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps(self.selected.actions)

		# Closing the game. We handle this last because it's the rarest.
		elif event.type == pygame.QUIT: sys.exit()

	def add_chat(self, msg):
		"""Add a message to the chat bar and automatically update the display."""
		self.chatbar.add_message(msg)
		pygame.display.update(self.chatbar.rect)

	def calc_pos(self, pos):
		"""calc_pos converts a gameboard logical position to a pixel position on screen."""
		return ((pos[0] + self.offset[0]) * TILESIZE[0]+GAME_WINDOW_RECT.left, (pos[1] + self.offset[1]) * TILESIZE[1])

	def reverse_calc_pos(self, pos):
		"""reverse_calc_pos converts a pixel position on screen to a gameboard logical position."""
		return [int(pos[0] - GAME_WINDOW_RECT.left) // TILESIZE[0] - self.offset[0], pos[1] // TILESIZE[1] - self.offset[1]]

	def fill_panel(self, salvage=None):
		"""fills the panel with information about the given object."""
		# First, clear it.
		pygame.draw.rect(self.window, PANEL_COLOR, PANEL_RECT, 0)
		# Right now, the only thing that puts buttons on the panel when selected is Hangars in details mode. But that's handled by fill_panel_hangar.
		self.panel_buttons = []
		# Draw info of whatever salvage is here first, so that it still gets drawn if there's no object.
		if salvage: draw_text(self.window, str(salvage), TEXT_COLOR, PANEL_SALVAGE_RECT, FONT)
		# This catch is here so we can call fill_panel() with nothing selected to blank it.
		if not self.selected:
			pygame.display.update(PANEL_RECT)
			return
		draw_text(self.window, self.selected.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
		# This must be checked with "is False", because 0 would mean True for this purpose.
		if self.assigning is not False: draw_text(self.window, "Assigning...", ASSIGNING_TEXT_COLOR, PANEL_ASSIGNING_RECT, FONT)
		else: pygame.draw.rect(self.window, PANEL_COLOR, PANEL_ASSIGNING_RECT, 0)
		# Hull and shield.
		draw_text(self.window, str(self.selected.hull)+"/"+str(self.selected.maxhull), TEXT_COLOR, PANEL_HULL_RECT, FONT)
		draw_bar(self.window, PANEL_HULL_BAR_RECT, TEXT_COLOR, HULL_COLOR, HULL_DAMAGE_COLOR, self.selected.maxhull, self.selected.hull)
		if self.selected.maxshield > 0:
			draw_text(self.window, shield_repr(self.selected), TEXT_COLOR, PANEL_SHIELD_RECT, FONT)
			draw_bar(self.window, PANEL_SHIELD_BAR_RECT, TEXT_COLOR, SHIELD_COLOR, SHIELD_DAMAGE_COLOR, self.selected.maxshield, self.selected.shield)
		y = 0
		if self.selected.weapons:
			draw_text(self.window, "Weapons:", TEXT_COLOR, PANEL_WEAPON_DESC_BEGIN, FONT)
			y += 20
			for weapon in self.selected.weapons:
				y += draw_text(self.window, str(weapon)+self.selected.desc_target(weapon,self.gamestate), TEXT_COLOR, pygame.Rect(PANEL_WEAPON_DESC_BEGIN.x+5, PANEL_WEAPON_DESC_BEGIN.y+y, PANEL_WEAPON_DESC_BEGIN.w-7, 60), FONT)
		# Now draw special properties.
		if self.selected.type == "Probe":
			rect = PANEL_SHIELD_BAR_RECT.move(0, y+30)
			draw_text(self.window, "Salvage: " + str(self.selected.load) + "/" + str(PROBE_CAPACITY), TEXT_COLOR, rect, FONT)
			draw_bar(self.window, rect.move(0,20), TEXT_COLOR, CAPACITY_COLOR, CAPACITY_EMPTY_COLOR, PROBE_CAPACITY, self.selected.load)
		# Station components also display the pooled power.
		if self.selected in self.gamestate.station:
			draw_text(self.window, power_repr(self.gamestate.station), TEXT_COLOR, PANEL_POWER_RECT, FONT)
			draw_bar(self.window, PANEL_POWER_BAR_RECT, TEXT_COLOR, POWER_COLOR, POWER_LOW_COLOR, self.gamestate.station.maxpower(), self.gamestate.station.power)
			# Hangars show a summary of their contents when selected.
			if self.selected.type == "Hangar":
				rect = PANEL_SHIELD_BAR_RECT.move(0, 30)
				draw_text(self.window, "Capacity: " + str(self.selected.current_fill()) + "/" + str(HANGAR_CAPACITY), TEXT_COLOR, rect, FONT)
				rect.move_ip(0, 20)
				draw_bar(self.window, rect, TEXT_COLOR, CAPACITY_COLOR, CAPACITY_EMPTY_COLOR, HANGAR_CAPACITY, self.selected.current_fill())
				rect.inflate_ip(0, 100)
				# Give it more space, since we're starting from the shield bar rect and this might need to be several lines long.
				# And we give it 50 extra pixels because inflate_ip expands in both directions, so it moved up by 50.
				rect.move_ip(0, 80)
				draw_text(self.window, "Contains: " + self.selected.summarize_contents(), TEXT_COLOR, rect, FONT)

		pygame.display.update(PANEL_RECT)

	def fill_panel_hangar(self):
		"""An alternative to fill_panel called on a Hangar to show the details of its contents."""
		# First, clear it.
		pygame.draw.rect(self.window, PANEL_COLOR, PANEL_RECT, 0)
		# And I guess still bother saying it's a hangar.
		draw_text(self.window, self.selected.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
		# Prepare to return a list of Buttons. We need them to persist after the panel is drawn so play() can use them.
		self.panel_buttons = []
		# Give them more space, and move it back down to compensate.
		y = 50
		rect = PANEL_NAME_RECT.inflate(0, 40).move(0, 20+y)
		for ship in self.selected.contents:
			text = ship.hangar_describe()
			# Subtracting 2 from the width because it also needs to fit inside the Button.
			h = get_height(text, rect.w-2, FONT)
			button = Button(self.window, pygame.Rect(rect.x, rect.y, rect.w, h+2), ACTIVE_HANGAR_BUTTON_COLOR, INACTIVE_HANGAR_BUTTON_COLOR, TEXT_COLOR, FONT, text)
			button.draw()
			self.panel_buttons.append(button)
			#h = draw_text(self.window, ship.hangar_describe(), TEXT_COLOR, rect, FONT)
			rect.move_ip(0, h+5)

		pygame.display.update(PANEL_RECT)

	def select_pos(self, pos):
		"""Takes a gameboard logical position and finds the object on it, then calls fill_panel and projects its planned move."""
		# First clear the currently projected move if we're selecting away from sonething else.
		if self.selected: self.clear_projected_move()
		entity = self.gamestate.occupied(list(pos))
		self.selected = entity
		if entity:
			self.project_move()
		else:
			# If we're clearing self.selected, we should get out of assigning mode too.
			self.assigning = False
		self.select(pos)

	def select(self, pos=None):
		"""An envelope around fill_panel that also finds the salvage under the selected Entity.
		   If pos is not provided, select will pass whatever salvage is under the selected Entity to fill_panel.
		   If pos is provided, select will check that pos for salvage instead. This is useful to selecte a space with no Entity on it.
		"""
		if not pos: pos = self.selected.pos
		# FIXME This is an imperfect method, as it makes it impossible to see salvage that's under a big ship but not under its central pos.
		salvage = None
		for s in self.gamestate.salvages:
			if s.pos == pos: salvage = s
		self.fill_panel(salvage)

	def project_move(self):
		"""Show a yellow path from the selected Entity projecting the moves it's going to make."""
		pos = (self.selected.pos[0]+self.offset[0], self.selected.pos[1]+self.offset[1])
		for move in self.selected.moves_planned():
			pos = (pos[0]+move[0], pos[1]+move[1])
			pygame.draw.rect(self.window, (255,255,0), (GAME_WINDOW_RECT.left+TILESIZE[0]*pos[0], GAME_WINDOW_RECT.top+TILESIZE[1]*pos[1], TILESIZE[0], TILESIZE[1]), 2)
		pygame.display.flip()

	def clear_projected_move(self):
		"""Clears the yellow projected path from an Entity while assigning move commands to it."""
		rect = pygame.Rect(self.selected.move_rect())
		rect = pygame.Rect(self.calc_pos(rect.topleft), (rect.size[0]*TILESIZE[0], rect.size[1]*TILESIZE[1]))
		self.window.fill((0,0,0), rect)
		# Redraw the other gamestate entities clobbered when we erased.
		# It seems like rounding requires a +1,+1 expansion.
		self.draw_gamestate(rect.inflate_ip(1,1))

	def entity_pixel_rect(self, entity):
		"""Finds the rectangle that an Entity is occupying (in terms of pixels)."""
		rect = entity.rect()
		return pygame.Rect(self.calc_pos(rect[0:2]), (rect[2]*TILESIZE[0], rect[3]*TILESIZE[1]))

	def erase(self, rect):
		"""Takes a pixel rect and erases only the gameboard entities on it (by redrawing the grid.)"""
		self.window.fill((0,0,0), rect)
		draw_grid(rect)

	def draw_grid(self, rect=None):
		"""Draw the game window grid within the specified Rect."""
		if not rect: rect = GAME_WINDOW_RECT
		for x in range(rect.left, rect.right, TILESIZE[0]):
			pygame.draw.line(self.window, GRID_COLOR, (x, rect.top), (x, rect.bottom), 1)
		for y in range(rect.top, rect.bottom, TILESIZE[1]):
			pygame.draw.line(self.window, GRID_COLOR, (rect.left, y), (rect.right, y), 1)

	def draw_gamestate(self, rect=None):
		"""Draw the game window within the specified Rect. It's measured in logical position, not pixel position."""
		if not rect: rect = GAME_WINDOW_RECT
		self.draw_grid(rect) # self.reverse_calc_pos?
		for salvage in self.gamestate.salvages:
			if GAME_WINDOW_RECT.colliderect(self.entity_pixel_rect(salvage)):
				self.window.blit(IMAGE_DICT['salvage'], self.calc_pos(salvage.pos))
		for entity in self.gamestate.station:
			if GAME_WINDOW_RECT.colliderect(self.entity_pixel_rect(entity)):
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.enemy_ships:
			if GAME_WINDOW_RECT.colliderect(self.entity_pixel_rect(entity)):
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.allied_ships:
			if GAME_WINDOW_RECT.colliderect(self.entity_pixel_rect(entity)):
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.asteroids:
			if GAME_WINDOW_RECT.colliderect(self.entity_pixel_rect(entity)):
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		pygame.display.flip()

	def full_redraw(self):
		"""Blank and redraw the entire game window."""
		self.window.fill((0,0,0), GAME_WINDOW_RECT)
		self.draw_gamestate()
