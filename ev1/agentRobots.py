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
        self.boxes = []
        self.actions = [self.move]
        self.starting_position = self.define_starting_position()  # random position
        self.position = self.starting_position

    def move(self):
        if self.boxes:
            return self.move_to_box()
        else:
            return self.move_to_stack()

    def move_to_box(self):
        return ap.move_to(self, random.choice(BOXES_COORDS))

    def move_to_stack(self):
        return ap.move_to(self, BOX_STACK_COORDINATES)

    def move_to(self, target):
        while self.position != target:
            if self.position[0] < target[0]:
                self.position = (self.position[0] + 1, self.position[1])
            elif self.position[0] > target[0]:
                self.position = (self.position[0] - 1, self.position[1])
            elif self.position[1] < target[1]:
                self.position = (self.position[0], self.position[1] + 1)
            elif self.position[1] > target[1]:
                self.position = (self.position[0], self.position[1] - 1)
            return self.position

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
