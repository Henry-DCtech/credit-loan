# AI Credit Risk Console - Lagos

AI-Powered Loan Approval System for CEO Executive Review.

## Features
- Executive Risk Console (CEO-only approval)
- ML Risk Scoring (Random Forest)
- Multi-Branch Support: LAGOS, ABUJA, KANO, ONDO, OSUN, OYO, LOKOJA, PORT_HARCOURT
- Fairness & Explainability Module
- Client Management

## Tech Stack
- Django 5.x
- Python 3.11
- Scikit-learn for ML model
- SQLite / PostgreSQL

## Setup
```bash
git clone https://github.com/Henry-DCtech/credit-loan.git
cd credit-loan
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver