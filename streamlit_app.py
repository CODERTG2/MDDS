import streamlit as st
import time

st.set_page_config(
    page_title="Medical Diagnostic Device Research",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---- Custom CSS and JS Injection ----
def inject_css_js():
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
                max-width: 600px;
                margin: auto;
            }
            .search-input {
                width: 100%;
                padding-right: 3rem;
                font-size: 1rem;
                height: 3rem;
                padding-left: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #ccc;
            }
            .search-icon {
                position: absolute;
                right: 1rem;
                top: 50%;
                transform: translateY(-50%);
                font-size: 1.2rem;
                color: #888;
                pointer-events: none;
            }
        </style>
        <script>
            const docReady = (fn) => {
                if (document.readyState !== 'loading') {
                    fn();
                } else {
                    document.addEventListener('DOMContentLoaded', fn);
                }
            };

            docReady(() => {
                const iframe = window.parent.document;
                const input = iframe.querySelector('input[name="search_input_field"]');
                const target = iframe.querySelector('input[data-testid="search-mirror"]');
                if (input && target) {
                    input.addEventListener("input", () => {
                        target.value = input.value;
                        target.dispatchEvent(new Event("input", { bubbles: true }));
                    });
                }
            });
        </script>
    """, unsafe_allow_html=True)

inject_css_js()

# ---- State ----
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

# ---- Sidebar ----
with st.sidebar:
    st.title("🎛 Customize")
    st.session_state.username = st.text_input("Your Name", value=st.session_state.username)

    st.markdown("---")

    st.session_state.temperature = st.slider(
        "🎨 Creativity (LLM Temperature)",
        min_value=0.0, max_value=1.0,
        value=st.session_state.temperature,
        step=0.05
    )

    st.markdown("---")

    st.session_state.dark_mode = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode)

# ---- Dark Mode Styles ----
if st.session_state.dark_mode:
    st.markdown("""
        <style>
            body, .main, .stApp {
                background-color: #0e1117 !important;
                color: #FAFAFA !important;
            }
            .search-input {
                background-color: #262730 !important;
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
                color: black !important;
            }
        </style>
    """, unsafe_allow_html=True)

# ---- Header ----
st.markdown("<div class='title'>Medical Diagnostic Device Research</div>", unsafe_allow_html=True)

if st.session_state.username.strip():
    st.markdown(f"<div class='subtitle'>Hello {st.session_state.username.strip()}, what would you like to search?</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='subtitle'>What would you like to search?</div>", unsafe_allow_html=True)

# ---- Custom Search Box with Icon ----
st.markdown("""
    <div class="search-container">
        <input type="text" class="search-input" name="search_input_field" placeholder="Search medical devices, papers, or terms..." />
        <span class="search-icon">🔍</span>
    </div>
""", unsafe_allow_html=True)

# Hidden streamlit input to mirror the custom input value
search_query = st.text_input("Search Query", key="search-mirror", label_visibility="collapsed")

# ---- Search Trigger ----
search_button = st.button("Search", use_container_width=True)
if search_button and search_query.strip():
    st.session_state.loading = True
    st.session_state.search_query = search_query.strip()

# ---- Loading and Results ----
if st.session_state.loading:
    loader_area = st.empty()
    message_area = st.empty()

    loader_area.markdown('<div class="loader"></div>', unsafe_allow_html=True)

    steps = [
        "🔍 Creating subqueries from your query...",
        "📚 Searching vector DB for each subquery...",
        "🧠 Running Graph-RAG and collecting related nodes...",
        "🧵 Feeding context into the LLM...",
        "🔗 Cross-checking intersections between retrieved articles...",
        "📊 Ranking by match count and semantic relevance..."
    ]

    for step in steps:
        message_area.markdown(
            f"<p style='text-align:center; font-size:1.05rem;'>{step}</p>",
            unsafe_allow_html=True
        )
        time.sleep(1)

    loader_area.empty()
    message_area.empty()
    st.success(f"✅ Results for: **{st.session_state.search_query}**")
    st.session_state.loading = False
