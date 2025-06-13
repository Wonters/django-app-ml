import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import pandas as pd
import numpy as np

# Préparation des données
data_url = "http://lib.stat.cmu.edu/datasets/boston"
data = pd.read_csv(data_url, sep="\s+", skiprows=22, header=None)
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target, name='target')
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Paramètres du modèle
params = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "objective": "reg:squarederror"
}

# Tracking MLflow
with mlflow.start_run():
    # Création du modèle
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    # Prédiction et métriques
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))

    # Log des paramètres et métriques
    mlflow.log_params(params)
    mlflow.log_metric("rmse", rmse)

    # Log du modèle
    mlflow.xgboost.log_model(model, "xgboost_model")

    print(f"RMSE: {rmse:.4f}")