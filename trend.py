from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import LinearSVC

from price_crawler import update_token, build_features


TA_FEATURES = ['ROC', 'MOM', 'EMA']  # TA features to be included
ROLLING = 3                          # How many previous periods to be considered
DELTA = '6H'                         # Duration of each period
TARGET = {'12H-price': 2, '1D-price': 4, '3D-price': 12} # {name of label: number of period into the future}
MODEL = DecisionTreeClassifier       # Model used for prediction

# Create the list of feature names
FEATURES = ['open', 'close', 'high', 'low', 'volume'] + [s.lower() for s in TA_FEATURES]
FEATURES += [c + '-r' + str(i + 1) for i in range(ROLLING) for c in FEATURES]

def train(address):
    '''
    Input(address <str>) -> list
    This function gives a list of trained model for each time horizon using the configuration above
    '''
    update_token(address)
    df = build_features(address, freq=DELTA, ta_list=TA_FEATURES, ys=TARGET)
    X = df[FEATURES]
    X_train = X.iloc[:len(X) * 8 // 10, :]
    X_test = X.iloc[len(X) * 8 // 10:, :]
    models = []
    for target in TARGET.keys():
        y = df[target]
        y_train = y.iloc[:len(y) * 8 // 10]
        y_test = y.iloc[len(y) * 8 // 10:]
        m = MODEL(max_depth=5).fit(X_train, y_train)
        test_acc = m.score(X_test, y_test)
        train_acc = m.score(X_train, y_train)
        print(target, 'test accuracy:', test_acc)
        print(target, 'train accuracy:', train_acc)
        models.append(m)
    return models

if __name__ == '__main__':
    ms = train('0x514910771af9ca656af840dff83e8264ecf986ca')
