import pygame
import text_input, text_wrap

# A list of separate text items to be displayed on a pygame window, inside a specified area and with items separated.
class TextList:
	def __init__(self, window, rect, bgcolor, bordercolor, textcolor, font):
		self.window = window
		self.rect = rect
		self.bgcolor = bgcolor
		self.bordercolor = bordercolor
		self.textcolor = textcolor
		self.font = font
		self.stage_surface = font.render("", True, self.textcolor)
		self.erase_needed = False
		self.message_list = []
		self.new_height = 0 # The y that a new message will start at
	def add_message(self, message):
		self.message_list += [message]
		height = text_wrap.get_height(message, self.rect.w, 2, self.font)
		# TODO: flush old messages if the total height gets too big
		#fits = False
		#while not fits:
		#	
		#self.(, self.textcolor, self.font)
		self.new_height += height + 1
		#text_wrap.draw_text(self.window, message, self.textcolor, pygame.Rect(self.rect.x, self.rect.y+self.new_height, self.rect.w, height), self.font)
		# Add an extra 1 space between messages.
		self.draw()
	def draw(self):
		pygame.draw.rect(self.window, self.bgcolor, self.rect, 0)
		pygame.draw.rect(self.window, self.bordercolor, self.rect, 1)
		self.new_height = 0
		for message in self.message_list:
			height = text_wrap.draw_text(self.window, message, self.textcolor, pygame.Rect(self.rect.x, self.rect.y+self.new_height, self.rect.w, self.rect.h), self.font)
			self.new_height += height + 1


# A chat element, consisting of a TextList and an InputBox.
class Chat:
	def __init__(self, window, rect, entryheight, bgcolor, bordercolor, textcolor, active_color, inactive_color, font, username):
		self.window = window
		self.rect = rect
		self.bgcolor = bgcolor
		self.bordercolor = bordercolor
		self.textcolor = textcolor
		self.font = font
		self.username = username
		#self.chat_stage_surface = font.render("", True, self.textcolor)
		#self.entry_stage_surface = font.render("", True, self.textcolor)
		self.erase_needed = False
		log_rect = pygame.Rect(rect.x, rect.y, rect.w, rect.h-entryheight+1) # This +1 makes the borders overlap, so it doesn't look ugly
		self.log = TextList(window, log_rect, bgcolor, bordercolor, textcolor, font)
		entry_rect = pygame.Rect(rect.x, rect.bottom-entryheight, rect.w, entryheight)
		self.entry_box = text_input.InputBox(window, entry_rect, bgcolor, textcolor, active_color, inactive_color, font)
	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN:
			if self.entry_box.rect.collidepoint(event.pos):
				self.entry_box.handle_event(event)
		if event.type == pygame.KEYDOWN:
			entry = self.entry_box.handle_event(event)
			if entry: self.log.add_message(self.username+": "+entry)
	def add_message(self, message):
		self.log.add_message(message)
	def draw(self):
		self.log.draw()
		self.entry_box.draw()
#		pygame.draw.rect(self.window, self.bgcolor, self.rect, 0)
#		pygame.draw.rect(self.window, self.bordercolor, self.rect, 1)
#		self.entry_box.draw()
#		self.new_height = 0
#		for message in self.message_list:
#			height = text_wrap.draw_text(self.window, message, self.textcolor, pygame.Rect(self.rect.x, self.rect.y+self.new_height, self.rect.w, self.rect.h), self.font)
#			self.new_height += height + 1
