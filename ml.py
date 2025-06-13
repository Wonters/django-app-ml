import xgboost as xgb
import pandas as pd
from pathlib import Path
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler
from imblearn.over_sampling import SMOTE


def train(df_train:pd.DataFrame, checkpoint: Path):
    """
    Train XGboost model
    :return:
    """
    imputer = SimpleImputer(strategy='median')
    scaler = MinMaxScaler(feature_range=(0, 1))
    weighter = SMOTE(random_state=42)
    y_train = df_train['TARGET']
    X_train = df_train.drop('TARGET', axis=1)
    columns = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
    X_train = X_train.loc[:, columns]
    X_train_imputed = imputer.fit_transform(X_train)
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_train_weighted, y_train_weighted = weighter.fit_resample(X_train_scaled, y_train)
    train_matrix = xgb.DMatrix(X_train_weighted, label=y_train_weighted)
    params_2 = {
        'objective': 'binary:logistic',
        'learning_rate': 0.01,
        'max_depth': 20,
    }
    model = xgb.train(params_2, train_matrix, num_boost_round=100)
    model.save_model(checkpoint)

def predict(checkpoint: Path, client):
    """
    Predict the client loan
    :param checkpoint:
    :param client:
    :return:
    """
    model = xgb.load(checkpoint)
    y_pred_= model.predict(xgb.DMatrix(client))
    return y_pred_