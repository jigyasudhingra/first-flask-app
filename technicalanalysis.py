import pandas as pd
from datetime import date
import numpy as np
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
import tensorflow as tf
import sys

import yfinance as yf

# Define the stock symbol and time period
symbol = 'GOOGL'
start_date = '1970-01-01'
end_date = '2020-02-28'

# Fetch the stock data
stock_data = yf.download(symbol, start=start_date, end=end_date, interval="1d")
df = stock_data

def mean_squared_error(y_true, y_pred):
  # Calculate the squared error between the true and predicted values
  squared_error = (y_true - y_pred) ** 2

  # Calculate the mean of the squared error
  mse = squared_error.mean()

  return mse

# Calculate Moving Average
ma = df["Close"].rolling(window=20, min_periods=20, center=False).mean()

# Calculate the MACD
macd = df["Close"].ewm(span=12, adjust=False).mean() - df["Close"].ewm(span=26, adjust=False).mean()

# Calculate the RSI
delta = df["Close"].diff()
delta = delta[1:]
up, down = delta.copy(), delta.copy()
up[up < 0] = 0
down[down > 0] = 0
roll_up1 = up.ewm(span=14, adjust=False).mean()
roll_down1 = down.abs().ewm(span=14, adjust=False).mean()
rsi = 100 - 100 / (1 + roll_up1 / roll_down1)

# Calculate the Bollinger bands
std = df["Close"].rolling(window=20, min_periods=20, center=False).std()
upper_band = ma + (2 * std)
lower_band = ma - (2 * std)

# Combine the indicators into a single DataFrame
indicators = pd.DataFrame({"ma": ma, "macd": macd, "rsi": rsi, "upperband": upper_band, "lowerband": lower_band})
df = df.join(indicators)

df.fillna(method="ffill", inplace=True)
df.fillna(method="bfill", inplace=True)
tempDf = df
df = (df - df.mean()) / df.std()

# Splitting of the data - Train and Test
temp = int(df.shape[0] * 0.99)
X = df[:temp]
y = df[temp + 1:]

y_train = X["Close"]
y_train = y_train.shift(-1)
y_train = y_train.iloc[:-1]
X.drop(['Close'], axis=1, inplace=True)
X_train = X
X_train = X_train.iloc[:-1]

y_test = y["Close"]
y_test = y_test.iloc[1:]
y.drop(['Close'], axis=1, inplace=True)
X_test = y


# Define the deep learning model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, input_shape=(X_train.shape[1],), activation='relu'),
    tf.keras.layers.Dense(100, activation="relu"),
    tf.keras.layers.Dense(1, activation="linear")
])

# Compile the model
model.compile(loss="mean_squared_error", optimizer="adam", metrics = ['accuracy'])

# Train the model
history = model.fit(X_train.to_numpy().astype(np.float32), y_train.to_numpy().astype(np.float32), epochs=30, batch_size=32)

future_prices = model.predict(X_test.values)

# find rmse
rmse = np.sqrt(mean_squared_error(y_test.to_numpy().astype(np.float32), future_prices))
print('RMSE:', rmse)

from matplotlib import pyplot as plt
print(len(future_prices), len(y_test))
plt.figure(figsize=(10, 8))
plt.plot(future_prices, color="black")
plt.plot(y_test.to_numpy().astype(np.float32), color='red')
plt.show()