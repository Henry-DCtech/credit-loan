import os
import pickle
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print("Model loaded")
except:
    model = None
    print("Model not found - using rule-based")

def predict_risk(income, loan, credit, employment, existing):
    try:
        if model:
            # Adjust features to match your training
            features = np.array([[income, loan, credit, employment, existing]])
            prob = model.predict_proba(features)[0][1] * 100 if hasattr(model, 'predict_proba') else model.predict(features)[0] * 100
            risk = float(prob)
        else:
            raise Exception("No model")
    except:
        # Rule-based fallback - same logic as before
        risk = 0
        if income < 100000: risk += 30
        if loan > income * 3: risk += 25
        if credit < 600: risk += 30
        elif credit < 700: risk += 15
        if employment < 2: risk += 15
        if existing > 2: risk += 10
        risk = min(risk, 95)

    if risk < 30:
        decision = 'APPROVED'
        reason = 'Low risk profile - excellent credit and income'
    elif risk < 60:
        decision = 'MANUAL_REVIEW'
        reason = 'Medium risk - requires manual review'
    else:
        decision = 'REJECTED'
        reason = 'High risk - poor credit/income ratio'

    return {
        'risk_score': round(risk, 1),
        'decision': decision,
        'reason': reason
    }
