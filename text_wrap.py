from pygame import *

def draw_text(window, text, color, rect, font, spacing=2, aa=True, bgcolor=None):
	rect = Rect(rect)
	y = rect.top
	font_height = font.size("Tg")[1]
	while text:
		i = 1
		# Cut if the row of text will be outside our area.
		if y + font_height > rect.bottom:
			break
		# Determine maximum width of line.
		while font.size(text[:i])[0] < rect.width and i < len(text):
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
			window.blit(image, (rect.left, y))
		y += font_height + spacing
		# Remove the text we just blitted.
		text = text[i:]
	# Return the height of the result.
	return y-rect.top

# This function is used to get the height of a potentially wrapped piece of text.
# While we could just use draw_text for that, it would be much slower since it actually draws the text.
def get_height(text, width, spacing, font):
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
