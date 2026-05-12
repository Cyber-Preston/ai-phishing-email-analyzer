import streamlit as st
import re
import requests

st.set_page_config(
    page_title="Phishing Email Analyzer",
    page_icon="📧",
    layout="wide"
)

st.sidebar.title("🛡️ SOC Tools")
st.sidebar.write("Phishing Detection Engine")
st.sidebar.write("Version 2.1")
st.sidebar.write("Rule-Based + Local AI + File Upload")

st.title("📧 Phishing Email Analyzer")
st.info("Analyze suspicious emails for phishing indicators, malicious URLs, and social engineering tactics.")
st.write("Paste an email below or upload a `.txt` email file.")

if st.button("Load Sample Phishing Email"):
    st.session_state.sample_email = """
URGENT: Your Microsoft account has been suspended.

Click here immediately to verify your password:
https://bit.ly/security-check

Failure to act within 24 hours will result in permanent closure.
"""

uploaded_file = st.file_uploader(
    "Upload Email File",
    type=["txt"]
)

uploaded_text = ""

if uploaded_file is not None:
    uploaded_text = uploaded_file.read().decode("utf-8")

email_text = st.text_area(
    "Email Content",
    value=uploaded_text if uploaded_text else st.session_state.get("sample_email", ""),
    height=250
)

phishing_keywords = [
    "urgent",
    "verify your account",
    "password expired",
    "click here",
    "limited time",
    "account suspended",
    "confirm your identity",
    "login immediately",
    "payment failed",
    "security alert",
    "unusual activity",
    "reset your password",
    "invoice attached",
    "failure to act",
    "permanent closure",
    "suspended"
]

def extract_urls(text):
    return re.findall(r"https?://[^\s]+", text)

def ask_ai(email_content):
    prompt = f"""
You are a cybersecurity analyst.

Analyze this email for phishing and social engineering risks.

Explain:
- why it is suspicious
- what tactics are being used
- what the user should do

Keep it clear and beginner-friendly.

Email:
{email_content}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        return response.json()["response"]

    except requests.exceptions.ConnectionError:
        return "AI analysis unavailable. Make sure Ollama is open and running with: ollama run llama3"

    except Exception as e:
        return f"AI analysis error: {e}"

def analyze_email(text):
    score = 0
    indicators = []
    lower_text = text.lower()

    for keyword in phishing_keywords:
        if keyword in lower_text:
            score += 10
            indicators.append(f"⚠️ Suspicious phrase detected: '{keyword}'")

    urls = extract_urls(text)

    if urls:
        score += 20
        indicators.append(f"🔗 Found {len(urls)} URL(s) in the email")

    for url in urls:
        if any(shortener in url for shortener in ["bit.ly", "tinyurl", "t.co", "goo.gl"]):
            score += 20
            indicators.append(f"🚨 Shortened URL detected: {url}")

        if any(word in url.lower() for word in ["login", "verify", "secure", "update"]):
            score += 10
            indicators.append(f"🔍 Suspicious URL wording detected: {url}")

    if text.count("!") >= 2:
        score += 10
        indicators.append("❗ Multiple exclamation marks detected")

    sensitive_words = ["password", "bank", "credit card", "ssn", "social security"]

    if any(word in lower_text for word in sensitive_words):
        score += 15
        indicators.append("🔐 Sensitive information request detected")

    score = min(score, 100)

    if score >= 70:
        verdict = "High Risk - Likely Phishing"
    elif score >= 40:
        verdict = "Medium Risk - Suspicious"
    else:
        verdict = "Low Risk - Looks Safer"

    return score, verdict, indicators, urls

if st.button("Analyze Email"):
    if not email_text.strip():
        st.warning("Please paste or upload an email first.")
    else:
        score, verdict, indicators, urls = analyze_email(email_text)

        st.subheader("📊 Scan Results")
        st.metric("Phishing Risk Score", f"{score}%")
        st.progress(score)

        st.subheader("🚨 Threat Classification")

        if score >= 70:
            st.error("🔴 HIGH RISK THREAT")
        elif score >= 40:
            st.warning("🟠 MEDIUM RISK THREAT")
        else:
            st.success("🟢 LOW RISK")

        if score >= 70:
            st.error(verdict)
        elif score >= 40:
            st.warning(verdict)
        else:
            st.success(verdict)

        st.subheader("🧠 Indicators Found")

        if indicators:
            for item in indicators:
                st.write(item)
        else:
            st.write("✅ No major phishing indicators detected.")

        st.subheader("🔗 URLs Found")

        if urls:
            for url in urls:
                st.code(url)
        else:
            st.write("No URLs found.")

        st.subheader("🤖 AI Security Analysis")

        with st.spinner("AI is analyzing the email..."):
            ai_response = ask_ai(email_text)
            st.write(ai_response)

        st.subheader("🛡️ Recommendation")

        if score >= 70:
            st.write("Do not click links, download attachments, or reply. Report this email to IT/security immediately.")
        elif score >= 40:
            st.write("Be cautious. Verify the sender and avoid clicking links.")
        else:
            st.write("No obvious phishing signs detected, but remain cautious.")