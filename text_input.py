# Originally created by: skrx, from Stack Overflow

# TODO: Add more control character handling
# TODO: Add cursor display

import pygame, text_wrap

class InputBox:
	def __init__(self, window, rect, bgcolor, textcolor, active_color, inactive_color, font, text=''):
		self.window = window
		self.rect = rect
		self.textrect = (rect.x+1, rect.y+1, rect.w-2, rect.h-2)
		self.bgcolor = bgcolor
		self.textcolor = textcolor
		self.active_color = active_color
		self.inactive_color = inactive_color
		self.text = text
		self.font = font
		self.active = False
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
			self.draw()
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
				self.draw()
				if event.key == pygame.K_RETURN:
					return returntext
	def draw(self):
		# Clear the area. Without this, the text gets blurred more and more with each re-blitting. I have no idea why.
		pygame.draw.rect(self.window, self.bgcolor, self.textrect, 0)
		# Draw the text.
		text_wrap.draw_text(self.window, self.text, self.textcolor, self.textrect, self.font)
		# Draw the border.
		pygame.draw.rect(self.window, self.rectcolor(), self.rect, 1)
