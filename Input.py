import pygame


# No idea how to make singletons in Python, so this will have to do
class Inputs:
    def __init__(self):
        self.quit = False
        self.mouse_pos = (0, 0)
        self.mouse_buttons_pressed_this_frame = set()
        self.mouse_buttons_up = set()
        self.mouse_buttons_down = set()
        self.keys_pressed_this_frame = set()
        self.keys_up = set()
        self.keys_down = set()
        self.unicode: str = ""

    @staticmethod
    def is_key_down(key):
        return key in global_inputs.keys_down

    @staticmethod
    def is_key_up(key):
        return key in global_inputs.keys_up

    @staticmethod
    def is_key_pressed(key):
        return key in global_inputs.keys_pressed_this_frame

    @staticmethod
    def is_mouse_button_down(button):
        return button in global_inputs.mouse_buttons_down

    @staticmethod
    def is_mouse_button_up(button):
        return button in global_inputs.mouse_buttons_up

    @staticmethod
    def is_mouse_button_pressed(button):
        return button in global_inputs.mouse_buttons_pressed_this_frame

    @staticmethod
    def get_mouse_position():
        return global_inputs.mouse_pos

    @staticmethod
    def should_quit():
        return global_inputs.quit

    @staticmethod
    def get_unicode():
        return global_inputs.unicode

    @staticmethod
    def handle_input_events():
        global_inputs.keys_up.clear()
        global_inputs.mouse_buttons_up.clear()
        global_inputs.keys_pressed_this_frame.clear()
        global_inputs.mouse_buttons_pressed_this_frame.clear()
        global_inputs.unicode = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global_inputs.quit = True
            elif event.type == pygame.KEYDOWN:
                global_inputs.keys_down.add(event.key)
                global_inputs.keys_pressed_this_frame.add(event.key)
                global_inputs.unicode = event.unicode
            elif event.type == pygame.KEYUP:
                global_inputs.keys_down.discard(event.key)
                global_inputs.keys_up.add(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                global_inputs.mouse_buttons_down.add(event.button)
                global_inputs.mouse_buttons_pressed_this_frame.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                global_inputs.mouse_buttons_down.discard(event.button)
                global_inputs.mouse_buttons_up.add(event.button)
            elif event.type == pygame.MOUSEMOTION:
                global_inputs.mouse_pos = event.pos


global_inputs = Inputs()
