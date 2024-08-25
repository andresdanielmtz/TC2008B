# Important Commands

To run this project, you need to have Python 3 installed on your machine. After installing Python 3, follow these steps:

## Create a virtual environment:

`python3 -m venv .venv`

## Activate the virtual environment:

On MacOS or Linux:

```. .venv/bin/activate```

or on Windows:

```.venv\Scripts\activate```

## Install the required packages:

```pip install -r requirements.txt```

## Run the server:

```python agentsServer.py```

This will start the server, which includes both the robot simulation and the wealth agent model.

## Accessing the Simulations

### Robot Simulation:

Send GET or POST requests to http://localhost:8585/robot

### Wealth Agent Model:

Access wealth distribution data at http://localhost:8585/wealth

### Additional Information

- The server runs on port 8585 by default.
- The robot simulation uses a grid of size 10x10 with 5 robots and 15 boxes.
- The wealth agent model simulates 100 agents over 100 steps.

For more detailed information about the API and available endpoints, please refer to the `API.md` file.