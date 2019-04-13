"""A client-side module that handles the display during game. It never changes the gamestate."""

import pygame, sys, threading
from pygame_elements import *
from client_config import *
from gamestate import *
from util import *
from rules import *

class GameDisplay:
	"""An object that handles the screen during a game of Spacestation Defense. It abstracts so that the main module won't have to worry about pygame at all - theoretically the game could support a text-based version by only replacing this class."""
	def __init__(self, window, player_name, gamestate):
		self.window = window
		# Current running animation.
		self.anim = None
		# For concurrency.
		self.lock = threading.Lock()
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
		self.details_view = False
		# This variable holds whatever data needs holding during a unit assignment: the index of the weapon being targeted, the name of the ship being assigned to a Factory, or a dict of information about the ship being launched from a Hangar.
		self.assigning = None
		# The name of the player whose hand is selected.
		self.hand = None

	def event_respond(self, event) -> list:
		"""The basic method for receiving an event from pygame and reacting to it. Returns a list of commands that should be sent up to the server."""
		if event.type == pygame.MOUSEMOTION:
			# If the mouse is over the panel, we just need to check if any buttons need to be updated.
			if TOTAL_PANEL_RECT.collidepoint(event.pos):
				rects_to_update = []
				for button in self.panel_buttons + [self.done_button]:
					if button.handle_mousemotion(event):
						rects_to_update.append(button.rect)
				self.lock.acquire()
				pygame.display.update(rects_to_update)
				self.lock.release()
			# This happens while placing something.
			elif GAME_WINDOW_RECT.collidepoint(event.pos) and type(self.assigning) == dict:
				pos = self.reverse_calc_pos(event.pos)
				if pos != self.assigning['pos']:
					self.clear_projected_placement(flip=True)
					self.assigning['pos'] = pos
					self.project_placement(flip=True)

		# Clicks.
		if event.type == pygame.MOUSEBUTTONDOWN:
			# Chatbar entry box - recolor if necesary.
			if self.chatbar.handle_mousebuttondown(event):
				self.lock.acquire()
				pygame.display.update(self.chatbar.entry_box.rect)
				self.lock.release()

			# Game widow click events.
			if GAME_WINDOW_RECT.collidepoint(event.pos):
				pos = self.reverse_calc_pos(event.pos)
				# Selecting units - the most basic case.
				if self.assigning is None: self.select(pos)
				# Targeting weapons.
				elif type(self.assigning) == int:
					target = self.gamestate.occupied(pos)
					# If you try to target nothing, we assume you want to deselect the unit, since that would almost never be a mistake.
					if not target:
						self.assigning = None
						self.select(pos)
					# Don't let things target themselves.
					elif target == self.selected:
						SFX_ERROR.play()
					# Valid targets.
					elif self.gamestate.in_range(self.selected, self.selected.weapons[self.assigning].type, target) or override():
						self.selected.target(self.assigning, target.pos) # TODO this is the only one that modifies the Gamestate from inside client_display. I should look for a workaround.
						self.assigning += 1
						if self.assigning == len(self.selected.weapons): self.assigning = 0
						return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps(self.selected.actions)]
					# If the target is valid, but not reachable.
					else:
						SFX_ERROR.play()
				# Launching a ship from a Hangar.
				elif type(self.assigning) == dict:
					# Find the index of the ship in the Hangar's contents.
					index = self.selected.contents.index(self.assigning['ship'])
					# Make sure the launch is legal.
					if not self.gamestate.hangar_launch(self.selected, index, self.assigning['pos'], self.assigning['rot'], test=True) and not override():
							SFX_ERROR.play()
							return []
					# Form the return string ahead of time, since we have some things we need to do inbetween that and returning.
					string = "ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([{'type': 'launch', 'index': index, 'pos': self.assigning['pos'], 'rot': self.assigning['rot']}])
					self.clear_projected_placement(flip=True)
					self.assigning = None
					return [string]
				# Factory Hangar assignments.
				elif type(self.assigning) == str:
					entity = self.gamestate.occupied(pos)
					if entity and entity.type == "Hangar":
						# Form the return string ahead of time, since we have some things we need to do inbetween that and returning.
						string = "ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([{'type': 'build', 'ship': self.assigning, 'hangar': entity.pos}])
						self.assigning = None
						self.details_view = False
						return [string]
					else:
						SFX_ERROR.play()

			# Panel click events.
			else:
				# Done button.
				if self.done_button.handle_mousebuttondown(event): return ["DONE"]
				# Whatever other buttons are around.
				for button in self.panel_buttons:
					callback = button.handle_mousebuttondown(event)
					if callback:
						# Hangar launch buttons.
						if isinstance(callback, Entity):
							self.assigning = {'ship': callback, 'pos': callback.pos, 'shape': callback.shape, 'rot': callback.rot}
							self.project_placement(flip=True)
						# Factory assignment buttons.
						elif isinstance(callback, str):
							# Still need to select a Hangar, so we store the selected ship name in a variable that will persist.
							self.assigning = callback

		# Keypresses.
		elif event.type == pygame.KEYDOWN:
			# If the chatbar is active, just pass it the input and don't bother with gamestate commands.
			if self.chatbar.entry_box.active:
				entry = self.chatbar.handle_event(event)
				self.lock.acquire()
				pygame.display.update(self.chatbar.rect)
				self.lock.release()
				if entry: return ["LOCAL:" + self.player_name + ":" + entry]

			# Open the card menu.
			elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
				self.show_hand()

			# Cycle hands / weapons.
			elif event.key == pygame.K_TAB:
				if self.hand:
					self.cycle_hand()
				elif self.assigning is not None:
					self.assigning += 1
					if self.assigning == len(self.selected.weapons): self.assigning = 0

			# Everything else depends on something being selected, so instead of adding the condition everywhere, I just put a return here.
			elif not self.selected: return []

			# Targeting mode.
			elif event.key == pygame.K_SPACE and not self.animating():
				# Don't handle it if already in assigning mode; or else it will keep resetting.
				if type(self.assigning) == int: return []
				# The players can't assign targets to non-allied units, or to units that don't have any weapons.
				if self.selected.team != 'player' or not self.selected.weapons:
					SFX_ERROR.play()
					return []
				self.assigning = 0
				self.select()

			# Z clears a unit's actions.
			elif event.key == pygame.K_z and not self.animating():
				if self.selected.weapons and type(self.assigning) == int:
					self.assigning = 0
				self.clear_projected_move(flip=True)
				return ["ASSIGN:" + json.dumps(self.selected.pos) + ":[]"]

			# Esc gets out of assignment or placement mode.
			elif event.key == pygame.K_ESCAPE and not self.animating():
				self.assigning = None
				self.select()

			# Q, W, E and R are the unique action keys.
			elif event.key == pygame.K_q:
				# Shield Generators hide shields.
				if self.selected.type == "Shield Generator":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([{'type': 'hide'}])]
				# Hangar/Factory details page.
				elif self.selected.type == "Hangar":
					self.details_view = True
					self.select()
				elif self.selected.type == "Factory":
					self.details_view = True
					self.select()
				# Engines boost counterclockwise.
				elif self.selected.type == "Engine":
					# We need to make sure all Engines are boosting the same direction.
					cmds = []
					for comp in self.gamestate.station:
						if comp.type == "Engine" and (comp.powered() or comp == self.selected):
							cmds.append("ASSIGN:" + json.dumps(comp.pos) + ":" + json.dumps([{'type': 'boost', 'dir': -1}]))
					return cmds
				else: SFX_ERROR.play()
			elif event.key == pygame.K_w:
				# Normal Hangar/Factory panel page.
				if self.selected.type == "Hangar":
					self.details_view = False
					self.select()
				elif self.selected.type == "Factory":
					self.details_view = False
					self.select()
				# Engines boost clockwise.
				elif self.selected.type == "Engine":
					# We need to make sure all Engines are boosting the same direction.
					cmds = []
					for comp in self.gamestate.station:
						if comp.type == "Engine" and (comp.powered() or comp == self.selected):
							cmds.append("ASSIGN:" + json.dumps(comp.pos) + ":" + json.dumps([{'type': 'boost', 'dir': 1}]))
					return cmds
				else: SFX_ERROR.play()
			elif event.key == pygame.K_e:
				# Turn off the Component to save power.
				if self.selected.type == "Shield Generator":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([{'type': 'off'}])]
				elif self.selected.type == "Factory":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([{'type': 'off'}])]
				else: SFX_ERROR.play()
			elif event.key == pygame.K_r:
				# To turn the shield generator or Factory back on, we can just clear its actions.
				if self.selected.type == "Shield Generator":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([])]
				elif self.selected.type == "Factory":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([])]
				# Hangars and Engines cancel their launch/thrust.
				elif self.selected.type == "Hangar":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([])]
				elif self.selected.type == "Engine":
					return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps([])]
				else: SFX_ERROR.play()


			# Movement keys.
			elif self.selected.moves_left() and not self.animating():
				if event.key == pygame.K_UP: move = [0, -1]
				elif event.key == pygame.K_DOWN: move = [0, 1]
				elif event.key == pygame.K_LEFT: move = [-1, 0]
				elif event.key == pygame.K_RIGHT: move = [1, 0]
				else: return []
				obstacle = self.gamestate.invalid_move(self.selected, move)
				if obstacle and obstacle.type != "Hangar":
					SFX_ERROR.play()
					return []
				# We have to call this here because if we wait for the command to come back in, we won't know what the move to clear was.
				#self.clear_projected_move(flip=True)
				return ["ASSIGN:" + json.dumps(self.selected.pos) + ":" + json.dumps(self.selected.actions + [{'type': 'move', 'move': move}])]

		elif event.type == pygame.KEYUP:
			# Make sure this doesn't trigger on units that don't have weapons.
			if event.key == pygame.K_SPACE and type(self.assigning) == int:
				self.assigning = None
				self.select()

		# Closing the game. We handle this last because it's the rarest.
		elif event.type == pygame.QUIT: sys.exit()

	def add_chat(self, msg):
		"""Add a message to the chat bar and automatically update the display."""
		self.chatbar.add_message(msg)
		self.lock.acquire()
		pygame.display.update(self.chatbar.rect)
		self.lock.release()

	def calc_pos(self, pos):
		"""calc_pos converts a gameboard logical position to a pixel position on screen."""
		return ((pos[0] + self.offset[0]) * TILESIZE[0] + GAME_WINDOW_RECT.left, (pos[1] + self.offset[1]) * TILESIZE[1])

	def reverse_calc_pos(self, pos):
		"""reverse_calc_pos converts a pixel position on screen to a gameboard logical position."""
		return [int(pos[0] - GAME_WINDOW_RECT.left) // TILESIZE[0] - self.offset[0], pos[1] // TILESIZE[1] - self.offset[1]]

	def calc_rect(self, rect):
		"""calc_rect converts a gameboard logical rect to a pixel rect on screen."""
		return pygame.Rect(self.calc_pos((rect[0], rect[1])), (rect[2] * TILESIZE[0], rect[3] * TILESIZE[1]))

	def reverse_calc_rect(self, rect):
		"""reverse_calc_rect converts a pixel rect on screen to a gameboard logical rect."""
		return pygame.Rect(self.reverse_calc_pos((rect[0], rect[1])), (rect[2] // TILESIZE[0], rect[3] // TILESIZE[1]))

	def entity_pixel_rect(self, entity):
		"""Finds the rectangle that an Entity is occupying (in terms of pixels)."""
		rect = entity.rect()
		return pygame.Rect(self.calc_pos(rect[0:2]), (rect[2] * TILESIZE[0], rect[3] * TILESIZE[1]))

	def select(self, pos=None):
		"""Selects a gameboard space by logical position (or the space of the selected Entity if no pos is passed) and calls other functions to fill the UI with information."""
		if self.selected:
			self.clear_projected_placement()
			self.clear_projected_move()
		# Signal other code that we're not showing a hand.
		self.hand = None
		if pos:
			new_selected = self.gamestate.occupied(list(pos))
			# Switch back to normal view iff we're selected away from something else.
			if new_selected != self.selected: self.details_view = False
			self.selected = new_selected
		if self.selected:
			pos = self.selected.pos
			# Regenerate artifacts.
			self.project_move()
			self.project_placement()
		# If we're clearing self.selected, we should get out of assigning mode too.
		else: self.assigning = None
		# Now find the Salvage.
		# FIXME This is an imperfect method, as it makes it impossible to see salvage that's under a big ship but not under its central pos.
		salvage = None
		for s in self.gamestate.salvages:
			if s.pos == pos: salvage = s
		if not self.details_view:
			self.fill_panel(salvage)
		else:
			if self.selected.type == "Hangar": self.fill_panel_hangar()
			elif self.selected.type == "Factory": self.fill_panel_factory()
		self.lock.acquire()
		pygame.display.flip()
		self.lock.release()

	def deselect(self):
		"""Clears the panel and all Display artifacts."""
		self.selected = None
		self.assigning = None
		self.fill_panel()
		self.clear_projected_move()
		self.clear_projected_placement()
		self.lock.acquire()
		pygame.display.flip()
		self.lock.release()

	def project_move(self, flip=False):
		"""Shows a yellow path from the selected Entity projecting the moves it's going to make."""
		moves = self.selected.moves_planned()
		if not moves:
			# Don't waste time.
			return
		pos = (self.selected.pos[0] + self.offset[0], self.selected.pos[1] + self.offset[1])
		for move in self.selected.moves_planned():
			pos = (pos[0] + move[0], pos[1] + move[1])
			pygame.draw.rect(self.window, MOVE_PROJECTION_COLOR, (GAME_WINDOW_RECT.left + TILESIZE[0] * pos[0], GAME_WINDOW_RECT.top + TILESIZE[1] * pos[1], TILESIZE[0], TILESIZE[1]), 2)
		if flip:
			self.lock.acquire()
			pygame.display.update(self.calc_rect(self.selected.move_rect()).inflate(2, 2))
			self.lock.release()

	def clear_projected_move(self, flip=False):
		"""Clears the yellow projected path from a selected Entity."""
		# Make this check internally so it's always safe to call this.
		if not self.selected: return
		# It seems like rounding requires a +2, +2 expansion.
		rect = self.calc_rect(self.selected.move_rect()).inflate(2, 2)
		self.window.fill((0,0,0), rect)
		# Redraw the other gamestate entities clobbered when we erased.
		self.draw_gamestate(rect, flip=flip)

	def project_placement(self, flip=False):
		"""Shows an outline of where the object will be during placement."""
		# Make this check internally so it's safe to call this function when it isn't applicable.
		if type(self.assigning) != dict: return
		placement_spaces = spaces(self.assigning['pos'], self.assigning['shape'], self.assigning['rot'])
		for space in placement_spaces:
			pygame.draw.rect(self.window, PLACEMENT_PROJECTION_COLOR, (*self.calc_pos(space), TILESIZE[0], TILESIZE[1]), 2)
		if flip:
			self.lock.acquire()
			pygame.display.update(self.calc_rect(rect(placement_spaces)).inflate(2, 2))
			self.lock.release()

	def clear_projected_placement(self, flip=False):
		"""Clears the outline of where the object will be during placement."""
		# Make this check internally so it's safe to call this function when it isn't applicable.
		if type(self.assigning) != dict: return
		p_rect = self.calc_rect(rect(spaces(self.assigning['pos'], self.assigning['shape'], self.assigning['rot'])))
		self.window.fill((0,0,0), p_rect)
		if flip:
			# Redraw the other gamestate entities clobbered when we erased.
			self.draw_gamestate(p_rect.inflate(2, 2))

	def fill_panel(self, salvage=None):
		"""fills the panel with information about the given object."""
		# First, clear it.
		pygame.draw.rect(self.window, PANEL_COLOR, PANEL_RECT, 0)
		# Right now, the only thing that puts buttons on the panel when selected is Hangars in details mode. But that's handled by fill_panel_hangar.
		self.panel_buttons = []
		# Draw info of whatever salvage is here first, so that it still gets drawn if there's no object.
		if salvage: draw_text(self.window, str(salvage), TEXT_COLOR, PANEL_SALVAGE_RECT, FONT)
		# This catch is here so we can call fill_panel() with nothing selected to blank it.
		if not self.selected: return
		draw_text(self.window, self.selected.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
		if self.assigning is not None: draw_text(self.window, "Assigning...", ASSIGNING_TEXT_COLOR, PANEL_ASSIGNING_RECT, FONT)
		# Hull and shield.
		draw_text(self.window, str(self.selected.hull) + "/" + str(self.selected.maxhull), TEXT_COLOR, PANEL_HULL_RECT, FONT)
		draw_bar(self.window, PANEL_HULL_BAR_RECT, TEXT_COLOR, HULL_COLOR, HULL_DAMAGE_COLOR, self.selected.maxhull, self.selected.hull)
		if self.selected.maxshield > 0:
			draw_text(self.window, shield_repr(self.selected), TEXT_COLOR, PANEL_SHIELD_RECT, FONT)
			draw_bar(self.window, PANEL_SHIELD_BAR_RECT, TEXT_COLOR, SHIELD_COLOR, SHIELD_DAMAGE_COLOR, self.selected.maxshield, self.selected.shield)
		draw_text(self.window, "Speed: " + str(self.selected.speed), TEXT_COLOR, PANEL_SPEED_RECT, FONT)
		y = 0
		if self.selected.weapons:
			draw_text(self.window, "Weapons:", TEXT_COLOR, PANEL_WEAPON_DESC_BEGIN, FONT)
			y += LABEL_HEIGHT + LABEL_SPACING
			for weapon in self.selected.weapons:
				y += draw_text(self.window, str(weapon)+self.selected.desc_target(weapon,self.gamestate), TEXT_COLOR, pygame.Rect(PANEL_WEAPON_DESC_BEGIN.x+5, PANEL_WEAPON_DESC_BEGIN.y+y, PANEL_WEAPON_DESC_BEGIN.w-7, 60), FONT)
		# Now draw special properties.
		if self.selected.type == "Probe":
			rect = PANEL_SPEED_RECT.move(0, y + 30)
			draw_text(self.window, "Salvage: " + str(self.selected.load) + "/" + str(PROBE_CAPACITY), TEXT_COLOR, rect, FONT)
			rect.h = BAR_HEIGHT
			draw_bar(self.window, rect.move(0, LABEL_HEIGHT + LABEL_SPACING), TEXT_COLOR, CAPACITY_COLOR, CAPACITY_EMPTY_COLOR, PROBE_CAPACITY, self.selected.load)
		# Station components also display the pooled power.
		if self.selected in self.gamestate.station:
			draw_text(self.window, power_repr(self.gamestate.station), TEXT_COLOR, PANEL_POWER_RECT, FONT)
			draw_bar(self.window, PANEL_POWER_BAR_RECT, TEXT_COLOR, POWER_COLOR, POWER_LOW_COLOR, self.gamestate.station.maxpower(), self.gamestate.station.power)
			draw_text(self.window, str(self.gamestate.station.salvage) + "/" + str(self.gamestate.station.max_salvage()), TEXT_COLOR, PANEL_STATION_SALVAGE_RECT, FONT)
			draw_bar(self.window, PANEL_SALVAGE_BAR_RECT, TEXT_COLOR, SALVAGE_COLOR, SALVAGE_EMPTY_COLOR, self.gamestate.station.max_salvage(), self.gamestate.station.salvage)
			draw_text(self.window, thrust_repr(self.gamestate.station), TEXT_COLOR, PANEL_THRUST_RECT, FONT)
			draw_bar(self.window, PANEL_THRUST_BAR_RECT, TEXT_COLOR, THRUST_COLOR, THRUST_EMPTY_COLOR, self.gamestate.station.thrust_needed(), abs(self.gamestate.station.thrust))
			# Hangars show a summary of their contents when selected.
			if self.selected.type == "Hangar":
				rect = PANEL_SPEED_RECT.move(0, y + 30)
				# We have to adjust the size because the speed rect is sized for a line of text, not a bar.
				rect.h = BAR_HEIGHT
				draw_text(self.window, "Capacity: " + str(self.selected.current_fill()) + "/" + str(HANGAR_CAPACITY), TEXT_COLOR, rect, FONT)
				rect.move_ip(0, LABEL_HEIGHT + LABEL_SPACING)
				draw_bar(self.window, rect, TEXT_COLOR, CAPACITY_COLOR, CAPACITY_EMPTY_COLOR, HANGAR_CAPACITY, self.selected.current_fill())
				rect.inflate_ip(0, 100)
				# Give it more space, since we're starting from the shield bar rect and this might need to be several lines long.
				# And we give it 50 extra pixels because inflate_ip expands in both directions, so it moved up by 50.
				rect.move_ip(0, 80)
				draw_text(self.window, "Contains: " + self.selected.summarize_contents(), TEXT_COLOR, rect, FONT)
			# Factories show their current project and progress.
			elif self.selected.type == "Factory":
				# Determining the current project is a little more complicated for Factories. It might not be in the .project attribute.
				# If the players have set a project for it to take on but it hasn't happened yet, then we need to find in .actions.
				if self.selected.actions and self.selected.actions[0]['type'] == "build":
					project = self.selected.actions[0]['ship']
				else:
					project = self.selected.project
				if project:
					rect = PANEL_SPEED_RECT.move(0, y + 30)
					draw_text(self.window, "Building " + project + ", " + str(self.selected.progress) + "/" + str(SHIP_CONSTRUCTION_COSTS[project]), TEXT_COLOR, rect, FONT)
					rect.move_ip(0, LABEL_HEIGHT + LABEL_SPACING)
					rect.h = BAR_HEIGHT
					draw_bar(self.window, rect, TEXT_COLOR, CONSTRUCTION_COLOR, CONSTRUCTION_EMPTY_COLOR, SHIP_CONSTRUCTION_COSTS[project], self.selected.progress)

	def fill_panel_hangar(self):
		"""An alternative to fill_panel called on a Hangar to show the details of its contents."""
		# First, clear it.
		pygame.draw.rect(self.window, PANEL_COLOR, PANEL_RECT, 0)
		# And I guess still bother saying it's a Hangar.
		draw_text(self.window, self.selected.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
		# Prepare to return a list of Buttons. We need them to persist after the panel is drawn so play() can use them.
		self.panel_buttons = []
		# Give them more space, and move it back down to compensate.
		y = 50
		rect = PANEL_NAME_RECT.inflate(0, 40).move(0, 20 + y)
		for i, ship in enumerate(self.selected.contents):
			text = ship.hangar_describe()
			# Subtracting 2 from the width because it also needs to fit inside the Button.
			h = get_height(text, rect.w-2, FONT)
			# Check whether the current button is for a ship scheduled to launch. If so, the button should be different colors.
			if self.selected.actions and self.selected.actions[0].get('index') == i:
				button = Button(self.window, pygame.Rect(rect.x, rect.y, rect.w, h+2), ACTIVE_LAUNCH_HANGAR_BUTTON_COLOR, INACTIVE_LAUNCH_HANGAR_BUTTON_COLOR, TEXT_COLOR, FONT, text, ship)
			else:
				button = Button(self.window, pygame.Rect(rect.x, rect.y, rect.w, h+2), ACTIVE_HANGAR_BUTTON_COLOR, INACTIVE_HANGAR_BUTTON_COLOR, TEXT_COLOR, FONT, text, ship)
			button.draw()
			self.panel_buttons.append(button)
			rect.move_ip(0, h+5)

	def fill_panel_factory(self):
		"""An alternative to fill_panel called on a Factory to show the production menu."""
		# First, clear it.
		pygame.draw.rect(self.window, PANEL_COLOR, PANEL_RECT, 0)
		# And I guess still bother saying it's a Factory.
		draw_text(self.window, self.selected.type, TEXT_COLOR, PANEL_NAME_RECT, FONT)
		# Prepare to return a list of Buttons. We need them to persist after the panel is drawn so play() can use them.
		self.panel_buttons = []
		# Give them more space, and move it back down to compensate.
		y = 50
		rect = PANEL_NAME_RECT.inflate(0, 40).move(0, 20 + y)
		for ship in SHIP_CONSTRUCTION_COSTS:
			text = SHIP_DESCRIPTIONS[ship]
			# Subtracting 2 from the width because it also needs to fit inside the Button.
			h = get_height(text, rect.w - 2, FONT)
			# Check whether the current button is for a ship scheduled to launch. If so, the button should be different colors.
			button = Button(self.window, pygame.Rect(rect.x, rect.y, rect.w, h+2), ACTIVE_FACTORY_PROJECT_BUTTON_COLOR, INACTIVE_FACTORY_PROJECT_BUTTON_COLOR, TEXT_COLOR, FONT, text, ship)
			button.draw()
			self.panel_buttons.append(button)
			rect.move_ip(0, h+5)

	def show_hand(self):
		"""Fill the panel with info about a hand of cards."""
		self.selected = None
		self.assigning = None
		if not self.hand: self.hand = self.player_name
		# First, clear it.
		pygame.draw.rect(self.window, PANEL_COLOR, PANEL_RECT, 0)
		# Say whose hand it is.
		draw_text(self.window, self.hand + "'s hand", TEXT_COLOR, PANEL_NAME_RECT, FONT)
		# Find the actual hand.
		for player in self.gamestate.players:
			if player.name == self.hand: break
		self.panel_buttons = []
		rect = CARD_BEGIN_RECT.copy()
		for card in player.hand:
			text = card.name.upper() + "\n" + CARD_DESCRIPTIONS[card.name]
			# Subtracting 2 from the width because it also needs to fit inside the Button.
			h = get_height(text, rect.w - 2, FONT)
			# Check whether the current button is for a ship scheduled to launch. If so, the button should be different colors.
			button = Button(self.window, pygame.Rect(rect.x, rect.y, rect.w, h+2), ACTIVE_CARD_BUTTON_COLOR, INACTIVE_CARD_BUTTON_COLOR, TEXT_COLOR, FONT, text, card.name)
			button.draw()
			self.panel_buttons.append(button)
			rect.move_ip(0, h + 5)

		self.lock.acquire()
		pygame.display.update(PANEL_RECT)
		self.lock.release()

	def cycle_hand(self):
		"""A wrapper around show_hand that shows the next player's hand."""
		for i, player in enumerate(self.gamestate.players):
			if player.name == self.hand:
				i += 1
				if i >= len(self.gamestate.players): i = 0
				self.hand = self.gamestate.players[i].name
				return self.show_hand()

	def erase(self, rect):
		"""Takes a pixel rect and erases only the gameboard entities on it (by redrawing the grid.)"""
		self.window.fill((0,0,0), rect)
		self.draw_grid(rect)

	def draw_grid(self, rect=None):
		"""Draw the game window grid within the specified Rect. The Rect should be measured in pixel position."""
		if rect:
			# Account for the offset being in the wrong direction.
			rect.inflate_ip((TILESIZE[0], TILESIZE[1]))
			rect.move_ip((TILESIZE[0] // 2, TILESIZE[1] // 2))
			# Make sure the lines aren't misaligned.
			xoffset = (rect.x - GAME_WINDOW_RECT.x) % TILESIZE[0]
			yoffset = (rect.y - GAME_WINDOW_RECT.y) % TILESIZE[1]
		else:
			rect = GAME_WINDOW_RECT
			xoffset = yoffset = 0
		for x in range(rect.left, rect.right, TILESIZE[0]):
			pygame.draw.line(self.window, GRID_COLOR, (x - xoffset, rect.top), (x - xoffset, rect.bottom), 1)
		for y in range(rect.top, rect.bottom, TILESIZE[1]):
			pygame.draw.line(self.window, GRID_COLOR, (rect.left, y - yoffset), (rect.right, y - yoffset), 1)

	def draw_gamestate(self, rect=None, exclude=None, flip=True):
		"""Draw the game window within the specified Rect."""
		self.draw_grid(rect)
		if not rect: rect = GAME_WINDOW_RECT
		for salvage in self.gamestate.salvages:
			if rect.colliderect(self.entity_pixel_rect(salvage)) and exclude != salvage:
				self.window.blit(IMAGE_DICT['salvage'], self.calc_pos(salvage.pos))
		for entity in self.gamestate.station:
			if rect.colliderect(self.entity_pixel_rect(entity)) and exclude != entity:
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.ships:
			if rect.colliderect(self.entity_pixel_rect(entity)) and exclude != entity:
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.asteroids:
			if rect.colliderect(self.entity_pixel_rect(entity)) and exclude != entity:
				self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		if flip:
			self.lock.acquire()
			# I've heard that calling update on the entire window is slower than flip at least on some hardawre.
			if rect: pygame.display.update(rect)
			else: pygame.display.flip()
			self.lock.release()

	def full_redraw(self):
		"""Blank and redraw the entire game window."""
		self.window.fill((0,0,0), GAME_WINDOW_RECT)
		self.draw_gamestate(flip=False)
		if self.selected: self.select()
		pygame.display.flip()

	def move(self, entity, move):
		"""Starts an animation thread to move a unit."""
		self.anim = threading.Thread(target=self.animate_move, name="move animation", args=(entity, move))
		self.anim.start()

	def animate_move(self, entity, move):
		"""The function that the movemnet animation thread runs. This should never be called from the outside. Instead, call move."""
		# Precalculate the rect we'll need to erase.
		# TODO This probably only works with one-space ships.
		move_rect = self.calc_rect(rect((entity.pos, (entity.pos[0] + move[0], entity.pos[1] + move[1]))))
		# And extract the background image so we don't have to recalculate that either.
		# To exclude the moving ship's image from this, we'll have to draw things without it.
		self.window.fill((0,0,0), move_rect)
		self.draw_gamestate(move_rect, exclude=entity, flip=False)
		bg = self.window.subsurface(move_rect).copy()
		orig_pos = [move_rect[0], move_rect[1]]
		pos = list(self.calc_pos(entity.pos))
		dest = list(self.calc_pos((entity.pos[0] + move[0], entity.pos[1] + move[1])))
		while pos != dest:
			# Moves should always be just one space at a time, so they can only be one direction.
			if move[0]: pos[0] += move[0]
			else: pos[1] += move[1]
			# This is run concurrently, so it's important to lock the display.
			self.lock.acquire()
			self.window.blit(bg, orig_pos)
			self.window.blit(IMAGE_DICT[entity.type], pos)
			pygame.display.update(move_rect)
			self.lock.release()
			pygame.time.wait(10)

	def animating(self):
		"""Returns whether the Display is currently running an animation thread."""
		if self.anim and self.anim.is_alive(): return True
		return False



def override() -> bool:
	"""Returns whether an override key is pressed."""
	pressed = pygame.key.get_pressed()
	if pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]: return True
	return False
