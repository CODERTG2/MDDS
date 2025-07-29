import streamlit as st
import time

st.set_page_config(
    page_title="Medical Diagnostic Device Research",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---- Custom CSS including flip button ----
st.markdown("""
<style>
html, body, [class*="css"] {
  font-family: 'Segoe UI', sans-serif;
  transition: background-color 0.6s ease, color 0.6s ease;
}
.title {
  font-size: 2.2rem;
  font-weight: bold;
  text-align: center;
  margin-top: 1rem;
}
.subtitle {
  font-size: 1.2rem;
  text-align: center;
  margin-bottom: 2rem;
  color: #999;
}
.loader {
  border: 6px solid #f3f3f3;
  border-top: 6px solid #3498db;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}
@keyframes spin {
  0% { transform: rotate(0deg);}
  100% { transform: rotate(360deg);}
}

/* Flip Button */
.flip-btn {
  background-color: #0e1117;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  width: 130px;
  height: 40px;
  border-radius: 5px;
  border: none;
  cursor: pointer;
  perspective: 600px;
  position: relative;
  outline: none;
}
</style>
""", unsafe_allow_html=True)

# ---- Session State ----
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "loading" not in st.session_state:
    st.session_state.loading = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.3
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "result_shown" not in st.session_state:
    st.session_state.result_shown = False

# ---- Sidebar ----
with st.sidebar:
    st.title("Customize")
    st.session_state.username = st.text_input("Your Name", value=st.session_state.username)
    st.markdown("---")
    st.session_state.temperature = st.slider(
        "Creativity (LLM Temperature)",
        min_value=0.0, max_value=1.0,
        value=st.session_state.temperature,
        step=0.05,
        help="Higher values make the LLM more creative and open-ended."
    )
    st.markdown("---")
    st.session_state.dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)
    if st.button("🧹 Clear Chat"):
        st.session_state.search_query = ""
        st.session_state.result_shown = False
        st.session_state.loading = False

# ---- Dark Mode Styling ----
if st.session_state.dark_mode:
    st.markdown("""
        <style>
            body, .main, .stApp {
                background-color: #0e1117 !important;
                color: #FAFAFA !important;
                transition: background-color 0.6s ease, color 0.6s ease;
            }
            .stTextInput > div > div > input {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }
            .stButton > button {
                background-color: #1f77b4 !important;
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            body, .main, .stApp {
                background-color: white !important;
                color: black !important;
                transition: background-color 0.6s ease, color 0.6s ease;
            }
            .stTextInput > div > div > input {
                background-color: white !important;
                color: black !important;
            }
            .stButton > button {
                background-color: #0e1117 !important;
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)

# ---- Main Title & Greeting ----
st.markdown("<div class='title'>Medical Diagnostic Device Research</div>", unsafe_allow_html=True)

if st.session_state.username.strip():
    greeting = f"Hello {st.session_state.username.strip()}, what would you like to search?"
else:
    greeting = "What would you like to search?"

st.markdown(f"<div class='subtitle'>{greeting}</div>", unsafe_allow_html=True)

# ---- Search Input ----
search_query = st.text_input(
    label="",
    value=st.session_state.search_query,
    key="search_query",
    placeholder="Search medical devices, papers, or terms...",
    label_visibility="collapsed"
)

# ---- Flip Button ----
clicked = st.button(label="", key="search_btn")

# ---- Button Styling ----
st.markdown("""
<style>
div[role="button"][data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  width: 130px !important;
  height: 40px !important;
  cursor: pointer !important;
  perspective: 600px;
  position: relative;
  outline: none !important;
}
div[role="button"][data-testid="stButton"] > button > span {
  display: block !important;
  position: relative !important;
  width: 130px !important;
  height: 40px !important;
  text-align: center !important;
  transition: transform 0.6s !important;
  transform-style: preserve-3d !important;
  border-radius: 5px !important;
  box-shadow:
    inset 2px 2px 2px 0px rgba(255,255,255,0.5),
    7px 7px 20px 0px rgba(0,0,0,0.1),
    4px 4px 5px 0px rgba(0,0,0,0.1) !important;
  background: linear-gradient(0deg, rgba(0,172,238,1) 0%, rgba(2,126,251,1) 100%) !important;
  color: white !important;
  line-height: 40px !important;
  font-weight: 600 !important;
  font-size: 1rem !important;
  user-select: none !important;
}
div[role="button"][data-testid="stButton"]:hover > button > span {
  transform: rotateX(90deg) !important;
  background: linear-gradient(0deg, rgba(14,17,23,1) 0%, rgba(14,17,23,1) 100%) !important;
  color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ---- Trigger Search ----
if clicked and search_query.strip():
    st.session_state.loading = True
    st.session_state.search_query = search_query.strip()
    st.session_state.result_shown = False

# ---- Loading Simulation ----
if st.session_state.loading:
    loader_area = st.empty()
    message_area = st.empty()

    loader_area.markdown('<div class="loader"></div>', unsafe_allow_html=True)

    steps = [
        "Creating subqueries from your query...",
        "Searching vector DB for each subquery...",
        "Running Graph-RAG and collecting related nodes...",
        "Feeding context into the LLM...",
        "Cross-checking intersections between retrieved articles...",
        "Ranking by match count and semantic relevance..."
    ]

    for step in steps:
        message_area.markdown(
            f"<p style='text-align:center; font-size:1.05rem;'>{step}</p>",
            unsafe_allow_html=True
        )
        time.sleep(1.1)

    loader_area.empty()
    message_area.empty()
    st.session_state.loading = False
    st.session_state.result_shown = True

# ---- Result ----
if st.session_state.result_shown:
    st.success(f"Results for: **{st.session_state.search_query}**")
