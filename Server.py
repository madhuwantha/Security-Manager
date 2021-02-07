from flask import Flask, request
import requests, json
import ast

from Env import Env
from MainServer import FLModel
from datetime import datetime


app = Flask(__name__)
env = Env()


@app.route(env.get(key="homeUrl"))
def hello():
    return "Security manager running !"


@app.route(env.get(key="getClientStatusUrl"), methods=['GET', 'POST'])
def client_status():
    if request.method == 'POST':
        client_port = request.json['client_id']
        client_host = request.json['client_host']

        isClientExist = check_if_string_in_file('clients.txt', client_host)

        if isClientExist:
            return "Client already exist "

        with open('clients.txt', 'a+') as f:
            f.write("http://" + client_host + ':' + str(client_port) + '/\n')

        print(client_port)

        if client_port:
            serverack = {'server_ack': '1'}
            # response = requests.post( url, data=json.dumps(serverack), headers={'Content-Type': 'application/json'} )
            return str(serverack)
        else:
            return "Client status not OK!"
    else:
        return "Client GET request received!"


@app.route(env.get(key="getModelUrl"), methods=['POST'])
def get_model():
    if request.method == 'POST':
        file = request.files['model'].read()
        fname = request.files['json'].read()
        # cli = request.files['id'].read()

        fname = ast.literal_eval(fname.decode("utf-8"))
        cli = fname['id'] + '\n'
        fname = fname['fname']

        now = datetime.now()
        now = str(now).replace(" ", "-").replace(":", "-").replace(".", "-")

        wfile = open("ClientModels/" + str(fname).split(".")[0] + "-" + now + "." + str(fname).split(".")[1], 'wb')
        wfile.write(file)

        return "Model received!"
    else:
        return "No file received!"


@app.route(env.get(key="modelAggUrl"))
def perform_model_aggregation():
    try:
        fl = FLModel()
        fl.modelAggregation()
        return {'status': True, 'message': "Model aggregation done!\nGlobal model written to persistent storage."}
    except:
        return {'status': False, 'message': "Model aggregation Failed!"}


@app.route(env.get(key="sendModelUrl"))
def send_agg_to_clients():
    clients = ''
    with open('clients.txt', 'r') as f:
        clients = f.read()
    clients = clients.split('\n')

    res = []

    for c in clients:
        print("**********************Trying to send to ", c, "***********************")
        if c != '':
            file = open("PersistentStorage/agg_model.h5", 'rb')
            data = {'fname': 'agg_model.h5'}
            files = {
                'json': ('json_data', json.dumps(data), 'application/json'),
                'model': ('agg_model.h5', file, 'application/octet-stream')
            }

            print("**********************", c, 'agg_model*******************************************************')
            req = requests.post(url=c + 'update-model', files=files)
            print(req)
            print("*********************", req.status_code, "*********************************")

            if req.status_code == 200:
                result = {'status': True, 'client': c, 'message': "Aggregated model sent"}
            else:
                result = {'status': False, 'client': c, 'message': "Aggregated model sent Failed!"}

            res.append(result)

    file = open("clients.txt", "w")
    file.close()
    return str(res)


def check_if_string_in_file(file_name, string_to_search):
    """ Check if any line in the file contains given string """
    # Open the file in read only mode
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search in line:
                return True
    return False


def run():
    app.run(host=str(env.get(key="host")), port=env.get(key="port"), debug=False, use_reloader=True)
