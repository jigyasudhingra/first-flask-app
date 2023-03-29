from flask import Flask
from helper import home

app = Flask(__name__)

employees = [
    {
        'name': 'Param',
        'college': 'Motilal Nehru'
    },
]

# NOTE: use different function name for each of the route 

@app.route("/")
def hello():
    return "Welcome to new flask app"

@app.route("/employees", methods=['PUT'])
def index():
    return home(employees)