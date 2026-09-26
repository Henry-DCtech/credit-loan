import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')

def predict_default_probability(data):
    # Try load real model
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)

            features = [[
                float(data.get('monthly_income', 50000)),
                float(data.get('loan_amount', 100000)),
                float(data.get('credit_score', 650)),
                float(data.get('employment_years', 2))
            ]]
            prob = model.predict_proba(features)[0][1] # probability of default
            return float(prob)
        except Exception as e:
            print(f"Model load failed, using dummy: {e}")

    # Fallback dummy logic
    income = float(data.get('monthly_income', 50000) or 50000)
    loan = float(data.get('loan_amount', 100000) or 100000)
    credit = float(data.get('credit_score', 650) or 650)

    ratio = loan / (income + 1)
    if credit < 600 or ratio > 10:
        return 0.75
    elif credit < 700 or ratio > 5:
        return 0.45
    else:
        return 0.15