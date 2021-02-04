from random import choice, randint, seed
from copy import copy
from os import path
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score
from joblib import Parallel, delayed

from price_crawler_minute import retrieve_data, build_features


# [<Prediction Interval>-<Feature Name>]
TARGET = ['1D-close', '3D-close', '7D-close']

# Number of trials
TRIAL = 10

# TA features to be used
TA_FEATURES = ['ROC', 'MOM', 'EMA', 'SMA', 'VAR', 'MACD', 'ADX', 'RSI']

ROLL_RANGE = [1, 2, 4, 8]                             # How many previous periods to be considered
DELTA_RANGE = ['12H', '6H', '3H', '1H', '30min']      # Possible duration of each period
MODEL_RANGE = [DecisionTreeClassifier]                # Possible Models
NORMALIZE = ['MinMax', 'Normal', 'None']              # Possible data normalization method

CRITERION_RANGE = ['gini', 'entropy']   # Possible way to construct a decision tree
DEPTH_RANGE = [3, 4, 5, 6, 7, 8]        # Possible tree depth when using decision trees
HIDDEN_RANGE = [8, 16, 24, 32, 48]      # Possible hidden size when using MLP    # [<Prediction Interval>-<Feature Name>]


def generate_config():
    seed()
    config = {}

    config['delta'] = choice(DELTA_RANGE)
    config['roll'] = choice(ROLL_RANGE)
    config['model'] = choice(MODEL_RANGE)
    config['norm'] = choice(NORMALIZE)
    config['criterion'] = 'NA'
    config['depth'] = -1
    config['hidden'] = -1
    
    target = copy(TARGET)

    if config['model'] == DecisionTreeClassifier:
        config['depth'] = choice(DEPTH_RANGE)
        config['criterion'] = choice(CRITERION_RANGE)
    if config['model'] == MLPClassifier:
        config['hidden'] = choice(HIDDEN_RANGE)

    features = ['open', 'close', 'high', 'low', 'volume'] + [s.lower() for s in TA_FEATURES]
    features += [c + '-r' + str(i + 1) for i in range(config['roll']) for c in features]

    return config, target, features


def to_csv_line(cfg, target, result):
    hyper_paramters = ['model', 'delta', 'roll', 'norm', 'hidden', 'depth', 'criterion']
    row = [target] + [str(cfg[p]) for p in hyper_paramters] + result
    line = ','.join(row) + '\n'
    return line


def generate_config_and_train(token, i):
    cfg, target, features = generate_config()

    df = retrieve_data(token)
    X, y = build_features(df, freq=cfg['delta'], ta_list=TA_FEATURES, ys=target, roll=cfg['roll'])
    model = cfg['model']
    output_models = []
    results = []

    if cfg['norm'] == 'MinMax':
        X = (X - X.min()) / (X.max() - X.min())
    if cfg['norm'] == 'Normal':
        X = (X - X.mean()) / X.std()
    
    for label, t in y.iteritems():

        if model == DecisionTreeClassifier:
            depth = cfg['depth']
            criterion = cfg['criterion']
            m = model(max_depth=depth, criterion=criterion)
        elif model == MLPClassifier:
            hidden = cfg['hidden']
            m = model(hidden_layer_sizes=(hidden, 2), max_iter=500, solver='sgd')
        else:
            m = model(max_iter=500, solver='sag')

        scores = cross_val_score(m, X, t, cv=6)
        result = [str(scores.mean()), str(scores.std())]
        result = to_csv_line(cfg, label, result)
        output_models.append(m)
        results.append(result)

    return output_models, results


if __name__ == '__main__':
    token = 'leousd.csv'
    file_dir = 'tuning_logs/' + token + '_tuning.csv'
    if path.exists(file_dir):
        log = open(file_dir, 'a')
    else:
        log = open(file_dir, 'w')
        log.write('TARGET, MODEL, DELTA, ROLL, NORM, HIDDEN, DEPTH, CRITERION, SCORE, STD\n')
    outputs = Parallel(n_jobs=4)(delayed(generate_config_and_train)(token, i) for i in range(TRIAL))
    csv_lines = []
    for models, results in outputs:
        csv_lines += results
    log.writelines(csv_lines)
    log.close()