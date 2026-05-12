import re

import requests
import streamlit as st


st.set_page_config(
    page_title="Phishing Email Analyzer",
    page_icon="🛡️",
    layout="wide",
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
    "suspended",
]

URL_SHORTENERS = ["bit.ly", "tinyurl", "t.co", "goo.gl"]
SUSPICIOUS_URL_WORDS = ["login", "verify", "secure", "update"]
SENSITIVE_WORDS = ["password", "bank", "credit card", "ssn", "social security"]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

            :root {
                --bg: #07111f;
                --bg-soft: #0d1b2a;
                --panel: rgba(10, 24, 40, 0.82);
                --panel-strong: rgba(7, 16, 29, 0.95);
                --border: rgba(102, 252, 241, 0.18);
                --text: #e8f6ff;
                --muted: #8ba7bd;
                --cyan: #66fcf1;
                --blue: #4ea8de;
                --lime: #92ff9e;
                --amber: #ffbf69;
                --danger: #ff5d73;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(78, 168, 222, 0.20), transparent 28%),
                    radial-gradient(circle at top right, rgba(102, 252, 241, 0.14), transparent 24%),
                    linear-gradient(180deg, #040b14 0%, #07111f 45%, #09192b 100%);
                color: var(--text);
                font-family: 'Space Grotesk', sans-serif;
            }

            .stApp [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(8, 19, 33, 0.98), rgba(6, 15, 28, 0.98));
                border-right: 1px solid rgba(102, 252, 241, 0.12);
            }

            .stApp [data-testid="stSidebar"] * {
                color: var(--text);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1320px;
            }

            h1, h2, h3 {
                font-family: 'Space Grotesk', sans-serif;
                letter-spacing: -0.03em;
            }

            p, li, label {
                color: var(--muted);
            }

            [data-testid="stMetric"] {
                background: linear-gradient(180deg, rgba(10, 24, 40, 0.88), rgba(8, 18, 31, 0.92));
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 1rem;
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.25);
            }

            [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
                color: var(--text);
            }

            .stTextArea textarea, .stTextInput input {
                background: rgba(5, 15, 26, 0.92) !important;
                color: var(--text) !important;
                border: 1px solid rgba(102, 252, 241, 0.18) !important;
                border-radius: 18px !important;
                font-family: 'JetBrains Mono', monospace !important;
                box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
            }

            .stTextArea label, .stFileUploader label {
                color: var(--text) !important;
                font-weight: 600;
            }

            .stButton > button {
                border-radius: 999px;
                border: 1px solid rgba(102, 252, 241, 0.28);
                color: #03131f;
                background: linear-gradient(135deg, var(--cyan), #a5fff8);
                padding: 0.72rem 1.2rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                box-shadow: 0 10px 30px rgba(102, 252, 241, 0.2);
            }

            .stButton > button:hover {
                border-color: rgba(102, 252, 241, 0.5);
                transform: translateY(-1px);
            }

            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, var(--blue), var(--cyan));
            }

            .hero-card,
            .glass-card,
            .sidebar-card {
                background: linear-gradient(180deg, rgba(11, 24, 41, 0.9), rgba(8, 17, 31, 0.96));
                border: 1px solid var(--border);
                border-radius: 24px;
                box-shadow: 0 20px 80px rgba(0, 0, 0, 0.28);
                backdrop-filter: blur(14px);
            }

            .hero-card {
                padding: 2rem;
                overflow: hidden;
                position: relative;
                margin-bottom: 1.2rem;
            }

            .hero-card::after {
                content: "";
                position: absolute;
                inset: auto -80px -80px auto;
                width: 220px;
                height: 220px;
                background: radial-gradient(circle, rgba(102, 252, 241, 0.22), transparent 70%);
            }

            .eyebrow {
                color: var(--cyan);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.24em;
                text-transform: uppercase;
                margin-bottom: 0.7rem;
            }

            .hero-title {
                font-size: 3rem;
                line-height: 0.95;
                color: var(--text);
                margin: 0;
            }

            .hero-subtitle {
                max-width: 760px;
                color: #aec7db;
                font-size: 1.02rem;
                margin-top: 0.9rem;
                margin-bottom: 1.4rem;
            }

            .hero-grid,
            .signal-grid {
                display: grid;
                gap: 0.9rem;
            }

            .hero-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .signal-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                margin-top: 1rem;
            }

            .stat-chip,
            .signal-card {
                border-radius: 18px;
                padding: 1rem 1.1rem;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(102, 252, 241, 0.12);
            }

            .stat-chip small,
            .signal-card small {
                display: block;
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-size: 0.7rem;
                margin-bottom: 0.4rem;
            }

            .stat-chip strong,
            .signal-card strong {
                color: var(--text);
                font-size: 1.05rem;
            }

            .glass-card {
                padding: 1.25rem;
                height: 100%;
            }

            .section-title {
                color: var(--text);
                font-size: 1rem;
                text-transform: uppercase;
                letter-spacing: 0.16em;
                margin-bottom: 0.4rem;
            }

            .mono {
                font-family: 'JetBrains Mono', monospace;
            }

            .sidebar-card {
                padding: 1.1rem;
                margin-bottom: 1rem;
            }

            .sidebar-card h4 {
                color: var(--text);
                margin: 0 0 0.4rem 0;
            }

            .sidebar-card p {
                margin: 0.15rem 0;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                margin-bottom: 0.8rem;
            }

            .status-live {
                color: #042032;
                background: linear-gradient(135deg, var(--cyan), #b8fff4);
            }

            .threat-panel {
                border-radius: 22px;
                padding: 1.1rem 1.2rem;
                border: 1px solid rgba(255, 255, 255, 0.08);
                margin: 0.75rem 0 1rem 0;
            }

            .threat-panel.high {
                background: linear-gradient(180deg, rgba(72, 11, 19, 0.95), rgba(45, 8, 14, 0.98));
                border-color: rgba(255, 93, 115, 0.28);
            }

            .threat-panel.medium {
                background: linear-gradient(180deg, rgba(68, 39, 8, 0.95), rgba(47, 28, 8, 0.98));
                border-color: rgba(255, 191, 105, 0.22);
            }

            .threat-panel.low {
                background: linear-gradient(180deg, rgba(8, 51, 31, 0.95), rgba(6, 35, 21, 0.98));
                border-color: rgba(146, 255, 158, 0.22);
            }

            .threat-label {
                color: var(--text);
                font-size: 1.15rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }

            .threat-copy {
                color: #c9d9e6;
                margin: 0;
            }

            .indicator-list {
                display: grid;
                gap: 0.75rem;
            }

            .indicator-item,
            .url-item {
                border-radius: 16px;
                padding: 0.9rem 1rem;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(102, 252, 241, 0.1);
                color: var(--text);
            }

            .recommendation-box {
                padding: 1rem 1.1rem;
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(9, 30, 45, 0.94), rgba(7, 21, 34, 0.98));
                border: 1px solid rgba(78, 168, 222, 0.18);
                color: var(--text);
            }

            code {
                color: var(--cyan) !important;
                font-family: 'JetBrains Mono', monospace !important;
            }

            @media (max-width: 980px) {
                .hero-title {
                    font-size: 2.25rem;
                }

                .hero-grid,
                .signal-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text)


def ask_ai(email_content: str) -> str:
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
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "No AI response returned.")
    except requests.exceptions.ConnectionError:
        return (
            "AI analysis unavailable. Make sure Ollama is running locally "
            "with `ollama run llama3`."
        )
    except Exception as exc:
        return f"AI analysis error: {exc}"


def analyze_email(text: str) -> tuple[int, str, list[str], list[str]]:
    score = 0
    indicators = []
    lower_text = text.lower()

    for keyword in phishing_keywords:
        if keyword in lower_text:
            score += 10
            indicators.append(f"Suspicious phrase detected: '{keyword}'")

    urls = extract_urls(text)

    if urls:
        score += 20
        indicators.append(f"Found {len(urls)} URL(s) in the email")

    for url in urls:
        if any(shortener in url for shortener in URL_SHORTENERS):
            score += 20
            indicators.append(f"Shortened URL detected: {url}")

        if any(word in url.lower() for word in SUSPICIOUS_URL_WORDS):
            score += 10
            indicators.append(f"Suspicious URL wording detected: {url}")

    if text.count("!") >= 2:
        score += 10
        indicators.append("Multiple exclamation marks detected")

    if any(word in lower_text for word in SENSITIVE_WORDS):
        score += 15
        indicators.append("Sensitive information request detected")

    score = min(score, 100)

    if score >= 70:
        verdict = "High Risk - Likely Phishing"
    elif score >= 40:
        verdict = "Medium Risk - Suspicious"
    else:
        verdict = "Low Risk - Looks Safer"

    return score, verdict, indicators, urls


def get_threat_style(score: int) -> tuple[str, str, str]:
    if score >= 70:
        return "high", "HIGH RISK THREAT", "Immediate containment recommended."
    if score >= 40:
        return "medium", "MEDIUM RISK THREAT", "Manual verification strongly advised."
    return "low", "LOW RISK", "No major rule-based indicators triggered."


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero-card">
            <div class="eyebrow">Threat Intelligence Console</div>
            <h1 class="hero-title">Phishing Email Analyzer</h1>
            <p class="hero-subtitle">
                Investigate suspicious messages with a premium SOC-inspired interface,
                risk scoring, URL inspection, and local AI-assisted triage.
            </p>
            <div class="hero-grid">
                <div class="stat-chip">
                    <small>Detection Stack</small>
                    <strong>Rules + URL Heuristics + Local LLM</strong>
                </div>
                <div class="stat-chip">
                    <small>Designed For</small>
                    <strong>Analysts, Helpdesks, Security Training</strong>
                </div>
                <div class="stat-chip">
                    <small>Input Modes</small>
                    <strong>Paste Email or Upload <span class="mono">.txt</span></strong>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-card">
            <div class="status-pill status-live">SYSTEM ONLINE</div>
            <h4>SOC Tools</h4>
            <p>Phishing Detection Engine</p>
            <p>Version 2.1</p>
            <p>Cyber theme interface</p>
        </div>
        <div class="sidebar-card">
            <h4>Capabilities</h4>
            <p>Rule-based scoring</p>
            <p>Shortener detection</p>
            <p>Local AI narrative analysis</p>
            <p>TXT email ingestion</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.caption("Built for fast phishing triage and polished analyst workflows.")


def main() -> None:
    inject_styles()
    render_sidebar()
    render_hero()

    if st.button("Load Sample Threat Email"):
        st.session_state.sample_email = """
URGENT: Your Microsoft account has been suspended.

Click here immediately to verify your password:
https://bit.ly/security-check

Failure to act within 24 hours will result in permanent closure.
"""

    uploaded_file = st.file_uploader("Upload Email File", type=["txt"])
    uploaded_text = ""

    if uploaded_file is not None:
        uploaded_text = uploaded_file.read().decode("utf-8")

    st.markdown(
        """
        <div class="glass-card" style="margin-bottom: 1rem;">
            <div class="section-title">Email Intake</div>
            <p>
                Paste suspicious content below or load a plain-text email file to begin
                investigation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    email_text = st.text_area(
        "Email Content",
        value=uploaded_text if uploaded_text else st.session_state.get("sample_email", ""),
        height=280,
        placeholder="Paste the suspicious email body here...",
        label_visibility="collapsed",
    )

    action_col, spacer_col = st.columns([1, 4])
    with action_col:
        analyze_clicked = st.button("Analyze Email", use_container_width=True)
    with spacer_col:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Analysis Notes</div>
                <p>
                    The scanner checks for phishing language, suspicious URL patterns,
                    urgency cues, and sensitive-data requests before generating a local AI summary.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not analyze_clicked:
        return

    if not email_text.strip():
        st.warning("Please paste or upload an email first.")
        return

    score, verdict, indicators, urls = analyze_email(email_text)
    threat_class, threat_title, threat_copy = get_threat_style(score)

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
    summary_col, intel_col = st.columns([1.15, 1])

    with summary_col:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Risk Summary</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        metric_cols = st.columns(3)
        metric_cols[0].metric("Risk Score", f"{score}%")
        metric_cols[1].metric("Verdict", verdict.split(" - ")[0])
        metric_cols[2].metric("URLs Found", len(urls))
        st.progress(score)
        st.markdown(
            f"""
            <div class="threat-panel {threat_class}">
                <div class="threat-label">{threat_title}</div>
                <p class="threat-copy">{verdict}. {threat_copy}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with intel_col:
        indicator_count = len(indicators)
        suspicious_url_count = sum(
            1
            for url in urls
            if any(shortener in url for shortener in URL_SHORTENERS)
            or any(word in url.lower() for word in SUSPICIOUS_URL_WORDS)
        )
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Signal Snapshot</div>
                <div class="signal-grid">
                    <div class="signal-card">
                        <small>Indicators</small>
                        <strong>{indicator_count}</strong>
                    </div>
                    <div class="signal-card">
                        <small>Suspicious URLs</small>
                        <strong>{suspicious_url_count}</strong>
                    </div>
                    <div class="signal-card">
                        <small>AI Engine</small>
                        <strong>Local Ollama</strong>
                    </div>
                    <div class="signal-card">
                        <small>Response Mode</small>
                        <strong>Triage Ready</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Indicators Found</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if indicators:
            st.markdown('<div class="indicator-list">', unsafe_allow_html=True)
            for item in indicators:
                st.markdown(f'<div class="indicator-item">{item}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="indicator-item">No major phishing indicators detected.</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="glass-card" style="margin-top: 1rem;">
                <div class="section-title">Recommendation</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if score >= 70:
            recommendation = (
                "Do not click links, download attachments, or reply. Escalate this message "
                "to your IT or security team immediately."
            )
        elif score >= 40:
            recommendation = (
                "Treat the message as suspicious. Verify the sender through a trusted channel "
                "before taking any action."
            )
        else:
            recommendation = (
                "No obvious phishing signs were detected, but continue with normal caution and "
                "verify anything unexpected."
            )
        st.markdown(
            f'<div class="recommendation-box">{recommendation}</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">URLs Found</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if urls:
            for url in urls:
                st.markdown(f'<div class="url-item mono">{url}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="url-item">No URLs found in this message.</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="glass-card" style="margin-top: 1rem;">
                <div class="section-title">AI Security Analysis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.spinner("Running local AI analysis..."):
            ai_response = ask_ai(email_text)
        st.markdown(
            f'<div class="url-item" style="white-space: pre-wrap;">{ai_response}</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()