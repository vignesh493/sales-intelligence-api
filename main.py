from fastapi import FastAPI
from email_validator import validate_email, EmailNotValidError
import phonenumbers

app = FastAPI(title="Sales Intelligence API")

# -------------------------
# VALIDATION HELPERS
# -------------------------

def validate_email_address(email: str) -> int:
    if not email:
        return 0
    try:
        validate_email(email)
        return 100
    except EmailNotValidError:
        return 0


def validate_phone_number(phone: str) -> int:
    if not phone:
        return 0
    try:
        parsed = phonenumbers.parse(phone, None)
        return 100 if phonenumbers.is_valid_number(parsed) else 0
    except Exception:
        return 0


# -------------------------
# ROLE SCORING
# -------------------------

def score_role(role: str) -> int:
    if not role:
        return 0

    role = role.lower()

    # 🔥 TOP DECISION MAKERS
    if any(k in role for k in [
        "ceo", "cto", "co-founder", "founder", "chief",
        "cso", "cio", "cfo", "president", "vp", "vice president"
    ]):
        return 100

    # 🟡 SENIOR / REVENUE / TECH LEADERS
    if any(k in role for k in [
        "head", "director", "revops", "revenue",
        "engineering manager", "product manager", "growth"
    ]):
        return 75

    # 🟠 MID LEVEL
    if any(k in role for k in [
        "manager", "lead", "consultant"
    ]):
        return 50

    # 🔵 LOW INTENT
    return 25


# -------------------------
# COMPANY SCORING
# -------------------------

def score_company(company: str) -> int:
    if not company:
        return 0

    big_companies = [
        "google", "alphabet", "meta", "amazon",
        "apple", "databricks", "openai", "microsoft"
    ]

    if any(c in company.lower() for c in big_companies):
        return 100

    return 50


# -------------------------
# MAIN ENDPOINT
# -------------------------

@app.post("/process")
def process_lead(payload: dict):
    full_name = payload.get("full_name", "")
    email = payload.get("email", "")
    phone = payload.get("phone", "")
    company = payload.get("company", "")
    role = payload.get("role", "")

    # -------------------------
    # 1️⃣ SCORING
    # -------------------------

    email_score = validate_email_address(email)
    phone_score = validate_phone_number(phone)
    role_score = score_role(role)
    company_score = score_company(company)

    score = round(
        email_score * 0.35 +
        role_score * 0.35 +
        company_score * 0.20 +
        phone_score * 0.10
    )

    confidence = round(
        (email_score + role_score + company_score + phone_score) / 4
    )

    # -------------------------
    # 2️⃣ TIER LOGIC (FIXED)
    # -------------------------

    # 🚨 HARD RULE: EXECUTIVES NEVER GO TO TIER 3
    executive_keywords = [
        "ceo", "cto", "founder", "co-founder",
        "chief", "vp", "vice president", "c-level"
    ]

    if any(k in role.lower() for k in executive_keywords):
        tier = "Tier 1"

    elif score >= 80:
        tier = "Tier 1"

    elif score >= 50:
        tier = "Tier 2"

    else:
        tier = "Tier 3"

    # -------------------------
    # 3️⃣ FINAL RESPONSE
    # -------------------------

    return {
        "status": "accepted",
        "confidence": confidence,
        "score": score,
        "tier": tier
    }
