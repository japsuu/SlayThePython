#
# Project: Slay the Python
# Author: Jasper Honkasalo
# Description: Initializes the game and updates the main game loop.
#
import time

import pygame

from utils import debugging
from gameloop import update
from state_management import GameState
from utils.constants import FONT_HELP
from utils.input import Inputs

MAX_DELTA_TIME = 1 / 30
DEBUG_HELP = "(F1: Toggle debug, F2: Toggle extended referrer debug, F3: Debug object under mouse, F4: Debug game state, F5: Debug alive game objects)"
is_help_shown = False


def main():
    # Pygame setup
    global is_help_shown
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Slay the Python")
    clock = pygame.time.Clock()
    game_state = GameState(screen, clock)

    debugging.initialize_debug_window(screen)

    running = True
    while running:
        Inputs.handle_input_events()

        if Inputs.should_quit():
            running = False

        # Clear the debug_screen
        if game_state and game_state.current_room_background:
            screen.blit(game_state.current_room_background, (0, 0))
        else:
            screen.fill("black")

        # Clear the frame buffer
        game_state.frame_buffer.clear()

        if game_state.current_game_save is not None:
            # Update the window title
            save_name = game_state.current_game_save.save_game_name
            current_room = game_state.current_game_save.dungeon_room_index + 1
            boss_room = game_state.game_data.boss_room_index + 1
            window_caption = f"Slay the Python - {save_name} - Room {current_room} of {boss_room} - FPS: {round(clock.get_fps())} {DEBUG_HELP}"
            pygame.display.set_caption(window_caption)
        # If there is no save (the game was just opened or a run has just ended), start a new save
        else:
            del game_state
            game_state = GameState(screen, clock)
            game_state.enter_main_menu()

        start = time.time()
        # Update and draw the game loop
        update(screen, game_state)
        end = time.time()
        gameloop_update_time = end - start

        # Draw the frame buffer
        start = time.time()
        game_state.frame_buffer.draw()
        end = time.time()
        framebuffer_time = end - start

        start = time.time()
        if Inputs.is_key_pressed(pygame.K_F1):
            debugging.set_enable_debugging(not debugging.enable_debugging)
            debugging.update_debug_window(True)

        if Inputs.is_key_pressed(pygame.K_F2):
            debugging.set_extended_referrer_debugging(not debugging.extended_referrer_debugging)
            debugging.update_debug_window(True)

        if Inputs.is_key_pressed(pygame.K_F3):
            debugging.set_enable_debugging(True)
            previous_target = debugging.debug_target_object
            for game_object in game_state.game_object_collection.game_objects:
                if game_object.rect.collidepoint(pygame.mouse.get_pos()):
                    debugging.set_debug_target_object(game_object)
            if debugging.debug_target_object == previous_target:
                debugging.set_debug_target_object(None)
            debugging.update_debug_window(True)

        if Inputs.is_key_pressed(pygame.K_F4):
            debugging.set_enable_debugging(True)
            debugging.set_debug_target_object(game_state)
            debugging.update_debug_window(True)

        if Inputs.is_key_pressed(pygame.K_F5):
            debugging.set_enable_debugging(True)
            debugging.set_debug_target_object(game_state.game_object_collection)
            debugging.update_debug_window(True)

        debugging.update_debug_window()
        end = time.time()
        debug_update_time = end - start

        if Inputs.is_key_pressed(pygame.K_h):
            is_help_shown = not is_help_shown

        if is_help_shown:
            help_text_lines = [
                "",
                "#GENERAL",
                "-> The goal of the game is to defeat all enemies in each room.",
                "-> There's a boss at the end of each dungeon.",
                "-> Your stats are shown in the bottom left corner.",
                "-> Your stats are 'health', 'mana', and 'block'.",
                "",
                "#HEALTH",
                "-> Your health does not regenerate between rooms.",
                "-> Certain cards have healing properties.",
                "",
                "#MANA",
                "-> Your mana resets at the start of each turn.",
                "-> You can only play a card if you have the required mana.",
                "",
                "#BLOCK",
                "-> Your block resets at the start of each turn.",
                "-> Block negates the damage you take.",
                "",
                "#COMBAT",
                "-> Enemies' next round intentions are shown on top of them.",
                "-> Enemies can heal by casting a buff (blue fire icon).",
                "-> Click an enemy to set it as the target.",
                "",
                "#CARDS",
                "-> You can play cards by clicking on them.",
                "-> The mana cost of a card is shown in card's top left corner.",
                "",
                "#SAVING",
                "-> Game is automatically saved when you enter a new room.",
                "-> When a run is over, the save is deleted.",
            ]
            help_background = pygame.Surface((500, 700))
            help_background.fill((0, 0, 0))
            help_background.set_alpha(230)
            help_background_rect = help_background.get_rect()
            help_background_rect.midtop = (screen.get_width() / 2, 10)
            screen.blit(help_background, help_background_rect)
            help_text = FONT_HELP.render("Help ('H' to close):", True, (180, 180, 180))
            help_text_rect = help_text.get_rect()
            help_text_rect.midtop = (help_background_rect.midtop[0], 20)
            previous_rect = help_text_rect
            screen.blit(help_text, help_text_rect)
            for help_text_line in help_text_lines:
                if help_text_line.startswith("#"):
                    help_text = FONT_HELP.render(help_text_line[1:], True, (255, 255, 255))
                    help_text_rect = help_text.get_rect()
                    help_text_rect.topleft = (help_background_rect.topleft[0] + 20, previous_rect.bottom + 10)
                    previous_rect = help_text_rect
                    screen.blit(help_text, help_text_rect)
                else:
                    help_text = FONT_HELP.render(help_text_line, True, (180, 180, 180))
                    help_text_rect = help_text.get_rect()
                    help_text_rect.topleft = (help_background_rect.topleft[0] + 20, previous_rect.bottom)
                    previous_rect = help_text_rect
                    screen.blit(help_text, help_text_rect)
        else:
            help_text = FONT_HELP.render("Press 'H' for help", True, (180, 180, 180))
            help_text_rect = help_text.get_rect()
            help_text_rect.midtop = (screen.get_width() / 2, 10)
            screen.blit(help_text, help_text_rect)

        fps = round(clock.get_fps())
        delta_time = clock.get_time() / 1000
        debugging.set_stats(fps, delta_time, framebuffer_time, gameloop_update_time, debug_update_time)
        debugging.draw_debug_window()

        pygame.display.flip()

        # Limit FPS to 144
        clock.tick(144)
        game_state.delta_time = delta_time
        # Cap the delta time to 30fps (to prevent the game from running too fast if the FPS drops)
        game_state.delta_time = min(game_state.delta_time, MAX_DELTA_TIME)

    pygame.quit()


if __name__ == "__main__":
    main()
