from flask import Flask
from flask import request
from helper import home
from flask_cors import CORS
from fundamentalanalysis import fundamentalAnalysis

app = Flask(__name__)
CORS(app)

employees = [
    {
        'name': 'Param',
        'college': 'Motilal Nehru'
    },
]

# NOTE: use different function name for each of the route 
# Takes plYears, and threshold for now
@app.route("/fundamental", methods=['POST'])
def getFundamentalAnalysis():
    return fundamentalAnalysis()

@app.route("/employees", methods=['PUT'])
def index():
    return home(employees)