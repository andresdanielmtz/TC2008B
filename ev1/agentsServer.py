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
        # self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))
        self.wfile.write(str(response_data).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        # post_data = self.rfile.read(content_length)
        post_data = json.loads(self.rfile.read(content_length))
        # logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
        # str(self.path), str(self.headers), post_data.decode('utf-8'))
        logging.info(
            "POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
            str(self.path),
            str(self.headers),
            json.dumps(post_data),
        )

        # Aquí se procesa lo el cliente ha enviado, y se construye una respuesta.
        response_data = post_response(post_data)

        self._set_response()
        # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        self.wfile.write(str(response_data).encode("utf-8"))


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


def post_response(data):
    robot_id = data.get("id")
    new_position = data.get("position")
    direction = data.get("direction")

    # Find the robot by ID
    robot = next((r for r in model.robots if r.id == robot_id), None)
    
    if robot is None:
        return json.dumps({"error": "Robot not found"}), 404

    # Update the robot’s position and direction
    if new_position:
        robot.model.grid.move_by(robot, tuple(new_position))  # Move robot to new position
    if direction:
        robot.direction = tuple(direction)  # Update direction

    robot.last_action = "moved"  # Example action, can be customized

    # Perform a step in the simulation
    model.step()

    # Prepare the response data
    response = {
        "robot_actions": [
            {
                "id": robot.id,
                "action": robot.last_action,
                "position": model.grid.positions[robot],
                "direction": robot.direction,
                "last_action": robot.last_action,
            }
            for robot in model.robots
        ],
        "box_positions": [model.grid.positions[box] for box in model.boxes],
    }

    return json.dumps(response)


def get_response():
    response = {
        "robot_positions": [
            {
                "id": robot.id,
                "position": model.grid.positions[robot],
                "direction": robot.direction,
                "last_action": robot.last_action,  # Include last movement action
            }
            for robot in model.robots
        ],
        "box_positions": [model.grid.positions[box] for box in model.boxes],
    }
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
        pass

    def add_box(self):
        if self.boxStack < 3:
            self.boxStack += 1
            self.stacked = True
        else:
            self.stacked = False
            print("Stack is full")

    def step(self):
        if self.first_step:
            self.pos = self.model.grid.positions[self]
            self.first_step = False
        pass

    def remove_box(self):
        if self.boxStack > 0:
            self.boxStack -= 1
            if self.boxStack < 2:
                self.stacked = False

    def update(self):
        pass

    def end(self):
        pass


class Robot(ap.Agent):
    def see(self, e):
        self.per = []
        current_pos = e.positions[self]

        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        np.random.shuffle(directions)

        for direction in directions:
            neighbor_pos = (
                current_pos[0] + direction[0],
                current_pos[1] + direction[1],
            )

            if 0 <= neighbor_pos[0] < e.shape[0] and 0 <= neighbor_pos[1] < e.shape[1]:
                box = next((b for b in self.model.boxes if b.pos == neighbor_pos), None)
                if box:
                    self.per.append(
                        Box(
                            has_place=Place(has_position=str(neighbor_pos)),
                            boxStack=box.boxStack,
                        )
                    )
                else:
                    self.per.append(
                        Box(has_place=Place(has_position=str(neighbor_pos)), boxStack=0)
                    )

    def next(self):
        action_taken = False
        for act in self.actions:
            for rule in self.rules:
                if rule(act):
                    print(f"Robot {self} executing action {act.__name__}.")
                    self.last_action = act.__name__
                    act()
                    action_taken = True
                    break
            if action_taken:
                break

        if not action_taken:
            print(f"Robot {self} executing random move.")
            self.move_random()

        # REGLAS PARA GRAB

    def rule_grabBox(self, act):
        validador = [False, False, False]

        for boxes in self.model.boxes:
            if (
                boxes.pos == self.model.grid.positions[self]
                and boxes.boxStack == 1
                and not boxes.stacked
            ):
                validador[0] = True

        if not self.carryingBox:
            validador[1] = True

        if act == self.grabBox:
            validador[2] = True

        return sum(validador) == 3

    def rule_mov_N_grab(self, act):
        validador = [False, False, False]
        if (
            self.per
            and eval(self.per[0].has_place.has_position)[0]
            == self.model.grid.positions[self][0] - 1
        ):
            if self.per[0].boxStack == 1 or (
                not self.carryingBox and self.per[0].boxStack == 0
            ):
                validador[0] = True
        if not self.carryingBox:
            validador[1] = True
        if act == self.move_N:
            validador[2] = True
        return sum(validador) == 3

    def rule_mov_E_grab(self, act):
        validador = [False, False, False]
        if (
            len(self.per) > 1
            and eval(self.per[1].has_place.has_position)[1]
            == self.model.grid.positions[self][1] + 1
        ):
            if self.per[1].boxStack == 1 or (
                not self.carryingBox and self.per[1].boxStack == 0
            ):
                validador[0] = True
        if not self.carryingBox:
            validador[1] = True
        if act == self.move_E:
            validador[2] = True
        return sum(validador) == 3

    def rule_mov_S_grab(self, act):
        validador = [False, False, False]
        if (
            len(self.per) > 2
            and eval(self.per[2].has_place.has_position)[0]
            == self.model.grid.positions[self][0] + 1
        ):
            if self.per[2].boxStack == 1 or (
                not self.carryingBox and self.per[2].boxStack == 0
            ):
                validador[0] = True
        if not self.carryingBox:
            validador[1] = True
        if act == self.move_S:
            validador[2] = True
        return sum(validador) == 3

    def rule_mov_W_grab(self, act):
        validador = [False, False, False]
        if (
            len(self.per) > 3
            and eval(self.per[3].has_place.has_position)[1]
            == self.model.grid.positions[self][1] - 1
        ):
            if self.per[3].boxStack == 1 or (
                not self.carryingBox and self.per[3].boxStack == 0
            ):
                validador[0] = True
        if not self.carryingBox:
            validador[1] = True
        if act == self.move_W:
            validador[2] = True
        return sum(validador) == 3

    def rule_mov_buscar_grabBox(self, act):

        # Validador de regla
        validador = [False, False, False]

        # Proposición 1: Si no hay box en el entorno

        if len(self.per) <= 0:
            validador[0] = True

        if self.carryingBox == False:
            validador[1] = True

        # Proposición 2: Si la acción es la de moverse aleatoriamente
        if act == self.move_random:
            validador[2] = True

        return sum(validador) == 3

    # REGLAS PARA STACK

    def rule_stackBox(self, act):
        validador = [False, False, False]

        for boxes in self.model.boxes:
            if boxes.pos == self.model.grid.positions[self] and 1 <= boxes.boxStack < 5:
                validador[0] = True

        if self.carryingBox:
            validador[1] = True

        if act == self.stackBox:
            validador[2] = True

        return sum(validador) == 3

    def rule_mov_N_stackBox(self, act):
        # Validador de regla
        validador = [False, False, False]

        # Proposición 1: Si hay box en la posición Norte
        for boxes in self.per:
            if (
                eval(boxes.has_place.has_position)[0]
                == self.model.grid.positions[self][0] - 1
                and 1 <= boxes.boxStack < 5
            ):
                validador[0] = True

        if self.carryingBox == True:
            validador[1] = True

        # Proposición 2: Si la acción es la de moverse hacia el norte
        if act == self.move_N:
            validador[2] = True

        return sum(validador) == 3

    def rule_mov_S_stackBox(self, act):
        # Validador de regla
        validador = [False, False, False]

        # Proposición 1: Si hay box en la posición Norte
        for boxes in self.per:
            if (
                eval(boxes.has_place.has_position)[0]
                == self.model.grid.positions[self][0] + 1
                and 1 <= boxes.boxStack < 5
            ):
                validador[0] = True

        if self.carryingBox == True:
            validador[1] = True

        # Proposición 2: Si la acción es la de moverse hacia el sur
        if act == self.move_S:
            validador[2] = True

        return sum(validador) == 3

    def rule_mov_E_stackBox(self, act):
        # Validador de regla
        validador = [False, False, False]

        # Proposición 1: Si hay box en la posición Norte
        for boxes in self.per:
            if (
                eval(boxes.has_place.has_position)[0]
                == self.model.grid.positions[self][1] + 1
                and 1 <= boxes.boxStack < 5
            ):
                validador[0] = True

        if self.carryingBox == True:
            validador[1] = True

        # Proposición 2: Si la acción es la de moverse hacia el este
        if act == self.move_E:
            validador[2] = True

        return sum(validador) == 3

    def rule_mov_W_stackBox(self, act):
        # Validador de regla
        validador = [False, False, False]

        # Proposición 1: Si hay box en la posición Norte
        for boxes in self.per:
            if (
                eval(boxes.has_place.has_position)[0]
                == self.model.grid.positions[self][1] - 1
                and 1 <= boxes.boxStack < 5
            ):
                validador[0] = True

        if self.carryingBox == True:
            validador[1] = True

        # Proposición 2: Si la acción es la de moverse hacia el sur
        if act == self.move_W:
            validador[2] = True

        return sum(validador) == 3

    def rule_buscar_stackBox(self, act):
        validador = [False, False]

        if self.carryingBox == True and all(box.boxStack != 1 for box in self.per):
            validador[0] = True

        if act == self.move_random:
            validador[1] = True

        return sum(validador) == 2

    # SIMULACIÓN DE AGENTE

    def setup(self):
        """
        Función de inicialización
        """

        self.agentType = 0  # Tipo de agente
        self.carryingBox = False
        self.direction = (1, 0)  # Dirección inicial
        self.previous_position = None
        self.last_positions = []
        self.last_action = "setup"
        # Acciones del agente

        self.frustration = 0
        self.frustration_threshold = 5  # Adjust as needed
        self.actions = (
            self.move_N,
            self.move_S,
            self.move_E,
            self.move_W,
            self.move_random,
            self.grabBox,
            self.stackBox,
        )
        # Reglas del agente
        self.rules = (
            self.rule_grabBox,
            self.rule_mov_N_grab,
            self.rule_mov_S_grab,
            self.rule_mov_E_grab,
            self.rule_mov_W_grab,
            self.rule_mov_buscar_grabBox,
            self.rule_mov_N_stackBox,
            self.rule_mov_S_stackBox,
            self.rule_mov_E_stackBox,
            self.rule_mov_W_stackBox,
            self.rule_stackBox,
            self.rule_buscar_stackBox,
        )
        pass

    def check_if_stuck(self):
        if len(set(self.last_positions)) == 1 and len(self.last_positions) >= 5:
            self.move_random()
            self.last_positions.clear()

    def step(self):
        current_pos = self.model.grid.positions[self]
        if current_pos == self.previous_position:
            self.frustration += 1
        else:
            self.frustration = 0

        if self.frustration >= self.frustration_threshold:
            self.move_random()
            self.frustration = 0
        else:
            self.see(self.model.grid)
            self.next()

        self.previous_position = current_pos

    def update(self):
        pass

    def end(self):
        pass

        # ACCIONES

    def move_N(self):
        """
        Función de movimiento hacia el norte
        """
        self.direction = (-1, 0)  # Cambio de dirección
        self.forward()  # Caminar un paso hacia adelante

    def move_S(self):
        """
        Función de movimiento hacia el sur
        """
        self.direction = (1, 0)  # Cambio de dirección
        self.forward()  # Caminar un paso hacia adelante

    def move_E(self):
        """
        Función de movimiento hacia el este
        """
        self.direction = (0, 1)  # Cambio de dirección
        self.forward()  # Caminar un paso hacia adelante

    def move_W(self):
        """
        Función de movimiento hacia el oeste
        """
        self.direction = (0, -1)  # Cambio de dirección
        self.forward()  # Caminar un paso hacia adelante

    def check_collision(self, new_pos):
        return any(
            self.model.grid.positions[agent] == new_pos
            for agent in self.model.robots
            if agent != self
        )

    def move_random(self):
        directions = [(0, 1), (-1, 0), (1, 0), (0, -1)]  # Up, Right, Down, Left
        np.random.shuffle(directions)

        self.direction = random.choice(directions)
        least_crowded_direction = None
        least_crowded_count = float("inf")

        for direction in directions:
            new_pos = (
                self.model.grid.positions[self][0] + direction[0],
                self.model.grid.positions[self][1] + direction[1],
            )

            # Correct way to check if the new position is within grid bounds
            if 0 <= new_pos[0] < self.p.M and 0 <= new_pos[1] < self.p.N:
                nearby_agents = sum(
                    1
                    for agent in self.model.robots
                    if self.model.grid.positions[agent] == new_pos
                )
                if nearby_agents < least_crowded_count:
                    least_crowded_count = nearby_agents
                    least_crowded_direction = direction

        if least_crowded_direction:
            self.model.grid.move_by(self, least_crowded_direction)

    def forward(self):
        new_pos = (
            self.model.grid.positions[self][0] + self.direction[0],
            self.model.grid.positions[self][1] + self.direction[1],
        )

        if not self.check_collision(new_pos):
            print(
                f"Robot at {self.model.grid.positions[self]} moving to {new_pos} with direction {self.direction}"
            )
            self.model.grid.move_by(self, self.direction)
        else:
            print(
                f"Collision avoided at {new_pos} by robot at {self.model.grid.positions[self]}"
            )

    def turn(self):
        """
        Función de rotación
        """
        if self.direction == (-1, 0):
            self.direction = (0, 1)  # Hacia Este
        elif self.direction == (0, 1):
            self.direction = (1, 0)  # Hacia Sur
        elif self.direction == (1, 0):
            self.direction = (0, -1)  # Hacia Oeste
        elif self.direction == (0, -1):
            self.direction = (-1, 0)  # Hacia Norte
        pass

    def grabBox(self):
        if not self.carryingBox:
            current_position = self.model.grid.positions[self]
            for box in self.model.boxes[:]:
                if box.pos == current_position and box.boxStack == 1:
                    box.remove_box()
                    if box.boxStack == 0:
                        self.model.grid.remove_agents(box)
                        self.model.boxes.remove(box)
                    self.carryingBox = True
                    print(f"Robot at {current_position} grabbed a box.")
                    return

    def stackBox(self):
        if self.carryingBox:
            current_position = self.model.grid.positions[self]

            existing_box = next(
                (box for box in self.model.boxes if box.pos == current_position), None
            )

            if existing_box:
                if existing_box.boxStack < 5:
                    existing_box.add_box()
                    self.carryingBox = False
                    print(
                        f"Robot at {current_position} stacked its box. "
                        f"Pile now has {existing_box.boxStack} boxes."
                    )
                    return True
                else:
                    print(
                        f"Robot at {current_position} cannot stack, pile has {existing_box.boxStack} boxes."
                    )
            else:
                new_box = Box(pos=current_position, model=self.model)
                new_box.boxStack = 2
                self.model.grid.add_agents(new_box)
                self.model.boxes.append(new_box)
                self.carryingBox = False
                print(f"Robot at {current_position} created a new stack.")
                return True
        return False


class RobotModel(ap.Model):
    def setup(self):

        self.robots = ap.AgentList(self, self.p.robots, Robot)
        self.boxes = ap.AgentList(self, self.p.boxes, BoxPile)

        self.grid = ap.Grid(self, (self.p.M, self.p.N), track_empty=True)

        self.grid.add_agents(self.robots, random=True, empty=True)
        self.grid.add_agents(self.boxes, random=True, empty=True)

        pass

    def step(self):
        self.boxes.step()
        self.robots.step()

        pass

    def update(self):
        pass

    def end(self):
        pass


#


#
#


# ==================================Main===========================

if __name__ == "__main__":
    from sys import argv
    import time

    global model  # so we can use it anywhere else
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
