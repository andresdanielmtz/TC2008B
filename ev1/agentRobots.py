import agentpy as ap
import numpy as np
import random

BOX_STACK_COORDINATES = (0, 0)
LIMITS = (10, 10)
BOXES_COORDS = [
    (random.randint(0, LIMITS[0]), random.randint(0, LIMITS[1])) for i in range(10)
]


class RobotAgent(ap.Agent):
    def see(self):
        pass

    def setup(self):
        self.boxes = 0
        self.actions = [self.move]
        self.starting_position = self.define_starting_position()  # random position

    def move(self):
        pass

    def define_starting_position(self):
        while True:
            starting_position = (
                random.randint(0, LIMITS[0]),
                random.randint(0, LIMITS[1]),
            )
            if starting_position not in BOXES_COORDS:
                return starting_position

    def update(self):
        self.see()
        a = self.move()
        self.action(a)
