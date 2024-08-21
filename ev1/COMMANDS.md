## Important Commands

To run this project, you need to have Python 3 installed on your machine. After installing Python 3, you can create a virtual environment using the following command:

```
python3 -m venv .venv
```

After that, you can activate the virtual environment using the following command:

```
. .venv/bin/activate
```

Using the following command, you can install the required packages:

```
pip install -r requirements.txt
```

After initializing the virtual environment, run the following command to start the server:

```
python -m flask --app main run
```