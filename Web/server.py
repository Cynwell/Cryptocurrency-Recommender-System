import pickle as pk
import json
from threading import Thread

import pandas as pd
from flask import Flask, render_template, request
from recommender_module.recommend import recommend

# Load user transaction data 
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
        worker = Thread(target=recommend, args=[uid, address, PROFILES, USER_ARRAY, TOKENS])
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
        tokens = profile.user_knn_results
        predictions = profile.predict_results
        for c, t, i in zip(code, tokens, range(5)):
            output[c] = TOKENS.loc[t, 'Name']
            output[c + '-des'] = TOKENS.loc[t, 'Description']
            output[c + '-1d'] = 'Up' if predictions[i][0] > 0 else 'Down'
            output[c + '-3d'] = 'Up' if predictions[i][1] > 0 else 'Down'
            output[c + '-7d'] = 'Up' if predictions[i][2] > 0 else 'Down'
    else:
        output['r1'] = 'Maker'
        output['r1-des'] = 'Maker is a very popular coin'
        output['r1-1d'] = 'Up'
        output['r1-3d'] = 'Down'
        output['r1-7d'] = 'Up'
    
    return render_template('result.html', data=json.dumps(output))


if __name__ == '__main__':
    app.run(port=80, host='0.0.0.0')