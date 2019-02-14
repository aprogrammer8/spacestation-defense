# A client-side module that handles the display during game.

import pygame, sys
from pygame_elements import *
from client_config import *
from gamestate import *

class GameDisplay:
	def __init__(self, window, player_name, gamestate):
		self.window = window
		grid_size = [GAME_WINDOW_RECT.w//TILESIZE[0], GAME_WINDOW_RECT.h//TILESIZE[1]]
		self.offset = [grid_size[0]//2, grid_size[1]//2]
		self.player_name = player_name
		self.gamestate = gamestate
		self.draw_gamestate()
		self.playerlist = TextList(window, GAME_PLAYERLIST_RECT, PANEL_COLOR, PANEL_COLOR, TEXT_COLOR, FONT, (player.name for player in gamestate.players))
		done_button = Button(window, DONE_BUTTON_RECT, ACTIVE_DONE_BUTTON_COLOR, INACTIVE_DONE_BUTTON_COLOR, TEXT_COLOR, FONT, "Done")
		done_button.draw()
		self.buttons = [done_button]
		#self.chatbar = chatbar
		self.chatbar = Chat(window, CHAT_RECT, CHAT_ENTRY_HEIGHT, BGCOLOR, CHAT_BORDERCOLOR, TEXT_COLOR, ACTIVE_INPUTBOX_COLOR, INACTIVE_INPUTBOX_COLOR, FONT, player_name)
		# Blank the panel to begin.
		pygame.draw.rect(window, PANEL_COLOR, TOP_PANEL_RECT, 0)
		pygame.draw.rect(window, PANEL_COLOR, PANEL_RECT, 0)
		# Update display.
		pygame.display.flip()

	def event_respond(self, event):
		"""The basic method for receiving an event from pygame and reacting to it."""
		# In the case of mousemotion, all we need to do is check all the buttons to see if they need to be redrawn.
		# For now, mousemotion outside of the panel doesn't do anything.
		if event.type == pygame.MOUSEMOTION and TOTAL_PANEL_RECT.collidepoint(event.pos):
			rects_to_update = []
			for button in self.buttons:
				if button.handle_mousemotion(event):
					rects_to_update.append(button.rect)
			pygame.display.update(rects_to_update)
		# Clicks are a little more complicated. We have to handle the callbacks of any buttons clicked, and account for clicks on the rest of the screen.
		if event.type == pygame.MOUSEBUTTONDOWN:
			if self.chatbar.entry_box: self.chatbar.handle_mousebuttondown(event)
			for button in self.buttons:
				callback = button.handle_mousebuttondown(event)
				if callback:
					# Now we get into the long process of handling the possible callbacks of all buttons.
					# Done button.
					if callback == "done": return "BUTTON", callback
					# TEMP
					print(callback)
		# Keypresses.
		elif event.type == pygame.KEYDOWN:
			# If the chatbar is active, just pass it the input and don't bother with gamestate commands.
			if self.chatbar.entry_box.active:
				entry = self.chatbar.handle_event(event)
				pygame.display.update(chatbar.rect)
				if entry: return "CHAT", "LOCAL:" + player_name + ":" + entry

		# Closing the game. We handle this last because it's the rarest.
		elif event.type == pygame.QUIT: sys.exit()

	def msg_respond(self, msg):
		"""The method for responding to a message from the server."""
		pass

	def calc_pos(self, pos):
		"""calc_pos converts a gameboard logical position to a pixel position on screen."""
		return ((pos[0]+self.offset[0])*TILESIZE[0]+GAME_WINDOW_RECT.left, (pos[1]+self.offset[1])*TILESIZE[1])

	def reverse_calc_pos(self, pos):
		"""reverse_calc_pos converts a pixel position on screen to a gameboard logical position."""
		return [int(pos[0]-GAME_WINDOW_RECT.left)//TILESIZE[0]-self.offset[0], pos[1]//TILESIZE[1]-self.offset[1]]

	def draw_grid(self, rect=None):
		"""Draw the game window grid."""
		if not rect: rect = pygame.Rect(GAME_WINDOW_RECT.left, GAME_WINDOW_RECT.top, GAME_WINDOW_RECT.w, GAME_WINDOW_RECT.h)
		for x in range(rect.left, rect.right, TILESIZE[0]):
			pygame.draw.line(self.window, GRID_COLOR, (x, rect.top), (x, rect.bottom), 1)
		for y in range(rect.top, rect.bottom, TILESIZE[1]):
			pygame.draw.line(self.window, GRID_COLOR, (rect.left, y), (rect.right, y), 1)

	def draw_gamestate(self, rect=None):
		"""The offset is where the player is scrolled to. The rect is which area of the gameboard should be updated. It's measured in logical position, not pixel position."""
		self.draw_grid(rect)
		for pos in self.gamestate.salvages:
			self.window.blit(IMAGE_DICT['salvage'], self.calc_pos(pos))
		for entity in self.gamestate.station:
			self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.enemy_ships:
			self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.allied_ships:
			self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))
		for entity in self.gamestate.asteroids:
			self.window.blit(IMAGE_DICT[entity.type], self.calc_pos(entity.pos))

