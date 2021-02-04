from random import choice, randint, seed
from copy import copy
from os import path
import warnings
warnings.filterwarnings("ignore")

import torch
from torch import nn

from price_crawler import update_token, build_features
from rnn_utils import get_model, pd_to_tensor


# [<Prediction Interval>-<Feature Name>]
TARGET = ['1D-close', '3D-close', '7D-close']

# Number of trials
TRIAL = 10

# TA features to be used
TA_FEATURES = ['ROC', 'MOM', 'EMA', 'SMA', 'VAR', 'MACD', 'ADX', 'RSI']

SIZE_RANGE = [32, 64, 96]                     # Size of hidden layers within the model
DELTA_RANGE = ['24H', '12H', '6H', '3H']      # Possible duration of each period
MODEL_RANGE = ['GRU', 'LSTM', 'RNN']          # Possible Models
NORMALIZE = ['MinMax', 'Normal']              # Possible data normalization method
LR_RANGE = [0.01, 0.001]                      # Possible learning rates


def generate_config():
    seed()
    config = {}

    config['roll'] = 1
    config['delta'] = choice(DELTA_RANGE)
    config['model'] = choice(MODEL_RANGE)
    config['norm'] = choice(NORMALIZE)
    config['hidden'] = choice(SIZE_RANGE)
    config['lr'] = choice(LR_RANGE)
    
    target = copy(TARGET)

    features = ['open', 'close', 'high', 'low', 'volume'] + [s.lower() for s in TA_FEATURES]
    features += [c + '-r' + str(i + 1) for i in range(config['roll']) for c in features]

    return config, target, features


def to_csv_lines(cfg, target, train_acc, val_acc):
    lines = []
    hyper_paramters = ['model', 'delta', 'norm', 'hidden', 'lr']
    for y, t, v in zip(target, train_acc, val_acc):
        row = [y] + [str(cfg[p]) for p in hyper_paramters] + [str(t), str(v)]
        line = ','.join(row) + '\n'
        lines.append(line)
    return lines


def train(address, cfg, target):

    '''
    Input(address <str>, configuration <dict>, features <list>, target <dict>, log <file>) -> list
    This function gives a list of trained model for each time horizon using the configuration above
    '''

    X, y = build_features(address, freq=cfg['delta'], ta_list=TA_FEATURES, ys=target, roll=cfg['roll'])
    cfg['input'] = len(X.columns)
    rnn = get_model(cfg)
    output_models = []

    if cfg['norm'] == 'MinMax':
        X = (X - X.min()) / (X.max() - X.min())
    if cfg['norm'] == 'Normal':
        X = (X - X.mean()) / X.std()

    cut = int(len(X) * 0.8)
    X, y = pd_to_tensor(X, y)
    train_x, train_y = X[:cut], y[:cut]
    val_x, val_y = X[cut:], y[cut:]

    optim = torch.optim.Adam(rnn.parameters(), lr=cfg['lr'])
    criterion = nn.BCELoss()
    i = 1
    overfit = 0
    previous_loss = 999
    while True:
        optim.zero_grad()
        train_pred = rnn(train_x)
        loss = criterion(train_pred, train_y)
        loss.backward()
        optim.step()
        val_pred = rnn(val_x)
        val_loss = criterion(val_pred, val_y)
        if val_loss > previous_loss:
            overfit += 1
        else:
            overfit = 0
        if overfit > 3:
            break
        previous_loss = val_loss
        i += 1

    train_pred = rnn(train_x)
    train_acc = ((train_pred > 0.5) == train_y).float()
    train_acc = torch.mean(train_acc, dim=0).tolist()[0]
    val_pred = rnn(val_x)
    val_acc = ((val_pred > 0.5) == val_y).float()
    val_acc = torch.mean(val_acc, dim=0).tolist()[0]
    lines = to_csv_lines(cfg, target, train_acc, val_acc)
    return rnn, lines


if __name__ == '__main__':
    # Number of trials
    TRIAL = 10

    address = '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2'
    update_token(address)
    csv_lines = []
    file_name = address + '_rnn.csv'
    if path.exists('tuning_logs/' + file_name):
        log = open('tuning_logs/' + file_name, 'a')
    else:
        log = open('tuning_logs/' + file_name, 'w')
        log.write('TARGET, MODEL, DELTA, NORM, HIDDEN, LR, TRAIN, VAL\n')
    try:
        for i in range(TRIAL):
            cfg, target, features = generate_config()
            model, lines = train(address, cfg, target)
            csv_lines += lines
            print(i + 1, 'trials completed')
        log.writelines(csv_lines)
        log.close()
    except KeyboardInterrupt:
        log.writelines(csv_lines)
        log.close()