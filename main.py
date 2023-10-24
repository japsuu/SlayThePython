#
# Project: Slay the Python
# Author: Jasper Honkasalo
#
import time

import pygame

from utils import debugging
from gameloop import update
from state_management import GameState
from utils.input import Inputs

MAX_DELTA_TIME = 1 / 30  # Cap the delta time to 30fps (to prevent the game from running too fast if the FPS drops)
DEBUG_HELP = "(F1: Toggle debug, F2: Toggle extended referrer debug, F3: Debug object under mouse, F4: Debug game state, F5: Debug alive game objects)"


def main():
    # Pygame setup
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

        start_frame(screen, game_state)

        # If there is no save (the game was just opened or a run has just ended), start a new save
        if game_state.current_game_save is None:
            del game_state
            game_state = GameState(screen, clock)
            game_state.enter_main_menu()
            end_frame(clock, game_state, 1 / 60)
            continue  # Skip the rest to not register any inputs this frame
        else:
            update_window_title(game_state)

        gameloop_update_time = update_gameloop(screen, game_state)

        framebuffer_time = draw_framebuffer(game_state)

        debug_update_time = process_debug_inputs(game_state)

        fps = round(clock.get_fps())
        delta_time = clock.get_time() / 1000
        debugging.set_stats(fps, delta_time, framebuffer_time, gameloop_update_time, debug_update_time)
        debugging.draw_debug_window()

        end_frame(clock, game_state, delta_time)

    pygame.quit()


def start_frame(screen, game_state: GameState):
    # Clear the screen
    if game_state and game_state.current_room_background:
        screen.blit(game_state.current_room_background, (0, 0))
    else:
        screen.fill("black")

    # Clear the frame buffer
    game_state.frame_buffer.clear()


def update_window_title(game_state: GameState):
    save_name = game_state.current_game_save.save_game_name
    current_room = game_state.current_game_save.dungeon_room_index + 1
    boss_room = game_state.game_data.boss_room_index + 1
    window_caption = f"Slay the Python - {save_name} - Room {current_room} of {boss_room} - FPS: {round(game_state.clock.get_fps())} {DEBUG_HELP}"
    pygame.display.set_caption(window_caption)


def update_gameloop(screen, game_state: GameState):
    start = time.time()
    update(screen, game_state)
    end = time.time()
    return end - start


def draw_framebuffer(game_state: GameState):
    start = time.time()
    game_state.frame_buffer.draw()
    end = time.time()
    return end - start


def process_debug_inputs(game_state: GameState):
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

    if Inputs.is_key_pressed(pygame.K_ESCAPE):
        if game_state.is_help_shown:
            game_state.is_help_shown = False
        else:
            game_state.is_pause_menu_shown = not game_state.is_pause_menu_shown

    debugging.update_debug_window()
    end = time.time()
    return end - start


def end_frame(clock, game_state, delta_time):
    pygame.display.flip()

    # Limit FPS to 144
    clock.tick(144)
    # Cap the delta time to 30fps (to prevent the game from running too fast if the FPS drops)
    game_state.delta_time = min(delta_time, MAX_DELTA_TIME)


if __name__ == "__main__":
    main()
