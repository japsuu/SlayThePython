#
# Project: Slay the Python
# Author: Jasper Honkasalo
# Description: The main file of the game. Initializes the game and runs the game loop.
#

import pygame

from Gameplay import gameloop_update
from Input import Inputs
from StateManagement import GameData, GameState


def main():
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Slay the Python")
    clock = pygame.time.Clock()
    game_state = GameState()

    running = True
    while running:
        Inputs.handle_input_events()

        if Inputs.should_quit():
            running = False

        # Clear the screen
        screen.fill("black")

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
        gameloop_update(screen, game_state)

        pygame.display.flip()

        # Limit FPS to 60
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
