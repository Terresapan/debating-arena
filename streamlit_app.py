import streamlit as st
from html import unescape
import re
from main import DebateManager, extract_text_from_multiple_files

# Load API keys from Streamlit secrets
openai_api_key = st.secrets["general"]["OPENAI_API_KEY"]
gemini_api_key = st.secrets["general"]["GEMINI_API_KEY"]

# Streamlit configuration
st.set_page_config(
    page_title="AI Debate Arena",
    page_icon="🎭",
)

# Custom CSS for styling the app
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .debate-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }
    .player-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: white;
    }
    .affirmative-avatar {
        background-color: #0288d1;
    }
    .negative-avatar {
        background-color: #c2185b;
    }
    .debate-content {
        flex: 1;
    }
    .affirmative {
        background-color: #e1f5fe;
    }
    .negative {
        background-color: #fce4ec;
    }
    .summary {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to sanitize text
def sanitize_text(text):
    """
    Remove all HTML tags, decode HTML entities, and strip Markdown special characters
    to ensure a plain text output.
    """
    # Remove all HTML tags
    text = re.sub(r'</?[^>]+>', '', text)

    # Decode HTML entities (e.g., &lt; -> <, &amp; -> &)
    text = unescape(text.strip())

    # Remove Markdown style characters (e.g., **, *)
    text = re.sub(r'\*\*|__|\*|_', '', text)  # Remove **, __, *, _
    text = re.sub(r'[`#]', '', text)          # Remove ` and #

    return text

# Function to run the debate and display progress
def run_debate_with_status(debate_manager, topic, affirmative_doc, negative_doc):
    """
    Orchestrate the AI debate and return outputs and summary.
    """
    try:
        with st.spinner("Generating debate..."):
            outputs, raw_summary = debate_manager.run_debate(topic, affirmative_doc, negative_doc)
            if outputs and raw_summary:
                # Sanitize the outputs and summary
                debate_outputs = [(side, sanitize_text(response)) for side, response in outputs]
                summary = sanitize_text(raw_summary)
                return debate_outputs, summary
            else:
                st.error("Failed to generate debate.")
                return None, None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None, None

# Main app logic
def main():
    st.title("🎭 AI Debate Arena")

    # Session state management for debates
    if 'debate_started' not in st.session_state:
        st.session_state.debate_started = False
    if 'debate_finished' not in st.session_state:
        st.session_state.debate_finished = False
    if 'debate_manager' not in st.session_state:
        st.session_state.debate_manager = DebateManager(openai_api_key, gemini_api_key)

    # Input section: Topic and document uploads
    topic = st.text_input(
        "Enter the debate topic:",
        placeholder="e.g., It is not necessary to study coding nowadays when AI becomes so powerful and it can do it for us."
    )
    st.markdown("### Upload Background Documents")

    # File uploaders for Affirmative and Negative sides
    affirmative_files = st.file_uploader(
        "Upload one or more documents for Affirmative side:",
        type=["pdf", "doc", "docx", "txt"],
        accept_multiple_files=True
    )
    negative_files = st.file_uploader(
        "Upload one or more documents for Negative side:",
        type=["pdf", "doc", "docx", "txt"],
        accept_multiple_files=True
    )

    # Extract text from uploaded files
    affirmative_doc = extract_text_from_multiple_files(affirmative_files) if affirmative_files else ""
    negative_doc = extract_text_from_multiple_files(negative_files) if negative_files else ""

    # Start Debate Button
    if st.button("Start Debate") and topic:
        if not affirmative_doc and not negative_doc:
            st.session_state.debate_started = True
            st.session_state.topic = topic
        elif affirmative_doc and negative_doc:
            st.session_state.debate_started = True
            st.session_state.topic = topic
            st.session_state.affirmative_doc = affirmative_doc
            st.session_state.negative_doc = negative_doc
        else:
            st.warning("Debate will start only with the topic if no documents are provided. Ensure both Affirmative and Negative documents are uploaded or none at all.")

        # Run the debate
        debate_outputs, summary = run_debate_with_status(
            st.session_state.debate_manager,
            topic,
            affirmative_doc,
            negative_doc
        )

        if debate_outputs and summary:
            st.session_state.debate_outputs = debate_outputs
            st.session_state.summary = summary
            st.session_state.debate_finished = True
            st.experimental_rerun()

    # Display debate progress and summary
    if st.session_state.debate_finished:
        st.subheader("Debate Progress")

        for i, (side, response) in enumerate(st.session_state.debate_outputs):
            round_num = (i // 2) + 1
            if side == "affirmative":
                st.markdown(f"""
                    <div class="debate-box affirmative">
                        <div class="player-avatar affirmative-avatar">A</div>
                        <div class="debate-content">
                            <strong>Round {round_num} - Affirmative:</strong><br>{response}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            elif side == "negative":
                st.markdown(f"""
                    <div class="debate-box negative">
                        <div class="player-avatar negative-avatar">N</div>
                        <div class="debate-content">
                            <strong>Round {round_num} - Negative:</strong><br>{response}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Display summary with a box style
        st.subheader("Debate Summary")
        st.markdown(f"""
            <div class="summary">
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)

     
if __name__ == "__main__":
    main()