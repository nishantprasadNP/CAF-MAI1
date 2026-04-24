import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bias-platform", "backend"))

import pandas as pd
import numpy as np

from app.modules.module6.service import run_module6
from app.modules.module5.service import run_module5
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# ---------------------------
# 1. CREATE DUMMY DATASET
# ---------------------------
df = pd.DataFrame({
    "sex": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
    "race": ["White", "Black", "White", "Black", "Black", "White", "White", "Black"],
    "feature1": [10, 20, 15, 25, 30, 18, 22, 27],
    "feature2": [1, 0, 1, 0, 1, 0, 1, 0]
})

# Target (biased intentionally)
y = pd.Series([1, 0, 1, 0, 1, 0, 1, 0])

bias_columns = ["sex", "race"]

# ---------------------------
# 2. TRAIN BASE MODEL (Module 4 simulation)
# ---------------------------
X = df[["feature1", "feature2"]]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

# Convert to pandas Series
y_test = pd.Series(y_test.values, index=X_test.index)
predictions = pd.Series(predictions, index=X_test.index)

# ---------------------------
# 3. RUN MODULE 5 (BEFORE)
# ---------------------------
df_test = df.iloc[X_test.index].reset_index(drop=True)
y_test_reset = y_test.reset_index(drop=True)
predictions_reset = predictions.reset_index(drop=True)

module5_before = run_module5(
    df=df_test,
    y_true=y_test_reset,
    y_pred=predictions_reset,
    bias_columns=bias_columns
)

print("\n===== MODULE 5 BEFORE =====")
print(module5_before)

# ---------------------------
# 4. RUN MODULE 6
# ---------------------------
X_train_reset = X_train.reset_index(drop=True)
y_train_reset = y_train.reset_index(drop=True)
df_train_reset = df.iloc[X_train.index].reset_index(drop=True)

module6_results = run_module6(
    df=df_train_reset,
    X_train=X_train_reset,
    y_train=y_train_reset,
    bias_columns=bias_columns,
    module5_results=module5_before
)

print("\n===== MODULE 6 RESULTS =====")
print(module6_results)