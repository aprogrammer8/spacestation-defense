from pygame import *

def draw_text(window, text, color, rect, font, aa=True, bg=None):
	rect = Rect(rect)
	y = rect.top
	line_spacing = 2
	# get the height of the font
	font_height = font.size("Tg")[1]
	while text:
		i = 1
		# determine if the row of text will be outside our area
		if y + font_height > rect.bottom:
			break
		# determine maximum width of line
		while font.size(text[:i])[0] < rect.width and i < len(text):
			i += 1
		# if we've wrapped the text, then adjust the wrap to the last word
		if i < len(text):
			i = text.rfind(" ", 0, i) + 1
		# render the line and blit it to the window
		if bg:
			image = font.render(text[:i], 1, color, bg)
			image.set_colorkey(bg)
		else:
			image = font.render(text[:i], aa, color)
			window.blit(image, (rect.left, y))
		y += font_height + line_spacing
		# remove the text we just blitted
		text = text[i:]
	return y-rect.top
