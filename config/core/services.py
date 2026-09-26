from ml_engine.predictor import predict_default_probability

def make_decision(data):
    prob = predict_default_probability(data)

    if prob < 0.3:
        decision = "APPROVED"
        reason = f"Low risk: {prob*100:.1f}% default probability"
    elif prob < 0.6:
        decision = "MANUAL_REVIEW"
        reason = f"Medium risk: {prob*100:.1f}% - needs manual review"
    else:
        decision = "REJECTED"
        reason = f"High risk: {prob*100:.1f}% default probability"

    return {
        "probability": prob,
        "decision": decision,
        "reason": reason
    }