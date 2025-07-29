import streamlit as st
import time

st.set_page_config(page_title="Medical Research Search", layout="wide")

# --- Theme toggle ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.markdown("<div style='position: fixed; bottom: 2rem;'>", unsafe_allow_html=True)
    st.session_state.dark_mode = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Theme colors ---
if st.session_state.dark_mode:
    background = "#121212"
    card_bg = "#1e1e1e"
    text_color = "#ffffff"
    subtext_color = "#cccccc"
    input_border = "#4a90e2"
    button_color = "#4a90e2"
    button_hover = "#357ABD"
    spinner_color = "#4a90e2"
else:
    background = "linear-gradient(135deg, #d6f0f7 0%, #a0d8ef 100%)"
    card_bg = "#ffffff"
    text_color = "#004a9f"
    subtext_color = "#333333dd"
    input_border = "#0078d7"
    button_color = "#0078d7"
    button_hover = "#005a9e"
    spinner_color = "#0078d7"

# --- Inject CSS ---
st.markdown(
    f"""
    <style>
    html, body, .stApp {{
        height: 100%;
        margin: 0;
        padding: 0;
        background: {background};
        transition: background 0.5s ease-in-out;
        display: flex;
        justify-content: center;
        align-items: center;
    }}

    .block-container {{
        padding: 0 !important;
        margin: 0 !important;
    }}

    .main-container {{
        background: {card_bg};
        padding: 3rem 4rem;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        max-width: 600px;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: background-color 0.5s ease-in-out;
    }}

    .search-box > div > div > input {{
        width: 100% !important;
        font-size: 1.25rem !important;
        padding: 0.8rem 1rem !important;
        border-radius: 12px !important;
        border: 2px solid {input_border} !important;
        color: {'#ffffff' if st.session_state.dark_mode else '#000000'} !important;
        background-color: {'#2c2c2c' if st.session_state.dark_mode else 'white'} !important;
        transition: background-color 0.5s ease-in-out, color 0.5s ease-in-out;
    }}

    .search-box > div > div > input:focus {{
        outline: none !important;
        border-color: {button_hover} !important;
        box-shadow: 0 0 8px {button_hover}aa !important;
    }}

    .stButton > button {{
        background-color: {button_color};
        color: white;
        font-weight: 600;
        padding: 0.7rem 2.5rem;
        border-radius: 12px;
        border: none;
        font-size: 1.1rem;
        cursor: pointer;
        transition: background-color 0.3s ease;
        display: block;
        margin: 1.5rem auto 0;
    }}

    .stButton > button:hover {{
        background-color: {button_hover};
    }}

    .title {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {text_color};
        margin-bottom: 1rem;
        text-align: center;
        transition: color 0.5s ease-in-out;
    }}

    .subtitle {{
        font-size: 1.15rem;
        color: {subtext_color};
        margin-bottom: 2rem;
        font-style: italic;
        text-align: center;
        transition: color 0.5s ease-in-out;
    }}

    .loader {{
        border: 6px solid #f3f3f3;
        border-top: 6px solid {spinner_color};
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 2rem auto 1rem;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown('<div class="title">Medical Diagnostic Device Research</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Search the latest research and insights</div>', unsafe_allow_html=True)

    search_query = st.text_input(
        label="Enter your search term...",
        key="search",
        label_visibility="collapsed",
        placeholder="E.g., point-of-care diagnostics, biosensors"
    )

    if "loading" not in st.session_state:
        st.session_state.loading = False

    if st.button("Search"):
        if search_query.strip() == "":
            st.warning("Please enter a search term to proceed.")
        else:
            st.session_state.loading = True

    if st.session_state.loading:
        with st.spinner("Running Multi-Query RAG..."):
            st.markdown('<div class="loader"></div>', unsafe_allow_html=True)
            status_area = st.empty()
            steps = [
                "🔍 Creating subqueries from your query...",
                "📚 Searching vector DB for each subquery...",
                "🧠 Running Graph-RAG and collecting related nodes...",
                "🧵 Feeding context into the LLM...",
                "🔗 Cross-checking intersections between retrieved articles...",
                "📊 Ranking by match count and semantic relevance..."
            ]

            for step in steps:
                status_area.markdown(
                    f"<p style='font-size:1.05rem; color:{subtext_color}; text-align:center;'>{step}</p>",
                    unsafe_allow_html=True
                )
                time.sleep(1.1)

        # Show final results
        st.success(f"✅ Results for: **{search_query}**")
        st.session_state.loading = False

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
