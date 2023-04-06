from flask import Flask
from helper import home
from fundamentalanalysis import fundamentalAnalysis

app = Flask(__name__)

employees = [
    {
        'name': 'Param',
        'college': 'Motilal Nehru'
    },
]

# NOTE: use different function name for each of the route 
# Takes plYears, and threshold for now
@app.route("/fundamental")
def getFundamentalAnalysis():
    return fundamentalAnalysis()

@app.route("/employees", methods=['PUT'])
def index():
    return home(employees)