import math
import utils.helpers as helpers

class Position:
    """Position components hold the position of an Entity in the esper World.
    """
    def __init__(self, x=0.0, y=0.0, angle=0.0, w=0.0, h=0.0, movable=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.angle = angle
        self.changed = False
        self.movable = movable
        self.center = (x + w // 2, y + h // 2)

    # Helper functions
    # Intended for testing purposes, and instantiate new Components from a Position component
    def __str__(self):
        return "Position[({},{}) {} {} {}]".format(self.x, self.y, self.w, self.h, self.angle)

    def _get_box(self):
        x = self.x
        y = self.y
        width = self.w
        height = self.h
        center = (x + width // 2, y + height // 2)
        points = [(x, y), (x+width, y), (x+width, y+height), (x, y+height)]
        if self.angle != 0:
            points = map(lambda x: helpers.rotate_around_point(x, math.radians(self.angle), center), points)
        return points