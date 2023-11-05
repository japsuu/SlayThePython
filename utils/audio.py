import random
import pygame

from utils import logging

pygame.mixer.init()
pygame.mixer.set_num_channels(32)
delayed_sounds = []
"""
    A list of (sound, delay).
"""
looping_soundbank_sounds = []
"""
    A list of (soundbank, interval, the number of seconds when should be played again).
    This is used for looping sounds that should be played on interval.
"""


def update(delta_time):
    global delayed_sounds, looping_soundbank_sounds
    # Process delayed sounds
    for index, (sound, delay) in enumerate(delayed_sounds):
        if delay <= 0:
            play_one_shot(sound)
            delayed_sounds.pop(index)
        else:
            delayed_sounds[index] = (sound, delay - delta_time)
    # Process soundbank sounds
    for index, (soundbank, get_interval_seconds_func, next_play_time) in enumerate(looping_soundbank_sounds):
        if next_play_time <= 0:
            sound = random.choice(soundbank)
            play_one_shot(sound)
            looping_soundbank_sounds[index] = (soundbank, get_interval_seconds_func, get_interval_seconds_func())
        else:
            looping_soundbank_sounds[index] = (soundbank, get_interval_seconds_func, next_play_time - delta_time)


def add_looping_soundbank(soundbank, get_interval_seconds_func, start_delayed):
    if start_delayed:
        looping_soundbank_sounds.append((soundbank, get_interval_seconds_func, get_interval_seconds_func()))
    else:
        looping_soundbank_sounds.append((soundbank, get_interval_seconds_func, 0))


def play_one_shot(sound):
    channel = pygame.mixer.find_channel()
    if channel is not None:
        channel.play(sound[0])
        # logging.log_info(f"Playing sound {sound[1]}")
    else:
        logging.log_warning(f"Could not play sound {sound[1]} - no free channels!")


def play_one_shot_delayed(sound, delay_seconds):
    delayed_sounds.append((sound, delay_seconds))
    # logging.log_info(f"Delaying sound {sound[1]} for {delay_seconds} seconds")


def play_looping(loop_sound):
    channel = pygame.mixer.find_channel()
    if channel is not None:
        channel.play(loop_sound[0], loops=-1)
        # logging.log_info(f"Looping sound {loop_sound[1]}")
