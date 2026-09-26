# AI-Powered Credit Risk Platform | CEO Console

An end-to-end AI credit underwriting system built with Django + Machine Learning for intelligent loan decisioning.

Live Demo: `https://credit-loan.onrender.com` (deploying)

### Problem
Manual credit assessment is slow, biased, and risky for micro-lenders in emerging markets.

### Solution
An ML-driven platform that predicts loan default risk in <2 seconds with 87%+ accuracy and provides a CEO analytics console for portfolio management.

### Key Features
- **AI Risk Engine:** `ml_engine/` - XGBoost/Random Forest model trained on credit data
- **CEO Console:** Real-time dashboard - total loans, default rate, profit, risk distribution
- **Instant Decision:** API endpoint `/api/predict/` returns Approved/Rejected + risk score
- **Django Backend:** Secure auth, loan management, audit logs
- **Explainable AI:** SHAP values showing why a loan was rejected

### Tech Stack
Python, Django, Scikit-Learn, Pandas, PostgreSQL, Render, Git

### Architecture

#API SAMPLE

POST /api/predict/
{
  "income": 50000,
  "credit_score": 720,
  "loan_amount": 10000
}
Response: {"decision": "APPROVED", "risk_score": 0.12}