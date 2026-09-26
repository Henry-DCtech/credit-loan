import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

def train_model():
    # Sample data - replace with your real CSV if you have
    # columns: monthly_income, loan_amount, credit_score, employment_years, default
    data = {
        'monthly_income': [30000, 50000, 100000, 40000, 80000, 20000, 120000, 60000, 35000, 90000],
        'loan_amount': [100000, 150000, 200000, 500000, 300000, 400000, 250000, 100000, 300000, 150000],
        'credit_score': [650, 720, 800, 580, 700, 550, 780, 680, 600, 750],
        'employment_years': [2, 5, 10, 1, 6, 0, 8, 3, 2, 7],
        'default': [0, 0, 0, 1, 0, 1, 0, 0, 1, 0]
    }
    df = pd.DataFrame(data)

    X = df[['monthly_income', 'loan_amount', 'credit_score', 'employment_years']]
    y = df['default']

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Save model
    os.makedirs('ml_engine', exist_ok=True)
    with open('ml_engine/model.pkl', 'wb') as f:
        pickle.dump(model, f)

    print("Model trained and saved to ml_engine/model.pkl")
    return model

if __name__ == "__main__":
    train_model()