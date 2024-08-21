import agentpy as ap # type: ignore
import numpy as np


class WealthAgent(ap.Agent):
    def see(self, e):
        per = e.random()
        self.beliefs["partner"] = per

    def next(self):
        for act in self.actions:
            for rule in self.rules:
                if rule(act):
                    return act

    def action(self, act):
        if act is not None:
            act()

    def execute(self):
        self.see(self.model.agents)
        a = self.next()
        self.action(a)

    def setup(self):
        self.wealth = 1
        self.beliefs = {"partner": None}
        self.actions = [self.wealth_transfer]
        self.rules = [self.rule_1]

    def rule_1(self, act):
        rule_validation = [False, False, False]
        if self.wealth > 0:
            rule_validation[0] = True
        if self.beliefs["partner"] is not None:
            rule_validation[1] = True
        if act == self.wealth_transfer:
            rule_validation[2] = True
        return sum(rule_validation) == 3

    def wealth_transfer(self):
        self.beliefs["partner"].wealth += 1
        self.wealth -= 1


def gini(x):
    x = np.array(x)
    mad = np.abs(np.subtract.outer(x, x)).mean()  # mean absolute difference
    rmad = mad / np.mean(x)  # relative mean absolute difference
    return 0.5 * rmad


class WealthModel(ap.Model):
    def setup(self):
        self.agents = ap.AgentList(self, self.p.agents, WealthAgent)

    def step(self):
        self.agents.execute()

    def update(self):
        self.record("Gini Coefficient", gini(self.agents.wealth))

    def end(self):
        self.agents.record("wealth")


parameters = {
    "agents": 100,
    "steps": 100,
    "seed": 42,
}
