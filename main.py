#
# Project: Slay the Python
# Author: Jasper Honkasalo
# Description: Initializes the game and updates the main game loop.
#

import pygame

import utils
from gameplay import update_gameloop
from state_management import GameState


def main():
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Slay the Python")
    clock = pygame.time.Clock()
    game_state = GameState(screen, clock)

    running = True
    while running:
        utils.Inputs.handle_input_events()

        if utils.Inputs.should_quit():
            running = False

        # Clear the screen
        screen.fill("black")

        # Clear the frame buffer
        game_state.frame_buffer.clear()

        if game_state.current_game_save is not None:
            # Update the window title
            save_name = game_state.current_game_save.save_game_name
            current_room = game_state.current_game_save.dungeon_room_index + 1
            boss_room = game_state.game_data.BOSS_ROOM_INDEX + 1
            window_caption = f"Slay the Python - {save_name} - Room {current_room} of {boss_room}"
            pygame.display.set_caption(window_caption)

        # If there is no save (the game was just opened or a run has just ended), start a new save
        if game_state.current_game_save is None:
            game_state.display_blocking_save_selection_screen()

        # Update and draw the game loop
        update_gameloop(screen, game_state)

        # Draw the frame buffer
        game_state.frame_buffer.draw()

        pygame.display.flip()

        # Limit FPS to 60
        clock.tick(60)
        game_state.delta_time = clock.get_time() / 1000

    pygame.quit()


if __name__ == "__main__":
    main()
