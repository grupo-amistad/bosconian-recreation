class Animation:
    def __init__(self, name, start, end, framerate):
        self.name, self.start, self.end, self.framerate = name, start, end, framerate


class CAnimation:
    def __init__(self, frames, animations, current=None, destroy_on_finish=False, loop=True):
        self.frames = frames
        self.animations = {a.name: a for a in animations}
        self.current = current or next(iter(self.animations))
        self.frame = self.animations[self.current].start
        self.elapsed = 0.0
        self.destroy_on_finish = destroy_on_finish
        self.loop = loop
        self.finished = False

    def play(self, name):
        if name != self.current:
            self.current = name
            self.frame = self.animations[name].start
            self.elapsed = 0.0
            self.finished = False
