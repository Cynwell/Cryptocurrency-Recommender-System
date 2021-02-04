import torch
from torch import nn

import numpy as np

class Model(nn.Module):

    def __init__(self, input_size, size, rnn_type):
        super(Model, self).__init__()
        self.embed = nn.Linear(input_size, size)
        self.output = nn.Linear(size, 3)
        self.rnn_type = rnn_type
        self.size = size
        if rnn_type == 'LSTM':
            self.rnn = nn.LSTM(input_size=size, hidden_size=size)
        if rnn_type == 'GRU':
            self.rnn = nn.GRU(input_size=size, hidden_size=size)
        if rnn_type == 'RNN':
            self.rnn = nn.RNN(input_size=size, hidden_size=size)


    def forward(self, x):
        x = torch.relu(self.embed(x))
        if self.rnn_type == 'LSTM':
            h_0 = torch.zeros([1, 1, self.size])
            c_0 = torch.zeros([1, 1, self.size])
            x, (h, c) = self.rnn(x, (h_0, c_0))
        if self.rnn_type == 'GRU':
            h_0 = torch.zeros([1, 1, self.size])
            x, h = self.rnn(x, h_0)
        if self.rnn_type == 'RNN':
            x, h = self.rnn(x)
        y = torch.sigmoid(self.output(x))
        return y


def get_model(config):
    return Model(config['input'], config['hidden'], config['model'])


def pd_to_tensor(x, y):
    xx = x.to_numpy(dtype=np.float32)
    yy = y.to_numpy(dtype=np.float32)
    xx = torch.tensor(xx).unsqueeze(1)
    yy = torch.tensor(yy).unsqueeze(1)
    return xx, yy
