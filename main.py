from fastapi import FastAPI
from email_validator import validate_email, EmailNotValidError
import phonenumbers

app = FastAPI(title="Sales Intelligence API")

# -------------------------
# VALIDATION HELPERS
# -------------------------

def validate_email_address(email: str):
    try:
        validate_email(email)
        return 100
    except EmailNotValidError:
        return 0

def validate_phone_number(phone: str):
    try:
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(parsed):
            return 100
        return 30
    except:
        return 0

# -------------------------
# SCORING CONFIG
# -------------------------

ROLE_SCORES = {
    "CDO": 30,
    "CTO": 30,
    "VP AI": 28,
    "Head of Platform": 25,
    "Engineer": 15
}

COMPANY_SCORES = {
    "enterprise": 25,
    "series_c": 20,
    "series_b": 15,
    "startup": 5
}

# -------------------------
# MIXED AUTOMATION ENDPOINT
# -------------------------

@app.post("/process")
def process_lead(lead: dict):
    # 1️⃣ DATA VALIDATION
    email_score = validate_email_address(lead.get("email", ""))
    phone_score = validate_phone_number(lead.get("phone", ""))

    confidence = (email_score * 0.6) + (phone_score * 0.4)

    if confidence < 60:
        return {
            "status": "rejected",
            "reason": "Low contact confidence",
            "email_score": email_score,
            "phone_score": phone_score,
            "confidence": confidence
        }

    # 2️⃣ LEAD SCORING
    score = 0
    score += ROLE_SCORES.get(lead.get("role"), 0)
    score += COMPANY_SCORES.get(lead.get("company_size"), 0)
    score += lead.get("pain_signal", 0)
    score += confidence * 0.1

    if score >= 80:
        tier = "Tier 1"
    elif score >= 60:
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    # 3️⃣ FINAL RESPONSE
    return {
        "status": "accepted",
        "confidence": confidence,
        "score": score,
        "tier": tier
    }
