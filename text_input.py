# Originally created by: skrx, from Stack Overflow


# Add cursor display
# Add more control character handling

import pygame

class InputBox:
	def __init__(self, window, rect, bgcolor, textcolor, active_color, inactive_color, font, text=''):
		self.window = window
		self.rect = rect
		self.bgcolor = bgcolor
		self.textcolor = textcolor
		self.active_color = active_color
		self.inactive_color = inactive_color
		self.text = text
		self.font = font
		self.text_surface = font.render(text, True, self.textcolor)
		self.active = False
		self.erase_needed = False

	def rectcolor(self):
		if self.active: return self.active_color
		return self.inactive_color

	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN:
			if self.rect.collidepoint(event.pos):
				self.active = True
			else:
				self.active = False
			self.color = self.active_color if self.active else self.rectcolor()
		elif event.type == pygame.KEYDOWN:
			if self.active:
				if event.key == pygame.K_RETURN:
					returntext = self.text
					self.erase_needed = True
					self.text = ''
				elif event.key == pygame.K_BACKSPACE:
					self.text = self.text[:-1]
					self.erase_needed = True
				else:
					self.text += event.unicode
				self.text_surface = self.font.render(self.text, True, self.textcolor)
				if event.key == pygame.K_RETURN:
					return returntext

	def update(self):
		# Resize the box if the text is too long.
		width = max(200, self.text_surface.get_width()+10)
		self.rect.w = width

	def draw(self):
		if self.erase_needed: pygame.draw.rect(self.window, self.bgcolor, self.rect, 0)
		# Blit the text.
		self.window.blit(self.text_surface, (self.rect.x+2, self.rect.y+2))
		# Draw the rect.
		pygame.draw.rect(self.window, self.rectcolor(), self.rect, 1)
