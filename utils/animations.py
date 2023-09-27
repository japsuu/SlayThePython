from pygame.math import lerp, Vector2


class Tween:
    def __init__(self, start_value, end_value, duration: float, value_updated_callback=None, finished_callback=None):
        self.is_finished = False
        self.start_value = start_value
        self.current_value = start_value
        self.end_value = end_value
        self.duration: float = duration
        self.elapsed_time: float = 0
        self.on_value_updated_callback = value_updated_callback
        self.on_finished_callback = finished_callback

    def update(self, dt):
        self.elapsed_time += dt
        if self.elapsed_time >= self.duration:
            if not self.is_finished:
                self.is_finished = True
                if self.on_finished_callback:
                    self.on_finished_callback()
            self.current_value = self.end_value
            if self.on_value_updated_callback:
                self.on_value_updated_callback(self.current_value)
            return self.current_value

        progress = self.elapsed_time / self.duration
        self.current_value = self._calculate_current(progress)

        if self.on_value_updated_callback:
            self.on_value_updated_callback(self.current_value)

        return self.current_value

    def _calculate_current(self, progress):
        return lerp(self.start_value, self.end_value, progress)


class DualTween(Tween):
    def __init__(self, start_pos: tuple, end_pos: tuple, duration: float, value_updated_callback=None, finished_callback=None):
        super().__init__(start_pos, end_pos, duration, value_updated_callback, finished_callback)

    def _calculate_current(self, progress):
        return Vector2(self.start_value).lerp(self.end_value, progress)


class Animation:    # TODO: Animation.copy method to create animation templates?
    """
    An animation that consists of multiple tweens.
    is_finished is True when all tweens are finished.
    """

    def __init__(self, tweens: list[Tween], finished_callback=None):
        self.tweens = tweens
        self.is_finished = False
        self.on_finished_callback = finished_callback

    def update(self, dt):
        for tween in self.tweens:
            tween.update(dt)

        if all(tween.is_finished for tween in self.tweens):
            if not self.is_finished:
                self.is_finished = True
                if self.on_finished_callback:
                    self.on_finished_callback()

