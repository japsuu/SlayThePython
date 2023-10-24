from pygame.math import lerp, Vector2


class Tween:
    """
    Gradually changes a value from start_value to end_value over a duration.
    """
    def __init__(self, start_value, end_value, duration: float, value_updated_callback=None, finished_callback=None):
        self.is_finished = False
        self.start_value = start_value
        self.current_value = start_value
        self.end_value = end_value
        self.duration: float = duration
        self.elapsed_time: float = 0
        self.on_value_updated_callback = value_updated_callback
        self.on_finished_callback = finished_callback
        self.delta_time = 1/60

    def update(self, dt):
        self.delta_time = dt
        self.elapsed_time += dt
        if self.elapsed_time >= self.duration:
            self.current_value = self.end_value
            if self.on_value_updated_callback:
                self.on_value_updated_callback(self.current_value)
            if not self.is_finished:
                self.is_finished = True
                if self.on_finished_callback:
                    self.on_finished_callback()
            return self.current_value

        progress = self.elapsed_time / self.duration
        self.current_value = self._calculate_current(progress)

        if self.on_value_updated_callback:
            self.on_value_updated_callback(self.current_value)

        return self.current_value

    def _calculate_current(self, progress):
        return lerp(self.start_value, self.end_value, progress)


class GetterTween(Tween):
    """
    Like a Tween, but for a getter function.
    """
    def __init__(self, getter, end_value, duration: float, value_updated_callback=None, finished_callback=None):
        super().__init__(getter(), end_value, duration, value_updated_callback, finished_callback)
        self.getter = getter

    def _calculate_current(self, progress):
        self.start_value = self.getter()
        return lerp(self.start_value, self.end_value, progress * self.duration)     # Scuffed but works; this is not how lerp should work


class TupleTween(Tween):
    """
    Like a Tween, but for a tuple.
    """
    def __init__(self, start_pos: tuple, end_pos: tuple, duration: float, value_updated_callback=None, finished_callback=None):
        super().__init__(start_pos, end_pos, duration, value_updated_callback, finished_callback)
        self.delta_time = 1/60

    def _calculate_current(self, progress):
        return Vector2(self.start_value).lerp(self.end_value, progress)


class GetterTupleTween(Tween):
    """
    Like a GetterTween, but for a tuple.
    """
    def __init__(self, getter, end_pos: tuple, duration: float, value_updated_callback=None, finished_callback=None):
        super().__init__(getter(), end_pos, duration, value_updated_callback, finished_callback)
        self.getter = getter

    def _calculate_current(self, progress):
        self.start_value = self.getter()
        return Vector2(self.start_value).lerp(self.end_value, progress * self.duration)     # Scuffed but works; this is not how lerp should work


class Animation:
    """
    A collection of multiple tweens.
    Is_finished is True when all tweens are finished.
    """
    def __init__(self, tweens: list[Tween], finished_callback=None, name="unnamed"):
        self.tweens = tweens
        self.is_finished = False
        self.on_finished_callback = finished_callback
        self.name = name

    def update(self, dt):
        for tween in self.tweens:
            if not tween.is_finished:
                tween.update(dt)

        if all(tween.is_finished for tween in self.tweens):
            if not self.is_finished:
                self.is_finished = True
                if self.on_finished_callback:
                    self.on_finished_callback()
