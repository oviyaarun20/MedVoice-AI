import speech_recognition as sr
from medvoice import run_pipeline

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("Speak now...")
    audio = recognizer.listen(source)

try:
    text = recognizer.recognize_google(audio)
    print("\nYou said:", text)

    result = run_pipeline(text, patient_id="voice_user")

    print("\n===== MEDICAL SUMMARY =====")
    print("Chief Complaint:", result["summary"]["chief_complaint"])
    print("Symptoms:", result["summary"]["symptoms"])
    print("Severity:", result["summary"]["severity"])
    print("Duration:", result["summary"]["duration"])

    print("\n===== RECOMMENDATION =====")
    print("Urgency:", result["recommendation"]["urgency"])
    print("Reason:", result["recommendation"]["reasons"])
    print("Next Steps:", result["recommendation"]["next_steps"])

except Exception as e:
    print("Error:", e)