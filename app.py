import pandas as pd
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

app = FastAPI()

# Allow React to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load Data


train_df = pd.read_csv("train.csv")
test_df = pd.read_csv("test1.csv")

full_df = pd.concat([train_df, test_df], ignore_index=True)

full_df['date'] = pd.to_datetime(full_df['date'])
full_df = full_df.sort_values('date')

# Extract date features



full_df['year'] = full_df['date'].dt.year
full_df['month'] = full_df['date'].dt.month
full_df['day'] = full_df['date'].dt.day

train_last_date = pd.to_datetime(train_df['date']).max()

train_processed = full_df[full_df['date'] <= train_last_date]
test_processed = full_df[full_df['date'] > train_last_date]

X_train = train_processed.drop(columns=['meantemp', 'date'])
y_train = train_processed['meantemp']

X_test = test_processed.drop(columns=['meantemp', 'date'])
y_test = test_processed['meantemp']


# Train Model


model = RandomForestRegressor(
    n_estimators=500,
    max_depth=7,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)

r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))


# Input Schema


class InputData(BaseModel):
    year: int
    month: int
    day: int
    humidity: float
    wind_speed: float
    meanpressure: float
    rainfall: float


# Routes


@app.get("/")
def home():
    return {
        "message": "Temperature Prediction API Running",
        "R2 Score": r2,
        "MAE": mae,
        "RMSE": rmse
    }

@app.post("/predict")
def predict(data: InputData):

    input_data = pd.DataFrame([data.dict()])

    # Match training column order
    input_data = input_data[X_train.columns]

    prediction = model.predict(input_data)

    return {
        "predicted_temperature": float(prediction[0])
    }