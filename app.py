
import re
from pathlib import Path

import joblib
import streamlit as st


# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SmartSMS | Spam Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

MODEL_PATH = Path(__file__).resolve().parent / "sms_spam_model.pkl"

DEFAULT_SPAM_THRESHOLD = 0.50


# ============================================================
# 2. SECURITY RULES: SENSITIVE CREDENTIAL REQUESTS
# ============================================================

CREDENTIAL_REQUEST_PATTERNS = [
    (
        re.compile(
            r"\b(send|share|give|provide|tell|text|forward|"
            r"submit|reveal|disclose|enter)\b"
            r".{0,70}\b"
            r"(your\s+)?"
            r"((m[\s-]?pesa|mpesa|bank|account|card)\s+)?"
            r"(pin|password|passcode|otp|"
            r"one[\s-]?time[\s-]?password|"
            r"verification\s+code|security\s+code|cvv)\b",
            re.IGNORECASE
        ),
        "The message requests a sensitive PIN, password, OTP or security code."
    ),
    (
        re.compile(
            r"\b(reply|respond)\s+with\b.{0,50}\b"
            r"(pin|password|passcode|otp|verification\s+code|"
            r"security\s+code|cvv)\b",
            re.IGNORECASE
        ),
        "The message asks you to reply with a sensitive security credential."
    ),
    (
        re.compile(
            r"\b(m[\s-]?pesa|mpesa|bank)\s+pin\b"
            r".{0,60}\b(allocation|claim|unlock|verification|"
            r"activation|release|reward|processing)\b",
            re.IGNORECASE
        ),
        "The message connects a financial PIN with an allocation, claim or account action."
    )
]


PROTECTIVE_WARNING_PATTERN = re.compile(
    r"\b(never|don't|do\s+not|shouldn't|should\s+not|"
    r"must\s+not|cannot|can't|avoid)\b"
    r".{0,45}\b(send|share|give|provide|reveal|disclose)\b"
    r".{0,45}\b(pin|password|passcode|otp|verification\s+code|"
    r"security\s+code|cvv)\b",
    re.IGNORECASE
)


def detect_credential_risk(message):
    """
    Identify suspicious requests for sensitive credentials.

    Returns a warning explanation when a suspicious request
    is identified. Otherwise, returns None.
    """

    normalized_message = re.sub(r"\s+", " ", message).strip()

    sentences = re.split(r"(?<=[.!?])\s+", normalized_message)

    for sentence in sentences:

        # Do not flag a clear protective warning.
        if PROTECTIVE_WARNING_PATTERN.search(sentence):
            continue

        for pattern, reason in CREDENTIAL_REQUEST_PATTERNS:

            if pattern.search(sentence):
                return reason

    return None


# ============================================================
# 3. APPLICATION DESIGN
# ============================================================

st.markdown(
    """
    <style>
        .main .block-container {
            max-width: 1180px;
            padding: 2rem clamp(1rem, 4vw, 3rem) 3rem;
        }

        .stApp {
            background:
                radial-gradient(ellipse at 82% 4%, rgba(52, 180, 161, .13), transparent 34rem),
                radial-gradient(ellipse at 6% 38%, rgba(89, 134, 220, .10), transparent 30rem);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            opacity: .16;
            background-image: radial-gradient(rgba(128, 155, 176, .55) 0.65px, transparent 0.65px);
            background-size: 24px 24px;
            mask-image: linear-gradient(to bottom, black, transparent 70%);
        }

        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stSidebar"] {
            position: relative;
            z-index: 1;
        }

        .smart-hero {
            position: relative;
            display: flex;
            min-height: 250px;
            align-items: center;
            justify-content: space-between;
            gap: 2rem;
            overflow: hidden;
            padding: clamp(1.7rem, 5vw, 3.4rem);
            border: 1px solid rgba(255, 255, 255, .16);
            border-radius: 28px;
            color: #f7fbff;
            background:
                radial-gradient(circle at 83% 12%, rgba(87, 226, 201, .24), transparent 22rem),
                linear-gradient(118deg, #10243b 0%, #173c55 58%, #155a61 100%);
            box-shadow: 0 24px 70px rgba(19, 51, 74, .18);
            animation: hero-arrive .7s ease-out both;
        }

        .smart-hero::before,
        .smart-hero::after {
            content: "";
            position: absolute;
            border: 1px solid rgba(167, 244, 224, .18);
            border-radius: 50%;
            pointer-events: none;
            animation: float-orbit 12s ease-in-out infinite alternate;
        }

        .smart-hero::before {
            width: 290px;
            height: 290px;
            right: 7%;
            top: -175px;
        }

        .smart-hero::after {
            width: 390px;
            height: 390px;
            right: -2%;
            bottom: -315px;
            animation-delay: -5s;
        }

        .hero-copy {
            position: relative;
            z-index: 1;
            max-width: 700px;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: .55rem;
            margin-bottom: .85rem;
            color: #a7f4e0;
            font-size: .75rem;
            font-weight: 750;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .hero-eyebrow::before {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #64e3c2;
            box-shadow: 0 0 16px rgba(100, 227, 194, .9);
            content: "";
        }

        .smart-hero h1 {
            margin: 0;
            color: #fff;
            font-size: clamp(2.15rem, 5vw, 3.7rem);
            font-weight: 760;
            letter-spacing: -.055em;
            line-height: 1.04;
        }

        .smart-hero p {
            max-width: 560px;
            margin: 1rem 0 0;
            color: #d3e2ed;
            font-size: clamp(1rem, 2vw, 1.12rem);
            line-height: 1.65;
        }

        .hero-mark {
            position: relative;
            z-index: 1;
            display: grid;
            width: 116px;
            height: 116px;
            flex: 0 0 116px;
            place-items: center;
            border: 1px solid rgba(202, 255, 242, .28);
            border-radius: 32px;
            color: #a7f4e0;
            background: rgba(224, 255, 248, .08);
            box-shadow: inset 0 1px rgba(255, 255, 255, .12), 0 18px 45px rgba(1, 21, 33, .22);
            backdrop-filter: blur(8px);
            transform: rotate(4deg);
            animation: mark-bob 5s ease-in-out infinite;
        }

        .hero-mark svg {
            width: 64px;
            height: 64px;
        }

        div.stButton > button {
            min-height: 48px;
            border-radius: 13px;
            font-weight: 700;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 9px 22px rgba(23, 60, 85, .14);
        }

        div[data-testid="stTextArea"] textarea {
            min-height: 155px;
            border-radius: 16px;
            border-color: rgba(128, 150, 170, .42);
            line-height: 1.65;
            transition: border-color .18s ease, box-shadow .18s ease;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: #27a99a;
            box-shadow: 0 0 0 3px rgba(39, 169, 154, .20);
        }

        [data-testid="stMetric"] {
            min-height: 112px;
            padding: 18px 20px;
            border: 1px solid rgba(128, 150, 170, .34);
            border-radius: 18px;
            background: transparent;
            box-shadow: 0 8px 26px rgba(20, 50, 75, .07);
        }

        [data-testid="stAlert"] {
            border-radius: 16px;
        }

        [data-testid="stExpander"] {
            border-color: rgba(128, 150, 170, .34);
            border-radius: 14px;
            background: transparent;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 150, 170, .30);
        }

        @keyframes hero-arrive {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float-orbit {
            from { transform: translate3d(0, 0, 0); }
            to { transform: translate3d(-12px, 10px, 0); }
        }

        @keyframes mark-bob {
            0%, 100% { transform: translateY(0) rotate(4deg); }
            50% { transform: translateY(-7px) rotate(1deg); }
        }

        @media (max-width: 640px) {
            .main .block-container {
                padding: 1rem 1rem 2rem;
            }

            .smart-hero {
                min-height: 0;
                gap: .75rem;
                border-radius: 22px;
            }

            .hero-mark {
                width: 62px;
                height: 62px;
                flex-basis: 62px;
                border-radius: 19px;
            }

            .hero-mark svg {
                width: 36px;
                height: 36px;
            }

            .smart-hero h1 {
                font-size: clamp(2rem, 9vw, 2.7rem);
            }
        }

        @media (max-width: 420px) {
            .smart-hero {
                align-items: flex-start;
            }

            .hero-mark {
                width: 48px;
                height: 48px;
                flex-basis: 48px;
                border-radius: 15px;
            }

            .hero-mark svg {
                width: 28px;
                height: 28px;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                animation-duration: .01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: .01ms !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 4. LOAD THE TRAINED MACHINE-LEARNING MODEL
# ============================================================

@st.cache_resource
def load_model():

    loaded_object = joblib.load(MODEL_PATH)

    # Support a model bundle:
    # {
    #     "model": trained_pipeline,
    #     "spam_threshold": 0.35,
    #     "metrics": {...}
    # }

    if isinstance(loaded_object, dict):

        if "model" not in loaded_object:
            raise ValueError(
                "The saved model bundle does not contain a model."
            )

        model = loaded_object["model"]

        threshold = float(
            loaded_object.get(
                "spam_threshold",
                DEFAULT_SPAM_THRESHOLD
            )
        )

        metrics = loaded_object.get("metrics", {})

    else:

        # Support the original directly saved pipeline.
        model = loaded_object

        threshold = DEFAULT_SPAM_THRESHOLD

        metrics = {}

    if not 0 < threshold < 1:
        raise ValueError(
            "The spam threshold must be between 0 and 1."
        )

    if not hasattr(model, "predict_proba"):
        raise ValueError(
            "The trained model does not support probability predictions."
        )

    if not hasattr(model, "classes_"):
        raise ValueError(
            "The trained model does not expose its class labels."
        )

    return model, threshold, metrics


# ============================================================
# 5. CHECK MODEL AVAILABILITY
# ============================================================

if not MODEL_PATH.exists():

    st.error(
        "Trained model not found. "
        "Please run python train_model.py in your project directory."
    )

    st.stop()


try:

    model, spam_threshold, model_metrics = load_model()

except Exception as error:

    st.error(
        "Unable to load the trained model. "
        "Check that the model file is valid and compatible "
        "with your installed libraries."
    )

    # Display a short diagnostic message, not a full traceback.
    st.caption(f"Technical detail: {error}")

    st.stop()


# ============================================================
# 6. SESSION STATE AND CALLBACKS
# ============================================================

if "sms_input" not in st.session_state:
    st.session_state.sms_input = ""

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "sample_selection" not in st.session_state:
    st.session_state.sample_selection = "Choose a sample message"

if "last_sample_selection" not in st.session_state:
    st.session_state.last_sample_selection = "Choose a sample message"


def clear_message():
    """Clear the input and previous analysis."""

    st.session_state.sms_input = ""

    st.session_state.analysis_result = None

    st.session_state.sample_selection = "Choose a sample message"

    st.session_state.last_sample_selection = "Choose a sample message"


# ============================================================
# 7. APPLICATION HERO HEADER
# ============================================================

st.markdown(
    """
    <section class="smart-hero" aria-label="SmartSMS message safety">
        <div class="hero-copy">
            <div class="hero-eyebrow">A clearer view of your messages</div>
            <h1>Pause before you reply.</h1>
            <p>Check a text for spam signals and risky requests for personal information.</p>
        </div>
        <div class="hero-mark" aria-hidden="true">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M32 6 52 14v15c0 13-8.3 23.2-20 29C20.3 52.2 12 42 12 29V14L32 6Z" stroke="currentColor" stroke-width="3.5" stroke-linejoin="round"/>
                <path d="M23 29h18a4 4 0 0 1 4 4v9H19v-9a4 4 0 0 1 4-4Z" stroke="currentColor" stroke-width="3.5" stroke-linejoin="round"/>
                <path d="M25 29v-5a7 7 0 0 1 14 0v5" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
                <circle cx="32" cy="36" r="2" fill="currentColor"/>
            </svg>
        </div>
    </section>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 8. SIDEBAR: SAFETY INFORMATION
# ============================================================

with st.sidebar:

    st.markdown("## :material/security: How it works")

    st.write(
        "SmartSMS checks message patterns and screens for requests "
        "for passwords, PINs and one-time codes."
    )

    st.divider()

    st.markdown("### :material/tips_and_updates: Stay safer")

    st.caption(
        "Never share a PIN, password or one-time code in response "
        "to a message. If unsure, contact the organization using "
        "a trusted number."
    )

    with st.expander("Screening details"):
        st.caption(
            "The text classifier uses a spam threshold of "
            f"{spam_threshold:.2f}. Credential-safety rules can "
            "also raise a high-risk warning."
        )

# ============================================================
# 9. SMS INPUT SECTION
# ============================================================

st.divider()

st.markdown("## :material/sms: Check a message")

st.write(
    "Paste a text message or choose an example to get a safety check."
)


# ============================================================
# 10. SAMPLE SMS MESSAGES
# ============================================================

EXAMPLES = {

    "Choose a sample message": "",

    "Legitimate example": (
        "Hey, are we still meeting tomorrow?"
    ),

    "Traditional spam example": (
        "WINNER! You have won a FREE cash prize. "
        "Call now to claim your reward!"
    ),

    "Mobile money notification": (
        "Your account has received a payment. "
        "Thank you for using our service."
    ),

    "M-Pesa PIN scam example": (
        "Send us your M-Pesa PIN number for allocation."
    ),

    "OTP request example": (
        "Share your OTP to receive your reward immediately."
    ),

    "Security warning example": (
        "Never share your M-Pesa PIN with anyone."
    ),

    "Suspicious account message": (
        "URGENT! Your account will be blocked. "
        "Send us your password immediately."
    )
}


selected_example = st.selectbox(
    "Try a sample message",
    options=list(EXAMPLES.keys()),
    key="sample_selection"
)


# Update the input when a different sample is selected.

if selected_example != st.session_state.last_sample_selection:

    st.session_state.sms_input = EXAMPLES[selected_example]

    st.session_state.analysis_result = None

    st.session_state.last_sample_selection = selected_example


message = st.text_area(
    "Message text",
    key="sms_input",
    height=155,
    max_chars=5000,
    placeholder="Paste or type the message you want to check...",
    help="Your message can contain up to 5,000 characters."
)

st.caption(f"{len(message)} / 5,000 characters")


# ============================================================
# 11. ACTION BUTTONS
# ============================================================

analyze_column, clear_column = st.columns([3, 1])


with analyze_column:

    analyze_clicked = st.button(
        "Analyze Message",
        use_container_width=True,
        type="primary"
    )


with clear_column:

    st.button(
        "Clear",
        use_container_width=True,
        on_click=clear_message
    )


# ============================================================
# 12. CLASSIFY THE SMS MESSAGE
# ============================================================

if analyze_clicked:

    current_message = st.session_state.sms_input.strip()

    if not current_message:

        st.warning(
            "Please enter an SMS message before analysing."
        )

        st.session_state.analysis_result = None

    else:

        try:

            # Obtain ML probabilities.
            probabilities = model.predict_proba([current_message])[0]

            classes = [
                str(class_name).strip().lower()
                for class_name in model.classes_
            ]

            if "spam" not in classes or "ham" not in classes:

                raise ValueError(
                    "The model must contain both spam and ham classes."
                )

            spam_index = classes.index("spam")

            ham_index = classes.index("ham")

            spam_probability = float(probabilities[spam_index])

            ham_probability = float(probabilities[ham_index])
            
            # Additional credential security screening.
            security_warning = detect_credential_risk(current_message)

            # Preserve the actual machine-learning probabilities.
            ml_spam_probability = spam_probability
            ml_ham_probability = ham_probability

            if security_warning:
                prediction = "spam"
                detection_method = "Security rule"

                # The system has identified a high-risk credential request.
                # This is a rule-based risk indicator, NOT an ML probability.
                system_spam_score = 0.99
                system_ham_score = 0.01

            elif spam_probability >= spam_threshold:
                prediction = "spam"
                detection_method = "Text classifier"

                system_spam_score = spam_probability
                system_ham_score = ham_probability

            else:
                prediction = "ham"
                detection_method = "Text classifier"

                system_spam_score = spam_probability
                system_ham_score = ham_probability

            # Save the analysis for display.
            st.session_state.analysis_result = {
                "message": current_message,
                "prediction": prediction,

                # Overall system risk assessment.
                "spam_probability": system_spam_score,
                "ham_probability": system_ham_score,

                # Original machine-learning output.
                "ml_spam_probability": ml_spam_probability,
                "ml_ham_probability": ml_ham_probability,

                "security_warning": security_warning,
                "detection_method": detection_method
            }

        except Exception as error:

            st.session_state.analysis_result = None

            st.error(
                "The message could not be analysed. "
                "Please check the model and try again."
            )

            st.caption(f"Technical detail: {error}")


# ============================================================
# 13. DISPLAY ANALYSIS RESULTS
# ============================================================

result = st.session_state.analysis_result


if result:

    st.divider()

    st.markdown("## :material/analytics: Analysis Result")

    prediction = result["prediction"]

    security_warning = result["security_warning"]

    detection_method = result["detection_method"]


    # --------------------------------------------------------
    # HIGH-RISK CREDENTIAL REQUEST
    # --------------------------------------------------------

    if security_warning:

        with st.container(border=True):

            st.warning(
                "**:material/warning: HIGH-RISK CREDENTIAL REQUEST**"
            )

            st.write(
                "This message appears to request sensitive "
                "security information."
            )

        st.error(
            f"Security warning: {security_warning}"
        )

        st.warning(
            "Never disclose your M-Pesa PIN, bank PIN, password "
            "or OTP to someone through an SMS or message."
        )


    # --------------------------------------------------------
    # POTENTIAL SPAM
    # --------------------------------------------------------

    elif prediction == "spam":

        with st.container(border=True):

            st.error(
                "**:material/gpp_bad: POTENTIAL SPAM DETECTED**"
            )

            st.write(
                "The message crossed the spam-risk threshold."
            )

        st.warning(
            "Be cautious before replying, sharing personal "
            "information or opening links in this message."
        )


    # --------------------------------------------------------
    # LEGITIMATE MESSAGE
    # --------------------------------------------------------

    else:

        with st.container(border=True):

            st.success(
                "**:material/check_circle: LEGITIMATE MESSAGE**"
            )

            st.write(
                "No strong spam indicators were identified "
                "by the system."
            )

        st.info(
            "A legitimate classification does not prove that "
            "the sender is genuine or that the message is safe."
        )

    # --------------------------------------------------------
    # SYSTEM RISK ASSESSMENT
    # --------------------------------------------------------

    st.markdown("### :material/bar_chart: Risk assessment")

    metric_one, metric_two = st.columns(2)

    # Use one shared system score for all displayed indicators.
    system_spam_score = result["spam_probability"]
    system_ham_score = result["ham_probability"]

    with metric_one:
        st.metric(
            "Spam risk score",
            f"{system_spam_score * 100:.2f}%"
        )

    with metric_two:
        st.metric(
            "Legitimate score",
            f"{system_ham_score * 100:.2f}%"
        )

    st.caption(
        f"Detection method: {detection_method}"
    )

    st.caption(
        f"Screening threshold: {spam_threshold:.2f}"
    )

    # Progress bar uses exactly the same score as the metric.
    st.progress(
        max(0.0, min(1.0, system_spam_score)),
        text="Estimated system spam risk indicator"
    )

    with st.expander("View classifier scores"):
        st.caption(
            f"Classifier spam score: "
            f"{result['ml_spam_probability'] * 100:.2f}%"
            f" | Legitimate score: "
            f"{result['ml_ham_probability'] * 100:.2f}%"
        )

    # --------------------------------------------------------
    # SAFETY INFORMATION
    # --------------------------------------------------------

    with st.container(border=True):

        st.markdown("**:material/info: Important Safety Note**")

        st.write(
            "SmartSMS combines message screening with credential-safety "
            "checks. A suspicious request for a PIN, password or "
            "one-time code can raise the risk indicator regardless of "
            "the classifier score. This indicator is not a verified "
            "probability of fraud."
        )


# ============================================================
# 14. PROJECT FOOTER
# ============================================================

st.divider()

st.markdown(
    "**SmartSMS** · A second look at suspicious texts"
)
