from flask import request

def home(employees: object):
    print('----',request.data, request.json, request.form)
    # 1. json/get_json() - You can receive the body of API as 
    # an dictionary, and use like dictionary to perform
    # the operation
    # ---------------------------------------------
    # 2. There are other things which you can access from request
    # --- request.data and request.form ---
    req = request.get_json()
    employee = {
        'name': req['name'],
        'college': req['college']
    }
    return [*employees ,employee]