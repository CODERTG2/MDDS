import streamlit as st
import time
from src.main import normal_search, deep_search

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
    st.session_state.temperature = 0.5
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "result_shown" not in st.session_state:
    st.session_state.result_shown = False
if "search_result" not in st.session_state:
    st.session_state.search_result = ""
if "deep_search" not in st.session_state:
    st.session_state.deep_search = False

# ---- Title Styling ----
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
        transition: color 0.6s ease;
    }
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
        transition: color 0.6s ease;
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
    /* Logo styling */
    .logo-top-right {
        position: fixed;
        top: 3rem;
        right: 0.5rem;
        width: 160px;
        height: auto;
        z-index: 9999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        background: transparent;
        pointer-events: none;
    }
    </style>
""", unsafe_allow_html=True)



# Display logo in top right using absolute positioning and base64
import base64
with open("assets/img_0003.png", "rb") as img_file:
    img_base64 = base64.b64encode(img_file.read()).decode()
logo_html = f'''<img src="data:image/png;base64,{img_base64}" class="logo-top-right" alt="Logo"/>'''
st.markdown(logo_html, unsafe_allow_html=True)


# ---- Dark Mode Styling ----   
st.markdown("""
    <style>
    button[data-testid="stButton"], .stButton button {
        border: 2px solid #444 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 5px !important;
        font-size: 0.9rem !important;
        display: inline-block !important;
        width: 100% !important;
        text-align: center !important;
        background: white !important;
        color: #222 !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        transition: background 0.3s, color 0.3s;
    }
    button[data-testid="stButton"]:hover, .stButton button:hover {
        background: #444 !important;
        color: white !important;
        border-color: #222 !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    html, body, [class*="css"], body, .main, .stApp {
        transition: background-color 0.6s ease, color 0.6s ease;
    }
    button[data-testid="stButton"], .stButton button {
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 5px !important;
        font-size: 0.9rem !important;
        display: inline-block !important;
        width: 100% !important;
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

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
                border: 1px solid #444 !important;
            }
            ::placeholder {
                color: #BBBBBB !important;
            }
            /* Button styling for dark mode - use light background with dark text for contrast */
            .sidebar .stButton button, button[data-testid="stButton"] {
                background-color: #f8f9fa !important;
                color: #333333 !important;
                border: 1px solid #666 !important;
            }
            .sidebar .stButton button:hover, button[data-testid="stButton"]:hover {
                background-color: #e9ecef !important;
                color: #222222 !important;
            }
            /* Force button text to be dark for readability */
            button[data-testid="stButton"] *, .stButton button * {
                color: #333333 !important;
            }
            section[data-testid="stSidebar"], .sidebar-content {
                background-color: #0e1117 !important;
                color: #FAFAFA !important;
            }
            .stTextInput label, .stSlider label, .stCheckbox label {
                color: #FAFAFA !important;
            }
            .stMarkdown, .stMarkdown p, .stMarkdown div {
                color: #FAFAFA !important;
            }
            .title {
                color: #FAFAFA !important;
            }
            .subtitle {
                color: #BBBBBB !important;
            }
            /* Fix all text elements except buttons */
            p:not(button p), div:not(button div), span:not(button span), label:not(button label) {
                color: #FAFAFA !important;
            }
            /* Fix success messages */
            .stAlert, .stSuccess, .stInfo {
                color: #FAFAFA !important;
                opacity: 1 !important;
                visibility: visible !important;
            }
            /* Force success message brightness */
            .stAlert *, .stSuccess *, .stInfo * {
                color: #FAFAFA !important;
                opacity: 1 !important;
            }
            /* Fix success message backgrounds */
            .stSuccess {
                background-color: rgba(40, 167, 69, 0.2) !important;
                border: 1px solid #28a745 !important;
            }
            /* Fix code blocks */
            code, pre {
                background-color: #1a1a1a !important;
                color: #FAFAFA !important;
                border: 1px solid #444 !important;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>  
            body, .main, .stApp {
                background-color: white !important;
                color: #333333 !important;
            }
            input, .stTextInput > div > div > input {
                background-color: white !important;
                color: #333333 !important;
                border: 1px solid #ddd !important;
            }
            ::placeholder {
                color: #666666 !important;
            }
            /* Button styling for light mode */
            .sidebar .stButton button, button[data-testid="stButton"] {
                background-color: #f0f0f0 !important;
                color: #333333 !important;
                border: 1px solid #ccc !important;
            }
            .sidebar .stButton button:hover, button[data-testid="stButton"]:hover {
                background-color: #e0e0e0 !important;
                color: #222222 !important;
            }
            /* Force button text to be dark */
            button[data-testid="stButton"] *, .stButton button * {
                color: #333333 !important;
            }
            section[data-testid="stSidebar"], .sidebar-content {
                background-color: #fafafa !important;
                color: #333333 !important;
            }
            .stTextInput label, .stSlider label, .stCheckbox label {
                color: #333333 !important;
            }
            .stMarkdown, .stMarkdown p, .stMarkdown div {
                color: #333333 !important;
            }
            .title {
                color: #1f2937 !important;
            }
            .subtitle {
                color: #6b7280 !important;
            }
            /* Fix all text elements except buttons */
            p:not(button p), div:not(button div), span:not(button span), label:not(button label) {
                color: #333333 !important;
            }
            /* Fix success messages */
            .stAlert, .stSuccess, .stInfo {
                color: #333333 !important;
                opacity: 1 !important;
                visibility: visible !important;
            }
            /* Force success message brightness */
            .stAlert *, .stSuccess *, .stInfo * {
                color: #333333 !important;
                opacity: 1 !important;
            }
            /* Fix success message backgrounds */
            .stSuccess {
                background-color: rgba(40, 167, 69, 0.1) !important;
                border: 1px solid #28a745 !important;
            }
            /* Fix code blocks */
            code, pre {
                background-color: #f8f9fa !important;
                color: #333333 !important;
                border: 1px solid #e9ecef !important;
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

    dark_mode_label = "Dark Mode"
    dark_toggle = st.checkbox(dark_mode_label, value=st.session_state.dark_mode)
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
        div[data-testid="stSidebar"] label[for="dark_mode"] {
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    if st.button("🧹 Clear Chat", key="clear_chat_btn", help="Clear chat", args=None):
        st.session_state.search_query = ""
        st.session_state.search_result = ""
        st.session_state.result_shown = False
        st.session_state.loading = False
        # Reset typing animation states
        st.session_state.typing_complete = False
        st.session_state.typing_position = 0
        st.session_state.typing_active = False

# ---- Title & Greeting ----
st.markdown("<div class='title'>Medical Diagnostic Device Research</div>", unsafe_allow_html=True)
greeting = f"Hello {st.session_state.username}, what would you like to search?" if st.session_state.username else "What would you like to search?"
st.markdown(f"<div class='subtitle'>{greeting}</div>", unsafe_allow_html=True)

# ---- Search Field ----
with st.form(key="search_form", clear_on_submit=False):
    search_col = st.columns([10, 1])
    st.session_state.search_query = search_col[0].text_input(
        label="Search Query",
        value=st.session_state.search_query,
        placeholder="Search medical devices, papers, or terms...",
        label_visibility="collapsed"
    )
    submitted = search_col[1].form_submit_button("🔍")

# ---- Deep Search Toggle Button ----
col_deep = st.columns([1])
deep_search_label = f"🔎 Deep Search ({'ON' if st.session_state.deep_search else 'OFF'})"
if col_deep[0].button(deep_search_label, key="deep_search_btn", help="Toggle deep search mode"):
    st.session_state.deep_search = not st.session_state.deep_search
    st.rerun()

# ---- Search Action ----
if submitted and st.session_state.search_query.strip():
    # Reset typing state when starting a new search
    st.session_state.typing_complete = False
    st.session_state.typing_position = 0
    st.session_state.typing_active = False
    
    st.session_state.loading = True
    st.session_state.result_shown = False
    loader_area = st.empty()
    message_area = st.empty()

    loader_area.markdown('<div class="loader"></div>', unsafe_allow_html=True)

    steps = [
        "Creating subqueries from your query...",
        "Searching vector DB for each subquery...",
        "Running Graph-RAG and collecting related nodes...",
        "Feeding context into the LLM...",
        "Cross-checking intersections between retrieved articles...",
        "Ranking by match count and semantic relevance...",
        "Evaluating the results...",
    ]

    for step in steps:
        message_area.markdown(f"<p style='text-align:center; font-size:1.05rem;'>{step}</p>", unsafe_allow_html=True)
        time.sleep(1.1)

    loader_area.empty()
    message_area.empty()

    if st.session_state.deep_search:
        result = deep_search(st.session_state.search_query, st.session_state.temperature)
    else:
        result = normal_search(st.session_state.search_query, st.session_state.temperature)
    
    st.session_state.search_result = result
    st.session_state.loading = False
    st.session_state.result_shown = True
    st.rerun()  # Force rerun to display results with clean state

# Add typing animation CSS
st.markdown("""
    <style>
    .typing-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        opacity: 1 !important;
        visibility: visible !important;
    }
    .typing-text {
        font-size: 1rem;
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: break-word;
        opacity: 1 !important;
        visibility: visible !important;
        color: inherit !important;
    }
    .cursor {
        display: inline-block;
        background-color: currentColor;
        width: 2px;
        animation: blink 1s infinite;
        opacity: 1 !important;
    }
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    /* Enhanced typography for results */
    .typing-container h1, .typing-container h2, .typing-container h3 {
        margin: 1rem 0 0.5rem 0;
        font-weight: 600;
        opacity: 1 !important;
        color: inherit !important;
    }
    .typing-container p {
        margin: 0.5rem 0;
        opacity: 1 !important;
        color: inherit !important;
    }
    .typing-container ul, .typing-container ol {
        padding-left: 1.5rem;
        margin: 0.5rem 0;
        opacity: 1 !important;
        color: inherit !important;
    }
    .typing-container li {
        margin: 0.25rem 0;
        opacity: 1 !important;
        color: inherit !important;
    }
    /* Force bright colors and prevent dimming */
    .typing-container * {
        opacity: 1 !important;
        visibility: visible !important;
    }
    /* Prevent any focus/blur dimming effects */
    .stApp, .main, .block-container {
        opacity: 1 !important;
        filter: none !important;
    }
    /* Keep results section always bright */
    [data-testid="stAlert"], [data-testid="stSuccess"] {
        opacity: 1 !important;
        filter: none !important;
    }
    /* Override any Streamlit dimming classes */
    .css-1d391kg, .css-18e3th9, .stMarkdown {
        opacity: 1 !important;
        filter: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Display Result with Typing Animation ----
if st.session_state.result_shown and st.session_state.search_result and not submitted:
    # Force bright styling on the success message
    st.markdown("""
        <style>
        /* Force success message to stay bright */
        .stSuccess {
            opacity: 1 !important;
            filter: none !important;
            background-color: rgba(40, 167, 69, 0.1) !important;
            border: 1px solid #28a745 !important;
        }
        .stSuccess * {
            opacity: 1 !important;
            filter: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.success(f"Results for: **{st.session_state.search_query}**")
    
    # Initialize typing state variables
    if "typing_position" not in st.session_state:
        st.session_state.typing_position = 0
    if "typing_complete" not in st.session_state:
        st.session_state.typing_complete = False
    if "typing_active" not in st.session_state:
        st.session_state.typing_active = False
    
    # Get the result text
    result_text = st.session_state.search_result
    
    # Create container for typing animation
    result_container = st.empty()
    
    # Start typing animation only if not already started
    if not st.session_state.typing_active and not st.session_state.typing_complete:
        st.session_state.typing_active = True
        st.session_state.typing_position = 0
        st.rerun()  # Trigger immediate rerun to start animation
    
    # Animation in progress
    elif st.session_state.typing_active and st.session_state.typing_position < len(result_text):
        # Show text up to current position with cursor
        typed_text = result_text[:st.session_state.typing_position]
        display_text = typed_text + "█"  # Using block cursor
        
        # Apply appropriate styling based on dark mode
        if st.session_state.dark_mode:
            result_container.markdown(
                f'<div class="typing-container" style="background-color: #1e1e1e !important; color: #FAFAFA !important; border: 1px solid #444; padding: 1.5rem; border-radius: 8px; opacity: 1 !important;">'
                f'<div class="typing-text" style="font-family: \'Segoe UI\', sans-serif; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: #FAFAFA !important; opacity: 1 !important;">{display_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            result_container.markdown(
                f'<div class="typing-container" style="background-color: #f8f9fa !important; color: #333333 !important; border: 1px solid #e9ecef; padding: 1.5rem; border-radius: 8px; opacity: 1 !important;">'
                f'<div class="typing-text" style="font-family: \'Segoe UI\', sans-serif; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: #333333 !important; opacity: 1 !important;">{display_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        # Advance typing position - much faster now
        st.session_state.typing_position += 12  # Type 12 characters at a time for faster animation
        
        # Auto-advance the typing with minimal delay
        time.sleep(0.005)  # Even smaller delay for typing effect
        st.rerun()
        
    # Animation complete
    elif st.session_state.typing_position >= len(result_text) and st.session_state.typing_active:
        # Typing complete - show final text without cursor
        st.session_state.typing_complete = True
        st.session_state.typing_active = False
        
        if st.session_state.dark_mode:
            result_container.markdown(
                f'<div class="typing-container" style="background-color: #1e1e1e !important; color: #FAFAFA !important; border: 1px solid #444; padding: 1.5rem; border-radius: 8px; opacity: 1 !important;">'
                f'<div class="typing-text" style="font-family: \'Segoe UI\', sans-serif; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: #FAFAFA !important; opacity: 1 !important;">{result_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            result_container.markdown(
                f'<div class="typing-container" style="background-color: #f8f9fa !important; color: #333333 !important; border: 1px solid #e9ecef; padding: 1.5rem; border-radius: 8px; opacity: 1 !important;">'
                f'<div class="typing-text" style="font-family: \'Segoe UI\', sans-serif; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: #333333 !important; opacity: 1 !important;">{result_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Animation already complete - just display the final result
    elif st.session_state.typing_complete:
        if st.session_state.dark_mode:
            result_container.markdown(
                f'<div class="typing-container" style="background-color: #1e1e1e !important; color: #FAFAFA !important; border: 1px solid #444; padding: 1.5rem; border-radius: 8px; opacity: 1 !important;">'
                f'<div class="typing-text" style="font-family: \'Segoe UI\', sans-serif; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: #FAFAFA !important; opacity: 1 !important;">{result_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            result_container.markdown(
                f'<div class="typing-container" style="background-color: #f8f9fa !important; color: #333333 !important; border: 1px solid #e9ecef; padding: 1.5rem; border-radius: 8px; opacity: 1 !important;">'
                f'<div class="typing-text" style="font-family: \'Segoe UI\', sans-serif; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: #333333 !important; opacity: 1 !important;">{result_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
