from __future__ import annotations
from typing import TYPE_CHECKING

from utils.constants import FONT_DEBUG
from utils.input import Inputs

if TYPE_CHECKING:
    from typing import Optional

from _weakref import ReferenceType
from collections import Counter

import pygame
import weakref
import gc

debug_screen: Optional[pygame.Surface] = None
debug_surface: Optional[pygame.Surface] = None
debug_stats_surface: Optional[pygame.Surface] = None
debug_text_color = (0, 255, 0)
debug_target_object: Optional[ReferenceType] = None
enable_debugging: bool = False
extended_referrer_debugging: bool = False
DEBUG_UPDATE_INTERVAL = 500
last_debug_update_time = 0
debug_surface_width: int = 250
debug_surface_height: int = 200

debug_strings = []
debug_stats_strings = []
debug_info = []
debug_stats = []
debugged_object = ""


def set_enable_debugging(value: bool):
    global enable_debugging
    enable_debugging = value


def set_extended_referrer_debugging(value: bool):
    global extended_referrer_debugging
    extended_referrer_debugging = value


def set_stats(current_fps, current_delta_time, current_framebuffer_time, current_gameloop_update_time, current_debug_update_time):
    global debug_stats_strings
    debug_stats_strings.clear()
    debug_stats_strings.append(f"FPS: {current_fps}")
    debug_stats_strings.append(f"Frame ms: {current_delta_time:.4f}")
    debug_stats_strings.append(f"Framebuffer ms: {current_framebuffer_time:.4f}")
    debug_stats_strings.append(f"Gameloop ms: {current_gameloop_update_time:.4f}")
    debug_stats_strings.append(f"Debug ms: {current_debug_update_time:.4f}")
    debug_stats_strings.append(f"Mouse pos: {Inputs.get_mouse_position()}")


def set_debug_target_object(game_object):
    global debug_target_object, debugged_object
    if debug_target_object is not None:
        obj = debug_target_object()
        if obj is not None:
            obj.is_debugged = False
    if game_object is None:
        debug_target_object = None
        debugged_object = ""
        return
    game_object.is_debugged = True
    debug_target_object = weakref.ref(game_object)


def initialize_debug_window(screen: pygame.Surface):
    pygame.init()
    global debug_screen
    debug_screen = screen


def update_debug_window(force_update=False):
    global last_debug_update_time, debug_strings, debugged_object, debug_screen, debug_surface_width, debug_surface_height

    # Check if it's time to update the debug data
    if not force_update and (pygame.time.get_ticks() - last_debug_update_time < DEBUG_UPDATE_INTERVAL):
        return

    last_debug_update_time = pygame.time.get_ticks()

    if not enable_debugging:
        return

    debug_surface_height = 200
    debug_surface_width = 280
    debug_strings.clear()
    obj = None
    if debug_target_object is not None:
        obj = debug_target_object()
    if obj is None:
        debugged_object = f"TARGET OBJECT: none  -  Extended references: {extended_referrer_debugging}"
        debug_strings.append("No debug target")
    else:
        debugged_object = f"TARGET OBJECT: {truncate_obj_simple(obj)}  -  Extended references: {extended_referrer_debugging}"
        debug_strings.append(f"MEMBERS:")
        debug_strings.append("--------------------")
        for attr in dir(obj):
            if not callable(getattr(obj, attr)) and not attr.startswith("__"):
                debug_str = f"{attr}:   {truncate_obj_extended(getattr(obj, attr))}"
                debug_strings.append(debug_str)
        debug_strings.append("--------------------")
        all_referrers = gc.get_referrers(obj)
        debug_strings.append("")
        debug_strings.append(f"REFERRERS ({len(all_referrers)}):")
        debug_strings.append("--------------------")
        for referrer in all_referrers:
            # Clean up the referrer obj
            referrer_str = truncate_obj(referrer)
            debug_strings.append(f"{referrer_str}")
        if len(all_referrers) == 0:
            debug_strings.append("No referrers")
        debug_strings.append("--------------------")


def draw_debug_window():
    if not enable_debugging:
        return
    global debug_screen, debug_strings, debug_info, debug_surface_width, debug_surface_height, debug_surface, debug_stats_strings, debug_stats, debug_stats_surface

    # Update debug_info based on the latest debug_strings
    y_offset = 45
    max_width = 100  # To store the maximum width of debug strings
    debug_info.clear()
    for debug_string in debug_strings:
        text_surface = FONT_DEBUG.render(debug_string, True, debug_text_color)
        debug_info.append((text_surface, (30, y_offset)))
        y_offset += FONT_DEBUG.get_height() + 5
        max_width = max(max_width, text_surface.get_width())

    debug_surface_height = max(debug_surface_height, y_offset + 10)
    debug_surface_width = max(debug_surface_width, max_width + 30)
    if (debug_surface is None) or (debug_surface.get_width() < debug_surface_width or debug_surface.get_height() < debug_surface_height):
        debug_surface = pygame.Surface((debug_surface_width, debug_surface_height))
        debug_surface.set_alpha(128)

    debug_surface.fill((0, 0, 0))

    debug_screen.blit(debug_surface, (10, 10))

    text_surface = FONT_DEBUG.render(debugged_object, True, debug_text_color)
    debug_screen.blit(text_surface, (15, 15))

    for text_surface, position in debug_info:
        debug_screen.blit(text_surface, position)

    # Draw the debug stats
    y_offset = 15
    debug_stats.clear()
    left_start = debug_screen.get_rect().right - 210
    for debug_string in debug_stats_strings:
        text_surface = FONT_DEBUG.render(debug_string, True, debug_text_color)
        debug_stats.append((text_surface, (left_start + 5, y_offset)))
        y_offset += FONT_DEBUG.get_height() + 5
        max_width = max(max_width, text_surface.get_width())

    debug_surface_height = 95
    debug_surface_width = 140
    if debug_stats_surface is None:
        debug_stats_surface = pygame.Surface((debug_surface_width, debug_surface_height))
        debug_stats_surface.set_alpha(128)

    debug_stats_surface.fill((0, 0, 0))

    debug_screen.blit(debug_stats_surface, (left_start, 10))

    for text_surface, position in debug_stats:
        debug_screen.blit(text_surface, position)


def truncate_obj(obj):
    if extended_referrer_debugging:
        return truncate_obj_extended(obj)
    else:
        return truncate_obj_simple(obj)


def truncate_obj_simple(obj):
    if isinstance(obj, list):
        return truncate_obj_as_list(obj)

    if hasattr(obj, '__class__') and not isinstance(obj, type):
        class_name = obj.__class__.__name__
        if len(class_name) > 100:
            class_name = f"{class_name[:100]}..."
        return f"{class_name} (MEM_ADDR={hex(id(obj))})"

    obj_repr = repr(obj)
    if len(obj_repr) > 100:
        obj_repr = f"{obj_repr[:100]}..."
    return f"{obj_repr} (MEM_ADDR={hex(id(obj))})"


def truncate_obj_extended(obj):
    if isinstance(obj, list):
        return truncate_obj_as_list(obj)

    if len(str(obj)) > 150:
        obj = f"{str(obj)[:150]}..."
    return f"{str(obj)} (at memory address {hex(id(obj))})"


def truncate_obj_as_list(obj):
    item_counts = Counter(type(item).__name__ for item in obj)
    item_type_strings = [f"{count} x {item_type}" for item_type, count in item_counts.items()]

    list_elements = ', '.join(item_type_strings)
    if len(list_elements) > 100:
        list_elements = f"{obj[:100]}..."
    return f"List of \"{list_elements}\" -> (MEM_ADDR={hex(id(obj))})"
