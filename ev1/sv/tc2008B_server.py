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
    vacuum_id = data.get("id")
    position = data.get("position")
    direction = data.get("direction")

    for vacuum in model.vacuums:
        if vacuum.id == vacuum_id:
            vacuum.update_from_unity(
                position, direction
            )  # tbf i dont think this even works to begin with

    model.step()  # very important

    # response data
    response = {
        "vacuum_actions": [
            {
                "id": vacuum.id,
                "action": vacuum.last_action,
                "position": model.grid.positions[vacuum],
                "direction": vacuum.direction,
                "last_action": vacuum.last_action,
            }
            for vacuum in model.vacuums  # Note the correct spelling
        ],
        "dirt_positions": [model.grid.positions[dirt] for dirt in model.dirties],
    }

    return json.dumps(response)


def get_response():

    response = {
        "vacuum_positions": [
            {
                "id": vacuum.id,
                "position": model.grid.positions[vacuum],
                "direction": vacuum.direction,
            }
            for vacuum in model.vacuums  # Note the correct spelling
        ],
        "dirt_positions": [model.grid.positions[dirt] for dirt in model.dirties],
    }
    return json.dumps(response)


# ===================Definición de Agentes y simulación (Model)=================
#
#
onto = get_ontology("file://onto.owl")
with onto:

    class Entity(Thing):
        pass

    class Vaccum(Entity):
        pass

    class Dirt(Entity):
        pass

    class Box(Entity):
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


class VaccumAgent(ap.Agent):

    # Razonamiento
    def see(self, e, data=None):
        """
        Función de percepción
        @param e: entorno grid
        """
        self.per = []
        vecinos = e.neighbors(self, 1)
        
        if data: 
            # Creación de percepto: lista de creencias de agentes Dirt
            for vecino in vecinos:
                self.per.append(
                    Dirt(has_place=Place(has_position=str(e.positions[vecino])))
                )
            return
        # Creación de percepto: lista de creencias de agentes Dirt
        for vecino in vecinos:
            self.per.append(
                Dirt(has_place=Place(has_position=str(e.positions[vecino])))
            )
        pass

    def update_from_unity(self, position, direction):
        self.turn_to(direction)
        self.previous_position = self.model.grid.positions[self]
        self.previous_dirt_count = len(self.model.dirties)
        self.model.grid.move_to(self, position)

    def turn_to(self, direction):
        while self.direction != direction:
            self.turn()

    def next(self):
        """
        Función de razonamiento Deductivo
        """
        # Por cada acción
        for act in self.actions:
            # Por cada regla
            for rule in self.rules:
                # Si la acción es válidad dada la regla
                if rule(act):
                    # Ejecuta la acción
                    act()
        pass

    # REGLAS

    def rule_1(self, act):
        """
        Regla deductiva para limpiar
        @param act: acción a validar
        @return: booleano
        """
        # Validador de regla
        validador = [False, False]

        # Proposición 1: Si hay suciedad en la posición actual
        for dirty in self.model.dirties:
            if dirty.pos == self.model.grid.positions[self]:
                validador[0] = True

        # Proposición 2: Si la acción es la de limpiar
        if act == self.clean:
            validador[1] = True

        return sum(validador) == 2

    def rule_2(self, act):
        """
        Regla deductiva para moverse hacia el norte
        @param act: acción a validar
        @return: booleano
        """

        # Validador de regla
        validador = [False, False]

        # Proposición 1: Si hay suciedad en la posición Norte
        for dirty in self.per:
            if (
                eval(dirty.has_place.has_position)[0]
                == self.model.grid.positions[self][0] - 1
            ):
                validador[0] = True

        # Proposición 2: Si la acción es la de moverse hacia el norte
        if act == self.move_N:
            validador[1] = True

        return sum(validador) == 2

    def rule_3(self, act):
        """
        Regla deductiva para moverse hacia el sur
        @param act: acción a validar
        @return: booleano
        """

        # Validador de regla
        validador = [False, False]

        # Proposición 1: Si hay suciedad en la posición Sur
        for dirty in self.per:
            if (
                eval(dirty.has_place.has_position)[0]
                == self.model.grid.positions[self][0] + 1
            ):
                validador[0] = True

        # Proposición 2: Si la acción es la de moverse hacia el sur
        if act == self.move_S:
            validador[1] = True

        return sum(validador) == 2

    def rule_4(self, act):
        """
        Regla deductiva para moverse hacia el este
        @param act: acción a validar
        @return: booleano
        """

        # Validador de regla
        validador = [False, False]

        # Proposición 1: Si hay suciedad en la posición Este
        for dirty in self.per:
            if (
                eval(dirty.has_place.has_position)[1]
                == self.model.grid.positions[self][1] + 1
            ):
                validador[0] = True

        # Proposición 2: Si la acción es la de moverse hacia el este
        if act == self.move_E:
            validador[1] = True

        return sum(validador) == 2

    def rule_5(self, act):
        """
        Regla deductiva para moverse hacia el oeste
        @param act: acción a validar
        @return: booleano
        """

        # Validador de regla
        validador = [False, False]

        # Proposición 1: Si hay suciedad en la posición Oeste
        for dirty in self.per:
            if (
                eval(dirty.has_place.has_position)[1]
                == self.model.grid.positions[self][1] - 1
            ):
                validador[0] = True

        # Proposición 2: Si la acción es la de moverse hacia el oeste
        if act == self.move_W:
            validador[1] = True

        return sum(validador) == 2

    def rule_6(self, act):
        """
        Regla deductiva para moverse aleatoriamente
        @param act: acción a validar
        @return: booleano
        """

        # Validador de regla
        validador = [False, False]

        # Proposición 1: Si no hay suciedad en el entorno
        if len(self.per) <= 0:
            validador[0] = True

        # Proposición 2: Si la acción es la de moverse aleatoriamente
        if act == self.move_random:
            validador[1] = True

        return sum(validador) == 2

    # SIMULACIÓN DE AGENTE

    def setup(self):
        """
        Función de inicialización
        """

        self.agentType = 0  # Tipo de agente
        self.direction = (-1, 0)  # Dirección inicial
        # Acciones del agente
        self.actions = (
            self.clean,
            self.move_N,
            self.move_S,
            self.move_E,
            self.move_W,
            self.move_random,
        )
        # Reglas del agente
        self.rules = (
            self.rule_1,
            self.rule_2,
            self.rule_3,
            self.rule_4,
            self.rule_5,
            self.rule_6,
        )
        self.last_action = None
        self.previous_position = None

    def get_last_action(self):
        if self.model.grid.positions[self] != self.previous_position:
            return "move"
        elif len(self.model.dirties) < self.previous_dirt_count:
            return "clean"
        else:
            return "none"

    def step(self):
        self.see(self.model.grid)
        self.next()
        self.last_action = self.get_last_action()

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

    def move_random(self):
        """
        Función de movimiento aleatorio
        """
        # Rotaciones aleatorias
        for _ in range(random.randint(0, 4)):
            self.turn()
        self.forward()  # Caminar un paso hacia adelante

    def clean(self):
        """
        Función de limpieza
        """
        # Si hay suciedad en la posición actual
        for dirty in self.model.grid.agents:
            if dirty.agentType == 1:
                if dirty.pos == self.model.grid.positions[self]:
                    self.model.grid.remove_agents(dirty)  # Eliminación de suciedad
                    break  # Romper ciclo
        pass

    def forward(self):
        """
        Función de movimiento
        """
        self.model.grid.move_by(self, self.direction)
        pass

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


class DirtAgent(ap.Agent):

    def setup(self):
        self.agentType = 1
        self.first_step = True
        self.pos = None
        pass

    def step(self):
        if self.first_step:
            self.pos = self.model.grid.positions[self]
            self.first_step = False
        pass

    def update(self):
        pass

    def end(self):
        pass


class VaccumModel(ap.Model):
    def setup(self):
        self.vacuums = ap.AgentList(
            self, self.p.vacuums, VaccumAgent
        )  # Note the correct spelling
        self.dirties = ap.AgentList(self, self.p.dirties, DirtAgent)
        self.grid = ap.Grid(self, (self.p.M, self.p.N), track_empty=True)

        # Assign unique IDs to vacuum cleaners
        for i, vacuum in enumerate(self.vacuums):
            vacuum.p["id"] = f"{i}"

        self.grid.add_agents(self.vacuums, random=True, empty=True)
        self.grid.add_agents(self.dirties, random=True, empty=True)

    def step(self):
        """
        Función paso a paso
        """
        self.vacuums.step()  # Paso de aspiradora
        self.dirties.step()  # Paso de suciedad
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

    parameters = {
        "M": 10,
        "N": 10,
        "vacuums": 5,
        "dirties": 10,
    }
    model = VaccumModel(parameters)
    model.setup()
    # There's no need for model.run() here, since we only depend on the steps() function

    p = threading.Thread(target=run, args=tuple(), daemon=True)
    p.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped.")
