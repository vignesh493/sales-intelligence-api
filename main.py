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
        return 40
    except:
        return 0

# -------------------------
# MAIN PROCESS ENDPOINT
# -------------------------

@app.post("/process")
def process_lead(lead: dict):

    # -------------------------
    # 1️⃣ CONTACT CONFIDENCE
    # -------------------------

    email = lead.get("email", "")
    phone = lead.get("phone", "")

    email_score = validate_email_address(email)
    phone_score = validate_phone_number(phone)

    confidence = round((email_score * 0.6) + (phone_score * 0.4), 2)

    if confidence < 60:
        return {
            "status": "rejected",
            "reason": "Low contact confidence",
            "email_score": email_score,
            "phone_score": phone_score,
            "confidence": confidence,
            "tier": "Rejected"
        }

    # -------------------------
    # 2️⃣ BUSINESS SCORING
    # -------------------------

    score = 0

    # --- Role scoring (LinkedIn-aware) ---
    role = lead.get("role", "").lower()

    if any(x in role for x in ["chief", "cto", "cdo", "cio"]):
        score += 35
    elif any(x in role for x in ["vp", "vice president"]):
        score += 30
    elif "head" in role:
        score += 25
    elif "manager" in role:
        score += 18
    elif "engineer" in role:
        score += 12

    # --- Company scoring (Clay-enriched or inferred) ---
    company_size = lead.get("company_size", "").lower()
    company = lead.get("company", "").lower()

    if company_size in ["enterprise", "1000+", "500+"]:
        score += 30
    elif company_size in ["series_d", "series_c"]:
        score += 22
    elif company_size in ["series_b"]:
        score += 18
    elif company_size:
        score += 10
    else:
        # fallback inference if Clay field missing
        if any(x in company for x in ["inc", "corp", "enterprise"]):
            score += 20
        else:
            score += 8

    # --- LinkedIn intent signals (Clay usually provides these) ---
    score += int(lead.get("pain_signal", 0))        # 0–20
    score += int(lead.get("job_change_signal", 0)) # 0–15
    score += int(lead.get("hiring_signal", 0))     # 0–15

    # --- Bonus for complete contact ---
    if email_score == 100 and phone_score == 100:
        score += 10

    # --- Small confidence weight ---
    score += confidence * 0.1

    score = round(score, 2)

    # -------------------------
    # 3️⃣ TIER ASSIGNMENT
    # -------------------------

    if score >= 80:
        tier = "Tier 1"
    elif score >= 55:
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    # -------------------------
    # 4️⃣ FINAL RESPONSE
    # -------------------------

    return {
        "status": "accepted",
        "confidence": confidence,
        "score": score,
        "tier": tier
    }
