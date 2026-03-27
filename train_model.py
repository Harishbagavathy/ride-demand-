import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
import os

print("Step 1: Loading dataset using pandas...")
df = pd.read_csv('dataset/ride_demand_dataset.csv')

print("Step 2: Handling missing values...")
# Drop missing values if any
df = df.dropna()

print("Step 3: Encoding categorical columns using LabelEncoder...")
categorical_cols = ['City', 'Day_of_Week', 'Ride_Type', 'Weather', 'Event']
encoders = {}

for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

# Features and target
# User inputs: City, Day_of_Week, Ride_Distance_KM, Ride_Type, Weather, Event, Available_Drivers, Hour_of_Day, Traffic_Delay_Min
features = ['City', 'Day_of_Week', 'Ride_Distance_KM', 'Ride_Type', 'Weather', 'Event', 'Available_Drivers', 'Hour_of_Day', 'Traffic_Delay_Min']
X = df[features]

y_level = df['Demand_Level']
y_score = df['Demand_Score']
y_surge = df['Surge_Multiplier']

print("Step 4: Splitting dataset into training and testing...")
X_train, X_test, y_level_train, y_level_test, y_score_train, y_score_test, y_surge_train, y_surge_test = train_test_split(
    X, y_level, y_score, y_surge, test_size=0.2, random_state=42
)

print("Step 5: Training RandomForest models...")
# Classifier for Demand_Level
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_level_train)

# Regressors for Demand_Score and Surge_Multiplier
score_reg = RandomForestRegressor(n_estimators=100, random_state=42)
score_reg.fit(X_train, y_score_train)

surge_reg = RandomForestRegressor(n_estimators=100, random_state=42)
surge_reg.fit(X_train, y_surge_train)

print("Step 6: Calculating model accuracy...")
y_level_pred = clf.predict(X_test)
accuracy = accuracy_score(y_level_test, y_level_pred)
print(f"Demand Level Classifier Accuracy: {accuracy * 100:.2f}%")

score_pred = score_reg.predict(X_test)
score_mae = mean_absolute_error(y_score_test, score_pred)
print(f"Demand Score Regressor MAE: {score_mae:.2f}")

surge_pred = surge_reg.predict(X_test)
surge_mae = mean_absolute_error(y_surge_test, surge_pred)
print(f"Surge Multiplier Regressor MAE: {surge_mae:.2f}")

print("Step 7: Saving trained models and encoders using joblib...")
model_data = {
    'classifier': clf,
    'score_regressor': score_reg,
    'surge_regressor': surge_reg,
    'encoders': encoders,
    'features': features
}
joblib.dump(model_data, 'model.pkl')
print("Model saved to model.pkl successfully.")
