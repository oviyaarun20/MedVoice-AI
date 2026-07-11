import re
import json
import os
import uuid
from datetime import datetime, timezone
SYMPTOM_LEXICON = {
    "fever": ["fever", "high temperature", "chills"],
    "cough": ["cough", "coughing"],
    "shortness_of_breath": ["shortness of breath", "can't breathe", "difficulty breathing"],
    "chest_pain": ["chest pain", "chest tightness"],
    "headache": ["headache", "head pain", "migraine"],
    "nausea": ["nausea", "nauseous"],
    "vomiting": ["vomiting", "throwing up"],
    "abdominal_pain": ["stomach ache", "stomach pain", "abdominal pain"],
    "dizziness": ["dizziness", "dizzy", "lightheaded"],
    "fatigue": ["fatigue", "tired", "exhausted"],
    "sore_throat": ["sore throat", "throat pain"],
    "loss_of_consciousness": ["fainted", "passed out"],
    "severe_bleeding": ["bleeding a lot", "heavy bleeding"],
    "confusion": ["confused", "disoriented"],
}

RED_FLAG_SYMPTOMS = {
    "shortness_of_breath", "chest_pain", "loss_of_consciousness",
    "severe_bleeding", "confusion",
}

DURATION_PATTERN = re.compile(r"(\d+)\s*(day|days|hour|hours|week|weeks|month|months)", re.IGNORECASE)

SEVERITY_TERMS = {
    "mild": ["mild", "slight", "a little"],
    "moderate": ["moderate", "noticeable"],
    "severe": ["severe", "intense", "unbearable", "worst", "extreme"],
}

DISCLAIMER = (
    "This is an automated triage suggestion, not a medical diagnosis. "
    "It is not a substitute for evaluation by a licensed clinician. "
    "If this is a medical emergency, call your local emergency number immediately."
)


def summarize(text):
    text_lower = text.lower()

    symptoms = []
    for symptom, phrases in SYMPTOM_LEXICON.items():
        if any(phrase in text_lower for phrase in phrases):
            symptoms.append(symptom)

    duration_match = DURATION_PATTERN.search(text_lower)
    duration = duration_match.group(0) if duration_match else None

    severity = None
    for level, phrases in SEVERITY_TERMS.items():
        if any(phrase in text_lower for phrase in phrases):
            severity = level
            break

    red_flags = [s for s in symptoms if s in RED_FLAG_SYMPTOMS]

    first_sentence = re.split(r"[.!?]", text.strip())[0].strip()
    chief_complaint = first_sentence if first_sentence else (symptoms[0] if symptoms else "unspecified")

    return {
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity,
        "red_flags": red_flags,
    }
def recommend(summary):
    if summary["red_flags"]:
        return {
            "urgency": "emergency",
            "reasons": [f"Red-flag symptom(s) detected: {', '.join(summary['red_flags'])}"],
            "next_steps": ["Seek immediate emergency care or call emergency services."],
            "disclaimer": DISCLAIMER,
        }

    if summary["severity"] == "severe":
        return {
            "urgency": "see_doctor_soon",
            "reasons": ["Severity reported as severe."],
            "next_steps": ["Schedule an urgent appointment with a physician (within 24 hours)."],
            "disclaimer": DISCLAIMER,
        }

    if summary["duration"] and any(u in summary["duration"] for u in ["week", "weeks", "month", "months"]):
        return {
            "urgency": "see_doctor_soon",
            "reasons": [f"Symptoms have persisted for {summary['duration']}."],
            "next_steps": ["Schedule a non-urgent appointment with a physician."],
            "disclaimer": DISCLAIMER,
        }

    if summary["symptoms"]:
        return {
            "urgency": "self_care",
            "reasons": [f"Symptoms detected: {', '.join(summary['symptoms'])}. No red flags."],
            "next_steps": ["Rest, stay hydrated, and monitor symptoms."],
            "disclaimer": DISCLAIMER,
        }

    return {
        "urgency": "insufficient_info",
        "reasons": ["No recognized symptoms matched."],
        "next_steps": ["Ask clarifying questions to get more detail."],
        "disclaimer": DISCLAIMER,
    }
def run_pipeline(transcript_text, patient_id="anon", records_dir="medical_records"):
    os.makedirs(records_dir, exist_ok=True)

    summary = summarize(transcript_text)
    rec = recommend(summary)

    result = {
        "record_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transcript": transcript_text,
        "summary": summary,
        "recommendation": rec,
    }

    fname = f"{patient_id}_{result['record_id']}.json"
    path = os.path.join(records_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result
SAMPLE_CASES = {
    "case_emergency_chest_pain": ("I'm having severe chest pain and I can't breathe.", "emergency"),
    "case_emergency_fainting": ("My father just fainted and passed out, he seems confused.", "emergency"),
    "case_urgent_persistent_fever": ("I've had a fever and a bad cough for 2 weeks.", "see_doctor_soon"),
    "case_urgent_severe_headache": ("I have a severe headache, worst pain I've ever felt.", "see_doctor_soon"),
    "case_selfcare_mild_cold": ("I have a mild sore throat and a slight cough since yesterday.", "self_care"),
    "case_selfcare_fatigue": ("I've been feeling tired and a little dizzy for a day.", "self_care"),
    "case_insufficient_info": ("I don't feel well today.", "insufficient_info"),
}

if __name__ == "__main__":
    passed = 0
    failed = 0

    for case_id, (text, expected) in SAMPLE_CASES.items():
        result = run_pipeline(text, patient_id=case_id)
        actual = result["recommendation"]["urgency"]
        status = "PASS" if actual == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {case_id}: expected={expected} actual={actual}")

    total = passed + failed
    coverage_pct = round((passed / total) * 100, 1) if total else 0
    print(f"\n{passed}/{total} sample cases passed ({coverage_pct}% match rate)")
    print("Medical records saved to the 'medical_records' folder.")