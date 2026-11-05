import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_NAMES = ["Ridge", "Random forest", "Gradient boosting"]

class DropUninformative(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        data = pd.DataFrame(X)
        self.keep_ = [i for i in range(data.shape[1]) if data.iloc[:, i].nunique(dropna=True) >= 2]
        return self

    def transform(self, X):
        return pd.DataFrame(X).iloc[:, self.keep_].to_numpy(dtype=float)

def make_models():
    return {
        "Ridge": Pipeline([
            ("drop", DropUninformative()),
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ]),
        "Random forest": Pipeline([
            ("drop", DropUninformative()),
            ("impute", SimpleImputer(strategy="median")),
            ("model", RandomForestRegressor(
                n_estimators=300, min_samples_leaf=5, max_features=0.6, random_state=0)),
        ]),
        "Gradient boosting": Pipeline([
            ("drop", DropUninformative()),
            ("model", HistGradientBoostingRegressor(
                max_depth=3, learning_rate=0.05, max_iter=200,
                min_samples_leaf=20, l2_regularization=1.0, random_state=0)),
        ]),
    }
