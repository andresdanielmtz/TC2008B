# TC2008B Modelación de Sistemas Multiagentes con gráficas computacionales
# Python server to interact with Unity via POST
# Sergio Ruiz-Loza, Ph.D. March 2021
# Actualizado por Axel Dounce, PhD

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import threading
import agentpy as ap
from matplotlib import pyplot as plt
import random
import time
from owlready2 import *
import numpy as np

global model


class Server(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        logging.info(
            "GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers)
        )
        response_data = get_response()
        self._set_response()
        
        # Format the JSON for pretty printing
        formatted_json = json.dumps(json.loads(response_data), indent=2)
        
        # Wrap the JSON in HTML for better browser display
        html_response = f"""
        <html>
        <head>
            <title>JSON Response</title>
        </head>
        <body>
            <pre>{formatted_json}</pre>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = json.loads(self.rfile.read(content_length))
        logging.info(
            "POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
            str(self.path),
            str(self.headers),
            json.dumps(post_data),
        )

        response_data = post_response(post_data)
        self._set_response()
        
        # Format the JSON for pretty printing
        formatted_json = json.dumps(json.loads(response_data), indent=2)
        
        # Wrap the JSON in HTML for better browser display
        html_response = f"""
        <html>
        <head>
            <title>JSON Response</title>
        </head>
        <body>
            <pre>{formatted_json}</pre>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode("utf-8"))


def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n")  # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:  # CTRL+C stops the server
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")

    # ==========================================Procesamiento de datos de cliente=========================
def get_robot_data(robot):
    data = {
        "id": robot.id,
        "action": robot.action,
        "position": model.grid.positions[robot],
        "direction": robot.direction,
        "box_id": robot.robot_grab_id,
    }
    if robot.action == "stack":
        data["stack_coord"] = robot.stack_coord
    return data


def post_response(data):
    robot_id = data.get("id")
    new_position = data.get("position")
    direction = data.get("direction")

    # Find the robot by ID
    robot = next((r for r in model.robots if r.id == robot_id), None)
    
    if robot is None:
        return json.dumps({"error": "Robot not found"}), 404

    # Update the robot's position and direction
    if new_position:
        model.grid.move_by(robot, tuple(new_position))  # Move robot to new position
    if direction:
        robot.direction = tuple(direction)  # Update direction

    robot.action = "moved"  # Example action, can be customized

    # Perform a step in the simulation


    # Prepare the response data
    response = {
        "robot_actions": [get_robot_data(robot) for robot in model.robots],
        "box_positions": [
            {
                "id": box.id,
                "position": model.grid.positions[box],
                "status": "stacked" if box.stacked else "idle",
                "num_boxes": box.boxStack,
            }
            for box in model.boxes
        ],
    }

    model.step()

    return json.dumps(response)

def get_response():

    response = {
        "robot_actions": [get_robot_data(robot) for robot in model.robots],
        "box_positions": [
            {
                "id": box.id,
                "position": model.grid.positions[box],
                "action": "stacked" if box.stacked else "idle",
                "num_boxes": box.boxStack,
            }
            for box in model.boxes
        ],
    }
    model.step()
    return json.dumps(response)


# ===================Definición de Agentes y simulación (Model)=================
#
#
onto = get_ontology("file://onto.owl")
# ONTOLOGIA
# onto.delete()
with onto:

    class Entity(Thing):
        pass

    class Vaccum(Entity):
        pass

    class Dirt(Entity):
        pass

    class Box(Entity):
        boxStack = 1
        pass

    class Place(Thing):
        pass

    class Position(Thing):
        pass

    class has_place(ObjectProperty, FunctionalProperty):
        domain = [Entity]
        range = [Place]

    class has_position(DataProperty, FunctionalProperty):
        domain = [Place]
        range = [str]

        pass


class BoxPile(ap.Agent):

    def setup(self):
        self.boxStack = 1
        self.agentType = 4
        self.first_step = True
        self.pos = None
        self.stacked = False
        self.id = self.model.next_box_id() 

    def add_box(self):
        if self.boxStack < 3:
            self.boxStack += 1
            self.stacked = True
        else:
            self.stacked = False
            print("Stack is full. Stack height: " + str(self.boxStack))

    def step(self):
        if self.first_step:
            self.pos = self.model.grid.positions[self]
            self.first_step = False
    def update(self):
        pass

    def end(self):
        pass

class Stack(ap.Agent):
    def setup(self):
        self.boxStack = 2
        self.agentType = 2  # New agent type for Stack

    def add_box(self):
        if self.boxStack < 5:
            self.boxStack += 1
            return True
        return False

    def remove_box(self):
        if self.boxStack > 2:
            self.boxStack -= 1
            return True
        return False
    def step(self):
        pass

    def update(self):
        pass
    
    def end(self):
        pass

import random

class Robot(ap.Agent):
    def setup(self):
        self.agentType = 0
        self.carryingBox = False
        self.direction = (0, -1)  # Initial direction (facing North)
        self.previous_position = None
        self.frustration = 0
        self.frustration_threshold = 5
        self.steps_since_last_turn = 0
        self.turn_interval = random.randint(5, 15)  # Randomize turn interval
        self.boxes_grabbed = 0
        self.boxes_stacked = 0
        self.action = "setup"
        self.robot_grab_id = None  # Add variable to store grabbed box ID
        self.stack_coord = None  # Add variable to store stacking coordinates
        self.just_stacked = False
        self.actions = (
            self.move_and_grab,
            self.turn_and_stack,
            self.turn,
            self.random_turn,
            self.move_n,
            self.move_e,
            self.move_s,
            self.move_w,
            self.stack_box,  # New action
        )
        self.rules = (
            self.rule_move_and_grab,
            self.rule_turn_and_stack,
            self.rule_turn,
            self.rule_random_turn,
            self.rule_move_n,
            self.rule_move_e,
            self.rule_move_s,
            self.rule_move_w,
            self.rule_stack_box,  # New rule
        )
    def rule_stack_box(self, act):
        return act == self.stack_box and self.carryingBox and any(p[0] == "BoxPile" for p in self.per)


    def step(self):
        if self.just_stacked:
            self.action = "move" 
            self.just_stacked = False
            self.stack_coord = None
        self.see(self.model.grid)
        self.next()

    def next(self):
        for act in self.actions:
            for rule in self.rules:
                if rule(act):
                    act()
                    return  # Only perform one action per step
        self.random_turn()  # If no action is taken, random turn

    def rule_move_and_grab(self, act):
        return act == self.move_and_grab

    def rule_turn_and_stack(self, act):
        return act == self.turn_and_stack and self.carryingBox and any(p[0] == "BoxPile" for p in self.per)

    def rule_turn(self, act):
        return act == self.turn

    def rule_random_turn(self, act):
        return act == self.random_turn and self.steps_since_last_turn >= self.turn_interval

    def rule_move_n(self, act):
        return act == self.move_n and not self.carryingBox

    def rule_move_e(self, act):
        return act == self.move_e and not self.carryingBox

    def rule_move_s(self, act):
        return act == self.move_s and not self.carryingBox

    def rule_move_w(self, act):
        return act == self.move_w and not self.carryingBox
    
    def stack_box(self):
        self.action = "stack"
        for perception in self.per:
            if perception[0] == "BoxPile":
                box_pos = perception[1]
                box_agents = self.model.grid.agents[box_pos]
                box_pile = next((agent for agent in box_agents if isinstance(agent, BoxPile)), None)
                if box_pile:
                    box_pile.add_box()
                    self.carryingBox = False
                    self.boxes_stacked += 1
                    self.stack_coord = box_pile.id
                    self.just_stacked = True
                    self.robot_grab_id = None
                    print(f"Robot at {self.model.grid.positions[self]} stacked a box at {box_pile.pos}. Stack height: {box_pile.boxStack}. Total stacked: {self.boxes_stacked}")
                    return
        print(f"Robot at {self.model.grid.positions[self]} couldn't find a box to stack on.")

    def move_and_grab(self):
        self.action = "move"
        front_pos = self.get_front_position()
        if self.is_valid_position(front_pos):
            front_agents = self.model.grid.agents[front_pos]
            if not front_agents:
                # Move forward if the space is empty
                self.model.grid.move_by(self, self.direction)
                self.steps_since_last_turn += 1
                print(f"Robot at {self.model.grid.positions[self]} moved forward to {front_pos}")
            elif self.carryingBox and any(isinstance(agent, BoxPile) for agent in front_agents):
                # Stack the box if carrying one and colliding with another box
                self.stack_box()
            else:
                # Turn if there's an obstacle that's not a box
                self.random_turn()
                return
        else:
            # Turn if the position is invalid (border)
            self.random_turn()
            return

        # Check for adjacent boxes after moving
        if not self.carryingBox:
            for perception in self.per:
                if perception[0] == "BoxPile":
                    box_pos = perception[1]
                    box_agents = self.model.grid.agents[box_pos]
                    box = next((agent for agent in box_agents if isinstance(agent, BoxPile)), None)
                    if box and box.boxStack == 1:
                        self.model.grid.remove_agents(box)
                        self.model.boxes.remove(box)
                        self.carryingBox = True
                        self.boxes_grabbed += 1
                        self.action = "grab"
                        self.robot_grab_id = box.id  # Store the grabbed box ID

                        print(f"Robot at {self.model.grid.positions[self]} grabbed an adjacent box from {box_pos}. Total grabbed: {self.boxes_grabbed}")
                        break


    def turn_and_stack(self):
        
        for perception in self.per:
            if perception[0] == "BoxPile":
                box_pos = perception[1]
                current_pos = self.model.grid.positions[self]
                direction = (box_pos[0] - current_pos[0], box_pos[1] - current_pos[1])
                
                # Turn until facing the box
                while self.direction != direction:
                    self.turn()
                self.action = "turn"
                
                # Now that we're facing the box, stack it
                box_agents = self.model.grid.agents[box_pos]
                box = next((agent for agent in box_agents if isinstance(agent, BoxPile)), None)
                if box:
                    # Instead of using a Stack agent, we can just mark the position as occupied
                    self.model.grid.remove_agents(box)
                    self.action = "stack"
                    self.model.boxes.remove(box)
                    # Mark the position as occupied by a stack
                    self.model.grid.add_agents([], positions=[box_pos])  # No agent, just marking the position
                    self.carryingBox = False
                    print(f"Robot at {current_pos} created a stack at {box_pos}")
                return

    def move_n(self):
        self.direction = (-1, 0)  # North
        self.move()

    def move_e(self):
        self.direction = (0, 1)  # East
        self.move()

    def move_s(self):
        self.direction = (1, 0)  # South
        self.move()

    def move_w(self):
        self.direction = (0, -1)  # West
        self.move()

    def move(self):
        front_pos = self.get_front_position()
        self.action = "move"
        if self.is_valid_position(front_pos):
            front_agents = self.model.grid.agents[front_pos]
            if not front_agents:
                # Move forward if the space is empty
                self.model.grid.move_by(self, self.direction)
                print(f"Robot at {self.model.grid.positions[self]} moved to {front_pos}")
            elif self.carryingBox and any(isinstance(agent, BoxPile) for agent in front_agents):
                # Stack the box if carrying one and colliding with another box
                self.stack_box()
            else:
                # Turn if there's an obstacle that's not a box
                self.random_turn()
        else:
            # Turn if the position is invalid (border)
            self.random_turn()


    def turn(self):
        self.action = "turn 90"
        if self.direction == (-1, 0):  # North
            self.direction = (0, 1)  # East
        elif self.direction == (0, 1):  # East
            self.direction = (1, 0)  # South
        elif self.direction == (1, 0):  # South
            self.direction = (0, -1)  # West
        elif self.direction == (0, -1):  # West
            self.direction = (-1, 0)  # North
        print(f"Robot at {self.model.grid.positions[self]} turned to face {self.direction}")

    def random_turn(self):
        self.action = "turn random"
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # N, E, S, W
        self.direction = random.choice(directions)
        self.steps_since_last_turn = 0
        self.turn_interval = random.randint(5, 15)  # Reset turn interval
        print(f"Robot at {self.model.grid.positions[self]} randomly turned to face {self.direction}")

    def get_front_position(self):
        current_pos = self.model.grid.positions[self]
        return (current_pos[0] + self.direction[0], current_pos[1] + self.direction[1])

    def is_valid_position(self, pos):
        return 0 <= pos[0] < self.model.p.M and 0 <= pos[1] < self.model.p.N

    def see(self, grid):
        self.per = []
        current_pos = grid.positions[self]
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # N, E, S, W

        for direction in directions:
            neighbor_pos = (
                current_pos[0] + direction[0],
                current_pos[1] + direction[1],
            )

            if self.is_valid_position(neighbor_pos):
                agents_at_pos = grid.agents[neighbor_pos]
                if agents_at_pos:
                    agent = next(iter(agents_at_pos))
                    if isinstance(agent, BoxPile):
                        self.per.append(("BoxPile", neighbor_pos))
                    elif isinstance(agent, Robot):
                        self.per.append(("Robot", neighbor_pos))
                else:
                    self.per.append(("Empty", neighbor_pos))
            else:
                self.per.append(("Border", neighbor_pos))
    def end(self):
        print(f"Robot at {self.model.grid.positions[self]} final stats: Grabbed: {self.boxes_grabbed}, Stacked: {self.boxes_stacked}")


class RobotModel(ap.Model):
    def setup(self):
        self.box_id_counter = 0 
        self.robots = ap.AgentList(self, self.p.robots, Robot)
        self.boxes = ap.AgentList(self, self.p.boxes, BoxPile)
        self.stacks = ap.AgentList(self, 0, Stack)  # Start with 0 stacks

        self.grid = ap.Grid(self, (self.p.M, self.p.N), track_empty=True)

        self.grid.add_agents(self.robots, random=True, empty=True)
        self.grid.add_agents(self.boxes, random=True, empty=True)
   

    def next_box_id(self):
        self.box_id_counter += 1
        return self.box_id_counter
    def step(self):
        self.robots.step()

    def update(self):
        pass

    def end(self):
        print("\nSimulation Summary:")
        for i, robot in enumerate(self.robots):
            print(f"Robot {i}: Grabbed {robot.boxes_grabbed} boxes, Stacked {robot.boxes_stacked} boxes")
        
        stack_sizes = [box.boxStack for box in self.boxes if box.boxStack > 1]
        print(f"\nFinal stack count: {len(stack_sizes)}")
        print(f"Stack sizes: {stack_sizes}")
        print(f"Total boxes in stacks: {sum(stack_sizes)}")
        print(f"Single boxes remaining: {len([box for box in self.boxes if box.boxStack == 1])}")
#


#
#


# ==================================Main===========================

if __name__ == "__main__":
    from sys import argv
    import time

    # so we can use it anywhere else
    parameters = {"M": 10, "N": 10, "steps": 600, "robots": 5, "boxes": 15}
    model = RobotModel(parameters)
    model.setup()
    # There's no need for model.run() here, since we only depend on the steps() function

    p = threading.Thread(target=run, args=tuple(), daemon=True)
    p.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped.")
