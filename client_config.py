import pygame

server = ("127.0.0.1", 1025)
SCREEN_SIZE = (1800, 1000)
LOG_RECT = pygame.Rect(int(SCREEN_SIZE[0]/2)-50, int(SCREEN_SIZE[1]/2)-50, 100, 100) # The rect that messages like the username prompt appear in
NAME_ENTRY_RECT = pygame.Rect(int(SCREEN_SIZE[0]/2)-50, int(SCREEN_SIZE[1]/2)+60, 100, 20)
CHAT_RECT = pygame.Rect(5, 5, int(SCREEN_SIZE[0]/5), SCREEN_SIZE[1]-10)
CHAT_ENTRY_HEIGHT = 50
BGCOLOR = (0, 0, 0)
TEXTCOLOR = (255, 255, 255)
ACTIVE_INPUTBOX_COLOR = (0, 255, 0)
INACTIVE_INPUTBOX_COLOR = (255, 0, 0)
CHAT_BORDERCOLOR = (170, 170, 170)
