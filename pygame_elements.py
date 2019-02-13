import pygame

# draw_text wraps text as necessary to fit within the given area, and then draws it.
def draw_text(window, text, color, rect, font, spacing=2, aa=True, bgcolor=None):
	rect = pygame.Rect(rect)
	y = rect.top
	font_height = font.size("Tg")[1]
	while text:
		i = 1
		# Cut if the row of text will be outside our area.
		if y + font_height > rect.bottom:
			break
		# Determine maximum width of line.
		while font.size(text[:i])[0] < rect.w and i < len(text):
			i += 1
		# If we've wrapped the text, then adjust the wrap to the last word.
		if i < len(text):
			i = text.rfind(" ", 0, i) + 1
		# Render the line and blit it to the window.
		if bgcolor:
			image = font.render(text[:i], 1, color, bgcolor)
			image.set_colorkey(bgcolor)
		else:
			image = font.render(text[:i], aa, color)
			window.blit(image, (rect.x, y))
		y += font_height + spacing
		# Remove the text we just blitted.
		text = text[i:]
	# Return the height of the result.
	return y-rect.top

# This function is used to get the height of a potentially wrapped piece of text.
# While we could just use draw_text for that, it would be much slower since it actually draws the text.
def get_height(text, width, font, spacing=2):
	y = 0
	font_height = font.size("Tg")[1]
	while text:
		i = 1
		while font.size(text[:i])[0] < width and i < len(text):
			i += 1
		if i < len(text):
			i = text.rfind(" ", 0, i) + 1
		y += font_height + spacing
		text = text[i:]
	return y

# A text input box for pygame windows. It wraps the inputted text. It currently does not support key repeating or cursor movement.
# Modified from code created by skrx, from Stack Overflow
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
			active = self.rect.collidepoint(event.pos)
			if active != self.active:
				self.active = active
				self.draw()
		elif event.type == pygame.KEYDOWN:
			if self.active:
				if event.key == pygame.K_RETURN:
					returntext = self.text
					self.text = ''
				elif event.key == pygame.K_BACKSPACE:
					self.text = self.text[:-1]
				else:
					self.text += event.unicode
				self.draw()
				if event.key == pygame.K_RETURN:
					return returntext
	def draw(self):
		# Clear the area. Without this, the text gets blurred more and more with each re-blitting. I have no idea why.
		pygame.draw.rect(self.window, self.bgcolor, self.textrect, 0)
		# Draw the text.
		draw_text(self.window, self.text, self.textcolor, self.textrect, self.font)
		# Draw the border.
		pygame.draw.rect(self.window, self.rectcolor(), self.rect, 1)

# A list of separate text items to be displayed on a pygame window, inside a specified area and with items separated.
# The main useful feature is automatic rearrangement of the text items when new ones are inserted or deleted.
class TextList:
	def __init__(self, window, rect, bgcolor, bordercolor, textcolor, font):
		self.window = window
		self.rect = rect
		self.bgcolor = bgcolor
		self.bordercolor = bordercolor
		self.textcolor = textcolor
		self.font = font
		self.message_list = []
		self.new_height = 0 # The y that a new message will start at.
		self.spacing = 1
	def add(self, message):
		self.message_list += [message]
		height = get_height(message, self.rect.w, self.font)
		# If we're overflowing the box, flush old messages until there's enough room.
		while self.new_height + height + self.spacing > self.rect.h:
			self.new_height -= get_height(self.message_list[0], self.rect.w, self.font, self.spacing) + self.spacing
			self.message_list.pop(0)
		self.new_height += height + self.spacing
		self.draw()
	def remove_by_content(eslf, message):
		i = 0
		for msg in self.message_list:
			if msg == message: return self.remove_by_index(i)
			i += 1
		print("Could not remove message '"+message+"' because it was not found")
	def remove_by_index(self, index):
		self.message_list.pop(index)
		self.draw()
	def draw(self):
		pygame.draw.rect(self.window, self.bgcolor, self.rect, 0)
		pygame.draw.rect(self.window, self.bordercolor, self.rect, 1)
		self.new_height = 0
		for message in self.message_list:
			# Cropping the rect slightly so the text isn't on the border.
			height = draw_text(self.window, message, self.textcolor, pygame.Rect(self.rect.x+2, self.rect.y+self.new_height+1, self.rect.w-2, self.rect.h-1), self.font)
			self.new_height += height + self.spacing


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
		log_rect = pygame.Rect(rect.x, rect.y, rect.w, rect.h-entryheight+1) # This +1 makes the borders overlap, so it doesn't look ugly
		self.log = TextList(window, log_rect, bgcolor, bordercolor, textcolor, font)
		entry_rect = pygame.Rect(rect.x, rect.bottom-entryheight, rect.w, entryheight)
		self.entry_box = InputBox(window, entry_rect, bgcolor, textcolor, active_color, inactive_color, font)
	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN: self.entry_box.handle_event(event)
		if event.type == pygame.KEYDOWN: return self.entry_box.handle_event(event)
	def add_message(self, message):
		self.log.add(message)
		self.entry_box.draw()
	def draw(self):
		self.log.draw()
		self.entry_box.draw()

# Currently, these buttons trigger only on down-click. They have a color change for being hovered over, but don't support color changes when being pressed.
class Button:
	def __init__(self, window, rect, active_color, inactive_color, textcolor, font, label):
		self.window = window
		self.rect = rect
		self.textrect = (rect.x+1, rect.y+1, rect.w-2, rect.h-2)
		self.active_color = active_color
		self.inactive_color = inactive_color
		self.textcolor = textcolor
		self.font = font
		self.label = label
		self.active = False
	def handle_event(self, event):
		if event.type == pygame.MOUSEMOTION:
			self.active = self.rect.collidepoint(event.pos)
			self.draw()
		if event.type == pygame.MOUSEBUTTONDOWN:
			return self.rect.collidepoint(event.pos)
	def draw(self):
		if self.active: pygame.draw.rect(self.window, self.active_color, self.rect, 0)
		else: pygame.draw.rect(self.window, self.inactive_color, self.rect, 0)
		draw_text(self.window, self.label, self.textcolor, self.textrect, self.font)

def draw_bar(window, rect, border_color, fill_color, empty_color, capacity, value):
		pygame.draw.rect(window, border_color, rect, 1)
		#inner_rect = (rect.left+1, rect.top+1, rect.w-2, rect.h-2)
		if capacity > 0:
			fill_rect = pygame.Rect(rect.left+1, rect.top+1, int((rect.w-2)*(value/capacity)), rect.h-2)
		else:
			fill_rect = pygame.Rect(rect.left+1, rect.top+1, rect.w-2, rect.h-2)
		empty_rect = pygame.Rect(fill_rect.right, rect.top+1, rect.w-2-fill_rect.w, rect.h-2)
		# We have to check these manually, because pygame.Rect apparently has a minimum size of 2x2.
		if value>0: pygame.draw.rect(window, fill_color, fill_rect, 0)
		if value<capacity: pygame.draw.rect(window, empty_color, empty_rect, 0)

# A list of buttons to be displayed like a TextList. It's unfortunate that this couldn't inherit anything.
class ButtonList:
	def __init__(self, window, rect, bgcolor, bordercolor, textcolor, active_color, inactive_color, font):
		self.window = window
		self.rect = rect
		self.bgcolor = bgcolor
		self.bordercolor = bordercolor
		self.textcolor = textcolor
		self.active_color = active_color
		self.inactive_color = inactive_color
		self.font = font
		self.button_list = []
		self.new_height = 0 # The y that a new button will start at.
		self.spacing = 2
		self.button_height = font.size('Tg')[1] + 4
	def add(self, message):
		self.button_list.append(Button(self.window, pygame.Rect(self.rect.x+2, self.rect.y+self.new_height+1, self.rect.w, self.button_height), self.active_color, self.inactive_color, self.textcolor, self.font, message))
		self.draw()
	def remove_by_content(self, msg):
		i = 0
		for button in self.button_list:
			if msg == button.label: return self.remove_by_index(i)
			i += 1
		print("Could not remove button '"+msg+"' because it was not found")
	def remove_by_index(self, index):
		self.button_list.pop(index)
		self.draw()
	def handle_event(self, event):
		for button in self.button_list:
			# Any truthy return value means the button was clicked.
			if button.handle_event(event): return button.label
	def draw(self):
		pygame.draw.rect(self.window, self.bgcolor, self.rect, 0)
		pygame.draw.rect(self.window, self.bordercolor, self.rect, 1)
		self.new_height = 0
		for button in self.button_list:
			button.draw()
			self.new_height += self.button_height + self.spacing
			# Don't overflow our box.
			if self.new_height + self.button_height + self.spacing > self.rect.h: break
