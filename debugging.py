import pygame

# noinspection PyTypeChecker
debug_screen: pygame.Surface = None
# noinspection PyTypeChecker
debug_font: pygame.font.Font = None
debug_text_color = (0, 255, 0)
debug_target_object = None


def initialize_debug_window(screen: pygame.Surface):
    pygame.init()
    global debug_screen, debug_font, debug_target_object
    debug_screen = screen
    debug_font = pygame.font.Font(None, 15)


def draw_debug_window():
    global debug_font, debug_screen
    debug_strings = []
    if debug_target_object is None:
        debug_strings.append("No debug target")
    else:
        debug_strings = [f"{attr}: {getattr(debug_target_object, attr)}" for attr in dir(debug_target_object) if not callable(getattr(debug_target_object, attr)) and not attr.startswith("__")]

    y_offset = 30
    text_surface = debug_font.render(f"Debugging object: {debug_target_object}", True, debug_text_color)
    debug_screen.blit(text_surface, (30, y_offset))
    y_offset += debug_font.get_height()
    for debug_string in debug_strings:
        text_surface = debug_font.render(debug_string, True, debug_text_color)
        debug_screen.blit(text_surface, (30, y_offset))
        y_offset += debug_font.get_height()
