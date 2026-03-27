import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for
import joblib
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'dataset'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

MODEL_PATH = 'model.pkl'
DB_PATH = 'predictions.db'

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            city TEXT,
            day_of_week TEXT,
            ride_distance_km REAL,
            ride_type TEXT,
            weather TEXT,
            event TEXT,
            available_drivers INTEGER,
            hour_of_day INTEGER,
            traffic_delay_min INTEGER,
            predicted_demand_level TEXT,
            predicted_demand_score REAL,
            suggested_surge_multiplier REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Try loading the model globally
try:
    model_data = joblib.load(MODEL_PATH)
    clf = model_data['classifier']
    score_reg = model_data['score_regressor']
    surge_reg = model_data['surge_regressor']
    encoders = model_data['encoders']
    features = model_data['features']
except Exception as e:
    print(f"Warning: Model could not be loaded. Error: {e}")
    model_data = None


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict')
def predict_page():
    return render_template('predict.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/dataset')
def dataset_page():
    return render_template('dataset.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/predict', methods=['POST'])
def api_predict():
    if not model_data:
        return jsonify({'error': 'Model not loaded. Please wait for training to finish.'}), 500

    data = request.json
    
    try:
        # Prepare input df
        input_data = {
            'City': [data['City']],
            'Day_of_Week': [data['Day_of_Week']],
            'Ride_Distance_KM': [float(data['Ride_Distance_KM'])],
            'Ride_Type': [data['Ride_Type']],
            'Weather': [data['Weather']],
            'Event': [data['Event']],
            'Available_Drivers': [int(data['Available_Drivers'])],
            'Hour_of_Day': [int(data['Hour_of_Day'])],
            'Traffic_Delay_Min': [int(data['Traffic_Delay_Min'])]
        }
        input_df = pd.DataFrame(input_data)
        
        # Encode categorical variables
        for col, le in encoders.items():
            if col in input_df.columns:
                # Handle unknown categories safely
                if input_df[col][0] in le.classes_:
                    input_df[col] = le.transform(input_df[col])
                else:
                    input_df[col] = 0 # Default fallback
                    
        X_input = input_df[features]
        
        # Predict
        demand_level = clf.predict(X_input)[0]
        demand_score = round(float(score_reg.predict(X_input)[0]), 2)
        surge_multiplier = round(float(surge_reg.predict(X_input)[0]), 2)
        
        # Save to DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO prediction_history (
                timestamp, city, day_of_week, ride_distance_km, ride_type, weather, 
                event, available_drivers, hour_of_day, traffic_delay_min, 
                predicted_demand_level, predicted_demand_score, suggested_surge_multiplier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['City'], data['Day_of_Week'], float(data['Ride_Distance_KM']),
            data['Ride_Type'], data['Weather'], data['Event'],
            int(data['Available_Drivers']), int(data['Hour_of_Day']), int(data['Traffic_Delay_Min']),
            demand_level, demand_score, surge_multiplier
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'predicted_demand_level': demand_level,
            'demand_score': demand_score,
            'surge_multiplier_suggestion': surge_multiplier
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/dashboard-data', methods=['GET'])
def api_dashboard_data():
    try:
        df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'ride_demand_dataset.csv'))
        
        # Ride demand by city
        city_demand = df.groupby('City').size().to_dict()
        
        # Ride demand by weather
        weather_demand = df.groupby('Weather').size().to_dict()
        
        # Hourly ride demand
        hourly_demand = df.groupby('Hour_of_Day').size().to_dict()
        
        # Driver availability vs demand (Average drivers per demand level)
        driver_demand = df.groupby('Demand_Level')['Available_Drivers'].mean().to_dict()
        
        return jsonify({
            'city_demand': city_demand,
            'weather_demand': weather_demand,
            'hourly_demand': hourly_demand,
            'driver_demand': driver_demand
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dataset', methods=['GET'])
def api_get_dataset():
    try:
        df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'ride_demand_dataset.csv'))
        # Return first 200 rows to avoid crashing the browser
        return jsonify({'success': True, 'data': df.head(500).to_dict('records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ride_demand_dataset.csv')
        file.save(file_path)
        # We could retrain the model here, but for now we just accept the upload
        return jsonify({'success': True, 'message': 'Dataset uploaded successfully.'})
    return jsonify({'error': 'Invalid file format. Please upload a CSV.'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
