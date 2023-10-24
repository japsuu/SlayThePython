import hashlib
import random

from utils import logging


def lerp(a: float, b: float, t: float) -> float:
    """
    Linearly interpolate on the scale given by a to b, using t as the point on that scale.
    Examples
    --------
        50 == lerp(0, 100, 0.5)
        4.2 == lerp(1, 5, 0.8)
    """
    return (1 - t) * a + t * b


def lerp_unclamped(start, end, t):
    return start + (end - start) * t


def lerp_tuple(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    """
    Linearly interpolate on the scale given by a to b, using t as the point on that scale.
    """
    return (
        (1 - t) * a[0] + t * b[0],
        (1 - t) * a[1] + t * b[1],
    )


def get_random_inside_rect(rect_size) -> tuple[float, float]:
    """
    Returns a random point inside a unit rectangle.
    The unit rect is a square with both sides' width as 1, centered at (0, 0).
    """
    # Get a random point inside a unit square
    x = (random.random() * 2 - 1) * rect_size
    y = (random.random() * 2 - 1) * rect_size
    return x, y


def initialize_dungeon_random(seed: int, room_index: int):
    """Initialize the random module with a seed based on the given seed and room index."""
    xor_seed = seed ^ (room_index + 7229)
    random.seed(xor_seed)
    logging.log_info(f"Initialized dungeon random with seed {xor_seed}")


def hash_string(string: str):
    sha256 = hashlib.sha256(string.encode()).hexdigest()
    seed_integer = int(sha256, 16)
    return seed_integer


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)
