import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib

# load dataset
data = pd.read_csv("farm_dataset.csv")

X = data[['temp','humidity','light','soil_moisture']]
y = data['next_soil']

# split data
X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)

# train model
model = RandomForestRegressor(n_estimators=200)
model.fit(X_train,y_train)

# test accuracy
predictions = model.predict(X_test)

accuracy = r2_score(y_test,predictions)

print("Model Accuracy:", accuracy)

# save model
joblib.dump(model,"soil_model.pkl")