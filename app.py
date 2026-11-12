
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
    layout="centered",
    initial_sidebar_state="expanded"
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
        /* Main application width */

        .main .block-container {
            max-width: 900px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Hero section */

        .hero-container {
            padding-top: 12px;
            padding-bottom: 12px;
        }

        /* Buttons */

        div.stButton > button {
            border-radius: 9px;
            font-weight: 650;
            min-height: 43px;
        }

        /* Text input */

        div[data-testid="stTextArea"] textarea {
            border-radius: 10px;
        }

        /* Metric cards */

        [data-testid="stMetric"] {
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            min-height: 100px;
        }

        /* Sidebar */

        section[data-testid="stSidebar"] {
            border-right: 1px solid var(--border-color);
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

with st.container(border=True):

    st.markdown(
        "<div class='hero-container'>",
        unsafe_allow_html=True
    )

    st.title(":material/shield: SmartSMS")

    st.markdown(
        "**AI-Powered SMS Spam Detection System**"
    )

    st.caption(
        "ARTIFICIAL INTELLIGENCE  |  NLP  |  MACHINE LEARNING"
    )


# ============================================================
# 8. SIDEBAR: PROJECT INFORMATION
# ============================================================

with st.sidebar:

    st.markdown("## :material/security: About SmartSMS")

    st.write(
        "SmartSMS uses Machine Learning and Natural Language "
        "Processing to analyse SMS messages and identify "
        "potential spam."
    )

    st.divider()

    st.markdown("### :material/code: Technology Stack")

    st.write("**Programming:** Python")

    st.write("**Data processing:** Pandas")

    st.write("**Machine Learning:** Scikit-learn")

    st.write("**Text processing:** TF-IDF")

    st.write("**Classification:** Naive Bayes")

    st.write("**Interface:** Streamlit")

    st.divider()

    st.markdown("### :material/search: Detection Methods")

    st.write("1. Machine Learning classification")

    st.write("2. Sensitive credential screening")

    st.divider()

    st.caption("Academic AI/ML project")

    st.caption(
        "SmartSMS is an assistance tool. "
        "It cannot guarantee that a message is safe."
    )

    st.divider()

    st.caption(
        f"Current ML spam threshold: {spam_threshold:.2f}"
    )


# ============================================================
# 9. SMS INPUT SECTION
# ============================================================

st.divider()

st.markdown("## :material/sms: Analyze an SMS Message")

st.write(
    "Paste or type an SMS message below to check for potential spam."
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
    "SMS Message",
    key="sms_input",
    height=155,
    max_chars=5000,
    placeholder="Type or paste your SMS message here..."
)


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
                detection_method = "Machine learning"

                system_spam_score = spam_probability
                system_ham_score = ham_probability

            else:
                prediction = "ham"
                detection_method = "Machine learning"

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
                "The machine-learning model classified this "
                "message as potential spam."
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

    st.markdown("### :material/bar_chart: System Risk Assessment")

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
        f"ML spam threshold: {spam_threshold:.2f}"
    )

    # Progress bar uses exactly the same score as the metric.
    st.progress(
        max(0.0, min(1.0, system_spam_score)),
        text="Estimated system spam risk indicator"
    )

    # Display the actual machine-learning probabilities separately.
    st.caption(
        f"Original ML spam score: "
        f"{result['ml_spam_probability'] * 100:.2f}%"
        f" | Original ML ham score: "
        f"{result['ml_ham_probability'] * 100:.2f}%"
    )

    # --------------------------------------------------------
    # SAFETY INFORMATION
    # --------------------------------------------------------

    with st.container(border=True):

        st.markdown("**:material/info: Important Safety Note**")

        st.write(
            "SmartSMS combines machine-learning classification with "
            "additional security screening. When a suspicious request "
            "for a PIN, password or OTP is detected, the system assigns "
            "a high-risk indicator even if the machine-learning model "
            "returns a low spam score. The system risk indicator is not "
            "a statistically verified probability of fraud."
        )


# ============================================================
# 14. PROJECT FOOTER
# ============================================================

st.divider()

st.markdown(
    "**SmartSMS** | AI-Powered SMS Spam Detection System"
)

st.caption(
    "Built with Python, Natural Language Processing "
    "and Machine Learning."
)

st.caption("Academic AI/ML Project")
