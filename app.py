
import streamlit as st
import html
import hashlib
import time
from src.speech.rewriter import rewrite_speech
from audio_recorder_streamlit import audio_recorder

from src.topic_generator import generate_topic
from src.config import (
    APP_NAME,
    APP_TAGLINE,
    CATEGORIES,
    DIFFICULTIES,
    DURATIONS
)

from src.speech.recorder import get_audio_duration
from src.speech.transcriber import transcribe_audio


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Vocalis | AI Speaking Coach",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #0b1020;
    color: #f1f5f9;
}

section[data-testid="stSidebar"] {
    background-color: #11182b;
    border-right: 1px solid #26314a;
}

.hero {
    padding: 35px;
    border-radius: 20px;
    background: linear-gradient(120deg, #22245c, #30245f, #172d55);
    border: 1px solid #454078;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 42px;
    font-weight: 800;
    color: white;
}

.hero p {
    color: #c4c8e9;
    font-size: 16px;
}

.section-card {
    background-color: #151e33;
    padding: 24px;
    border: 1px solid #293653;
    border-radius: 16px;
    margin-bottom: 20px;
}

.metric-card {
    background-color: #151e33;
    padding: 20px;
    border: 1px solid #293653;
    border-radius: 14px;
    text-align: center;
}

.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #a78bfa;
}

.metric-label {
    font-size: 13px;
    color: #9ca3af;
}

div.stButton > button {
    background: linear-gradient(90deg, #7c3aed, #6366f1);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 20px;
    font-weight: 600;
    width: 100%;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #6d28d9, #4f46e5);
    color: white;
    border: none;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "topic": None,
    "page": "Practice",

    "audio_bytes": None,
    "audio_duration": None,
    "transcript": None,

    "recording_active": False,
    "recording_started_at": None,
    "recording_id": 0,

    "last_audio_hash": None,

    "selected_duration": "2 Minutes",

    "rewritten_text": None,
    "rewritten_style": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# COUNTDOWN TIMER
# ==================================================

@st.fragment(run_every=1)
def show_recording_timer():

    if not st.session_state.recording_active:
        return

    started_at = st.session_state.recording_started_at

    selected_duration = st.session_state.selected_duration

    total_seconds = DURATIONS[selected_duration]

    elapsed = time.monotonic() - started_at

    remaining = max(
        0,
        total_seconds - int(elapsed)
    )

    minutes = remaining // 60
    seconds = remaining % 60

    progress = 1 - (remaining / total_seconds)

    st.markdown("### 🔴 Recording in progress")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(
            "Time remaining",
            f"{minutes:02d}:{seconds:02d}"
        )

    with col2:
        st.metric(
            "Selected duration",
            selected_duration
        )

    st.progress(progress)

    if remaining == 0:
        st.info(
            "Time is up! Your recording is being finalized."
        )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("# 🎙️ Vocalis")
    st.caption("YOUR PERSONAL AI SPEAKING COACH")

    st.divider()

    if st.button("🏠 Practice", use_container_width=True):
        st.session_state.page = "Practice"

    if st.button("📊 My Progress", use_container_width=True):
        st.session_state.page = "Progress"

    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.page = "Settings"

    st.divider()

    st.markdown("### Your daily goal")
    st.progress(0.0)
    st.caption("Complete your first speaking session!")

    st.divider()

    st.caption("Powered by LangGraph · Groq · Whisper")


# ==================================================
# PRACTICE PAGE
# ==================================================

if st.session_state.page == "Practice":

    # ----------------------------------------------
    # HERO
    # ----------------------------------------------

    st.markdown("""
    <div class="hero">
        <h1>Speak with Confidence. 🚀</h1>
        <p>
            Practice your English, discover your weaknesses,
            and become a better communicator every day.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------
    # SESSION CONFIGURATION
    # ----------------------------------------------

    st.markdown("## Start a speaking session")

    col1, col2 = st.columns(2)

    with col1:

        category = st.selectbox(
            "Choose your topic category",
            CATEGORIES
        )

    with col2:

        difficulty = st.selectbox(
            "Select difficulty",
            DIFFICULTIES,
            index=1
        )

    duration = st.selectbox(
        "Speaking duration",
        list(DURATIONS.keys()),
        index=2
    )

    # ----------------------------------------------
    # GENERATE TOPIC
    # ----------------------------------------------

    if st.button("✨ Generate Speaking Topic"):

        st.session_state.recording_active = False

        st.session_state.selected_category = category
        st.session_state.selected_difficulty = difficulty
        st.session_state.selected_duration = duration

        try:

            with st.spinner("Generating your speaking challenge..."):

                topic = generate_topic(
                    category=category,
                    difficulty=difficulty
                )

                if not topic:
                    raise ValueError("Empty topic received.")

                st.session_state.topic = topic

                # Reset previous recording
                st.session_state.audio_bytes = None
                st.session_state.audio_duration = None
                st.session_state.transcript = None

                st.session_state.last_audio_hash = None

                st.session_state.recording_id += 1

                st.session_state.rewritten_text = None
                st.session_state.rewritten_style = None

            st.success("Your speaking challenge is ready!")

        except Exception as e:

            st.error(f"Topic generation failed: {e}")

    # ----------------------------------------------
    # DISPLAY TOPIC ONLY ONCE
    # ----------------------------------------------

    st.markdown("---")
    st.markdown("## 🎯 Your speaking challenge")

    if st.session_state.topic:

        safe_topic = html.escape(st.session_state.topic)

        st.markdown(
            f"""
            <div class="section-card">
                <h2>{safe_topic}</h2>
                <p>Get ready to express your thoughts!</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.info("Generate a topic to begin your practice.")

    # ----------------------------------------------
    # SPEAKING STUDIO
    # ----------------------------------------------

    st.markdown("## 🎙️ Speaking studio")

    if not st.session_state.topic:

        st.info("Your microphone will appear after topic generation.")

    else:

        selected_duration = st.session_state.selected_duration

        max_duration = DURATIONS[selected_duration]

        st.caption(
            f"Your speaking time: {selected_duration}"
        )

        # ------------------------------------------
        # START RECORDING
        # ------------------------------------------

        if not st.session_state.recording_active:

            if st.session_state.audio_bytes is None:

                if st.button(
                    "🎙️ Start recording",
                    use_container_width=True
                ):

                    st.session_state.recording_active = True

                    st.session_state.recording_started_at = (
                        time.monotonic()
                    )

                    st.session_state.last_audio_hash = None

                    st.rerun()

        # ------------------------------------------
        # RECORDING TIMER
        # ------------------------------------------

        if st.session_state.recording_active:

            show_recording_timer()

            st.caption(
                "Your recording will automatically stop "
                "when the timer reaches zero. You can also "
                "stop it manually."
            )

            # --------------------------------------
            # AUDIO RECORDER
            # --------------------------------------

            audio_bytes = audio_recorder(
                text="Recording... Click to stop early",

                recording_color="#ef4444",
                neutral_color="#7c3aed",

                icon_name="microphone",
                icon_size="3x",

                energy_threshold=(-1.0, 1.0),

                pause_threshold=float(max_duration),

                sample_rate=16000,

                auto_start=True,

                key=f"recorder_{st.session_state.recording_id}"
            )

            # --------------------------------------
            # RECEIVE COMPLETED RECORDING
            # --------------------------------------

            if audio_bytes:

                audio_hash = hashlib.sha256(
                    audio_bytes
                ).hexdigest()

                if audio_hash != st.session_state.last_audio_hash:

                    st.session_state.recording_active = False

                    st.session_state.audio_bytes = audio_bytes

                    st.session_state.last_audio_hash = audio_hash

                    try:

                        duration_seconds = get_audio_duration(
                            audio_bytes
                        )

                        st.session_state.audio_duration = duration_seconds

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Could not read the recording: {e}"
                        )

        # ------------------------------------------
        # RECORDING PREVIEW
        # ------------------------------------------

        if st.session_state.audio_bytes:

            st.markdown("---")

            st.markdown("## 🔊 Your recording")

            st.success("Your recording has been saved!")

            st.audio(
                st.session_state.audio_bytes,
                format="audio/wav"
            )

            if st.session_state.audio_duration:

                st.metric(
                    "Recorded duration",
                    f"{st.session_state.audio_duration:.1f} seconds"
                )

            # --------------------------------------
            # TRANSCRIPTION
            # --------------------------------------

            if st.session_state.transcript is None:

                try:

                    with st.spinner(
                        "🎙️ Whisper is transcribing your speech..."
                    ):

                        transcript = transcribe_audio(
                            st.session_state.audio_bytes
                        )

                        st.session_state.transcript = transcript

                except Exception as e:

                    st.error(
                        f"Transcription failed: {e}"
                    )

                    if st.button("Retry transcription"):

                        st.rerun()

            # --------------------------------------
            # EDITABLE TRANSCRIPT
            # --------------------------------------

            if st.session_state.transcript:

                st.markdown("---")

                st.markdown("## 📝 Your speech transcript")

                st.caption(
                    "Your speech has been converted into text. "
                    "You can correct it below."
                )

                edited_transcript = st.text_area(
                    "Edit your transcript",

                    value=st.session_state.transcript,

                    height=250,

                    key=f"transcript_editor_{st.session_state.recording_id}"
                )

                st.session_state.transcript = edited_transcript

                word_count = len(
                    edited_transcript.split()
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Total words",
                        word_count
                    )

                with col2:

                    duration_seconds = (
                        st.session_state.audio_duration or 0
                    )

                    if duration_seconds > 0:

                        wpm = word_count / (
                            duration_seconds / 60
                        )

                        st.metric(
                            "Estimated speaking speed",
                            f"{wpm:.1f} WPM"
                        )

                st.success(
                    "Your transcript is ready for evaluation."
                )

                # ----------------------------------
                # AI SPEECH REWRITING
                # ----------------------------------

                st.markdown("---")

                st.markdown("## ✨ Improve your speech")

                st.caption(
                    "Choose how you want your speech to sound. "
                    "AI will correct your English while preserving "
                    "your original meaning."
                )

                rewriting_style = st.selectbox(
                    "Choose your communication style",

                    [
                        "Professional",
                        "Friendly",
                        "Formal",
                        "Conversational",
                        "Academic"
                    ],

                    key=f"rewrite_style_{st.session_state.recording_id}"
                )

                if st.button(
                    "✨ Improve My Speech",
                    use_container_width=True
                ):

                    if not st.session_state.transcript.strip():

                        st.warning(
                            "Please enter some speech before rewriting."
                        )

                    else:

                        try:

                            with st.spinner(
                                "✨ AI is improving your speech..."
                            ):

                                improved_text = rewrite_speech(
                                    transcript=st.session_state.transcript,
                                    style=rewriting_style
                                )

                                st.session_state.rewritten_text = improved_text

                                st.session_state.rewritten_style = rewriting_style

                        except Exception as e:

                            st.error(
                                f"Speech rewriting failed: {e}"
                            )

                # ----------------------------------
                # DISPLAY IMPROVED SPEECH
                # ----------------------------------

                if st.session_state.rewritten_text:

                    st.markdown("---")

                    st.markdown("## 🌟 Your improved speech")

                    st.caption(
                        f"Communication style: "
                        f"{st.session_state.rewritten_style}"
                    )

                    st.markdown(
                        """
                        <div class="section-card">
                            <h4>AI-corrected version</h4>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.text_area(
                        "Improved speech",
                        value=st.session_state.rewritten_text,
                        height=250,
                        disabled=True,
                        key=f"improved_text_{st.session_state.recording_id}"
                    )

                    st.download_button(
                        label="📥 Download Improved Speech",

                        data=st.session_state.rewritten_text,

                        file_name="improved_speech.txt",

                        mime="text/plain",

                        use_container_width=True
                    )


                # ----------------------------------
                # RECORD AGAIN
                # ----------------------------------

                if st.button("🔄 Record another attempt"):

                    st.session_state.audio_bytes = None
                    st.session_state.audio_duration = None
                    st.session_state.transcript = None

                    st.session_state.last_audio_hash = None

                    st.session_state.recording_id += 1
                    st.session_state.rewritten_text = None
                    st.session_state.rewritten_style = None

                    st.rerun()


# ==================================================
# PROGRESS PAGE
# ==================================================

elif st.session_state.page == "Progress":

    st.markdown("## 📊 Your progress")

    st.caption("Your performance analytics will appear here.")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">--</div>
            <div class="metric-label">Sessions completed</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:

        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">--</div>
            <div class="metric-label">Average score</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:

        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">--</div>
            <div class="metric-label">Speaking minutes</div>
        </div>
        """, unsafe_allow_html=True)


# ==================================================
# SETTINGS PAGE
# ==================================================

elif st.session_state.page == "Settings":

    st.markdown("## ⚙️ Settings")

    st.write("Application settings will be added here.")

    st.info(
        "Your AI model will use Groq GPT-OSS-20B."
    )
