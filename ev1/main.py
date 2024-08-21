from flask import Flask, jsonify
from agentClasses import WealthModel, parameters, gini

app = Flask(__name__)


# Initialize the model and results globally
model = WealthModel(parameters)
results = model.run()

@app.route("/")
def hello_word():
    return "<h1> Hello, world </h1>"


@app.route("/wealth")
def wealth():
    wealth_distribution = [agent.wealth for agent in model.agents]
    gini_coefficient = gini(wealth_distribution)
    return jsonify(
        {
            "wealth_distribution": wealth_distribution,
            "gini_coefficient": gini_coefficient,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
    # https://localhost:3000
    
