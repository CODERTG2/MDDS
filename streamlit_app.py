import streamlit as st
import time

st.set_page_config(
    page_title="Medical Diagnostic Device Research",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="expanded"
)

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

# ---- Title and Greeting ----
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
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .search-container {
        position: relative;
        width: 100%;
    }
    .search-container input {
        width: 100%;
        padding-right: 40px;
    }
    .search-icon {
        position: absolute;
        right: 10px;
        top: 7px;
        color: gray;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.title("Customize")
    username = st.text_input("Your Name", value=st.session_state.username)
    if username != st.session_state.username:
        st.session_state.username = username
    temp = st.slider("Creativity (LLM Temperature)", 0.0, 1.0, st.session_state.temperature, 0.05)
    if temp != st.session_state.temperature:
        st.session_state.temperature = temp

    if st.checkbox("Dark Mode", value=st.session_state.dark_mode, key="dark_toggle"):
        st.session_state.dark_mode = True
    else:
        st.session_state.dark_mode = False

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
            }
            input, .stTextInput > div > div > input {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }
            .sidebar .stButton button, .stButton button {
                background-color: #444 !important;
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            input, .stTextInput > div > div > input {
                background-color: white !important;
                color: black !important;
            }
            .sidebar .stButton button, .stButton button {
                background-color: #f0f0f0 !important;
                color: black !important;
            }
        </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='title'>Medical Diagnostic Device Research</div>", unsafe_allow_html=True)

greeting = f"Hello {st.session_state.username}, what would you like to search?" if st.session_state.username else "What would you like to search?"
st.markdown(f"<div class='subtitle'>{greeting}</div>", unsafe_allow_html=True)

# ---- Search Field ----
with st.form(key="search_form", clear_on_submit=False):
    search_col = st.columns([10, 1])
    st.session_state.search_query = search_col[0].text_input(
        label="",
        value=st.session_state.search_query,
        placeholder="Search medical devices, papers, or terms...",
        label_visibility="collapsed"
    )
    submitted = search_col[1].form_submit_button("🔍")

# ---- Search Action ----
if submitted and st.session_state.search_query.strip():
    st.session_state.loading = True
    st.session_state.result_shown = False

# ---- Loading Spinner ----
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
        message_area.markdown(f"<p style='text-align:center; font-size:1.05rem;'>{step}</p>", unsafe_allow_html=True)
        time.sleep(1.1)

    loader_area.empty()
    message_area.empty()
    st.session_state.loading = False
    st.session_state.result_shown = True

# ---- Display Result ----
if st.session_state.result_shown:
    st.success(f"Results for: **{st.session_state.search_query}**")
