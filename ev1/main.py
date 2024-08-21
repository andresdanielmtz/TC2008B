from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_word():
    return "<h1> Ferunini si fuera chila </h1>"


@app.route("/wealth")
def wealth():
    pass
