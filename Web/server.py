import pickle as pk
import json
from threading import Thread

import pandas as pd
from flask import Flask, render_template, request
from recommender_module.recommend import recommend

with open('data/user_array.pkl', 'rb') as usr:
    USER_ARRAY = pk.load(usr)


TOKENS = pd.read_csv('data/tokens.csv')
TOKENS['Address'] = TOKENS['Address'].str.lower()
TOKENS.set_index('Address', inplace=True)

WORKERS = {}
PROFILES = {}

app = Flask(__name__, static_folder='static')


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/<path:target>')
def resource(target):
    return app.send_static_file(target)


@app.route('/survey', methods=['POST'])
def survey():
    if request.form['haveAddress'] == 'true':
        address = request.form['address']
        uid = request.form['id']
        worker = Thread(target=recommend, args=[uid, address, PROFILES, USER_ARRAY, TOKENS.index])
        WORKERS[uid] = worker
        worker.start()
        greet = 'We got your Address. Lets see your Investment Preference'
    else:
        greet = 'No Address is fine. Lets see your Investment Preference'
    return render_template('survey.html', message=greet)


@app.route('/result', methods=['POST'])
def result():
    code = ['r1', 'r2', 'r3', 'r4', 'r5']
    uid = request.form['id']
    output = {}
    if (uid in WORKERS) and ('surveyOnly' not in request.form):
        worker = WORKERS[uid]
        worker.join()
        profile = PROFILES[uid]
        if profile.status != 'Ok':
            return render_template('error.html', message=profile.status)
        tokens, scores = profile.user_knn_results
        for c, t in zip(code, tokens):
            output[c] = TOKENS.loc[t, 'Name']
            output[c + '-des'] = TOKENS.loc[t, 'Description']
            output[c + '-1d'] = 'Up'
            output[c + '-3d'] = 'Down'
            output[c + '-7d'] = 'Up'
    else:
        output['r1'] = 'Maker'
        output['r1-des'] = 'Maker is a very popular coin'
        output['r1-1d'] = 'Up'
        output['r1-3d'] = 'Down'
        output['r1-7d'] = 'Up'
    
    return render_template('result.html', data=json.dumps(output))


if __name__ == '__main__':
    app.run(port=80, host='0.0.0.0')