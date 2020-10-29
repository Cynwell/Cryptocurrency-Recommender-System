from random import choice, randint, seed
from copy import copy
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score

from price_crawler import update_token, build_features


# {label name: number of period into the future}
TARGET = {'1D-price': 1, '3D-price': 3, '7D-price': 7}

# Number of trials
TRIAL = 500

# TA features to be used
TA_FEATURES = ['ROC', 'MOM', 'EMA']

ROLL_RANGE = [1, 2, 3, 4, 5, 6, 7, 8]           # How many previous periods to be considered
DELTA_RANGE = ['1D', '12H', '6H', '3H']         # Possible duration of each period
MODEL_RANGE = [DecisionTreeClassifier, LogisticRegression, MLPClassifier]     # Possible Models
NORMALIZE = ['MinMax', 'Normal', 'None']        # Possible data normalization method

CRITERION_RANGE = ['gini', 'entropy']   # Possible way to construct a decision tree
DEPTH_RANGE = [3, 4, 5, 6, 7, 8]        # Possible tree depth when using decision trees
HIDDEN_RANGE = [8, 16, 24, 32, 48]      # Possible hidden size when using MLP

def generate_config():
    seed()
    config = {}
    i = randint(0, 3)

    config['delta'] = DELTA_RANGE[i]
    config['roll'] = choice(ROLL_RANGE)
    config['model'] = choice(MODEL_RANGE)
    config['norm'] = choice(NORMALIZE)
    config['criterion'] = 'NA'
    config['depth'] = -1
    config['hidden'] = -1
    
    target = copy(TARGET)
    for k in target.keys():
        target[k] *= 2 ** i

    if config['model'] == DecisionTreeClassifier:
        config['depth'] = choice(DEPTH_RANGE)
        config['criterion'] = choice(CRITERION_RANGE)
    if config['model'] == MLPClassifier:
        config['hidden'] = choice(HIDDEN_RANGE)

    features = ['open', 'close', 'high', 'low', 'volume'] + [s.lower() for s in TA_FEATURES]
    features += [c + '-r' + str(i + 1) for i in range(config['roll']) for c in features]

    return config, target, features


def log_config(f, cfg, target, result):
    hyper_paramters = ['model', 'delta', 'roll', 'norm', 'hidden', 'depth', 'criterion']
    row = [target] + [str(cfg[p]) for p in hyper_paramters] + result
    line = ','.join(row) + '\n'
    f.write(line)


def train(address, cfg, features, target, log):

    '''
    Input(address <str>, configuration <dict>, features <list>, target <dict>, log <file>) -> list
    This function gives a list of trained model for each time horizon using the configuration above
    '''

    df = build_features(address, freq=cfg['delta'], ta_list=TA_FEATURES, ys=target, roll=cfg['roll'])
    X = df[features]
    model = cfg['model']
    output_models = []

    if cfg['norm'] == 'MinMax':
        X = (X - X.min()) / (X.max() - X.min())
    if cfg['norm'] == 'Normal':
        X = (X - X.mean()) / X.std()
    
    for t in target.keys():
        
        if model == DecisionTreeClassifier:
            depth = cfg['depth']
            criterion = cfg['criterion']
            m = model(max_depth=depth, criterion=criterion)
        elif model == MLPClassifier:
            hidden = cfg['hidden']
            m = model(hidden_layer_sizes=(hidden, 2), max_iter=500, solver='sgd')
        else:
            m = model(max_iter=500, solver='sag')
        
        y = df[t]
        scores = cross_val_score(m, X, y, cv=6)
        result = [str(scores.mean()), str(scores.std())]
        log_config(log, cfg, t, result)
        output_models.append(m)
    
    return output_models


if __name__ == '__main__':
    address = '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'
    update_token(address)
    file_name = address + '_tuning.csv'
    log = open('price_data/' + file_name, 'a')
    try:
        for i in range(TRIAL):
            cfg, target, features = generate_config()
            train(address, cfg, features, target, log)
            print(i + 1, 'trials completed')
    except KeyboardInterrupt:
        log.close()
        
    address = '0x514910771af9ca656af840dff83e8264ecf986ca'
    update_token(address)
    file_name = address + '_tuning.csv'
    log = open('price_data/' + file_name, 'a')
    try:
        for i in range(TRIAL):
            cfg, target, features = generate_config()
            train(address, cfg, features, target, log)
            print(i + 1, 'trials completed')
    except KeyboardInterrupt:
        log.close()