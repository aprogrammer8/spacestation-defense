import pygame

server = ("127.0.0.1", 1025)
SCREEN_SIZE = (1800, 1000)
LOG_RECT = pygame.Rect((int(SCREEN_SIZE[0]/2)-50, int(SCREEN_SIZE[1]/2)-50, 100, 100)) # The rect that messages like the username prompt appear in
NAME_ENTRY_RECT = pygame.Rect((int(SCREEN_SIZE[0]/2)-50, int(SCREEN_SIZE[1]/2)+60, 100, 20))
