import streamlit as st

# --- Custom CSS for styling the page ---
st.markdown(
    """
    <style>
    /* Set background gradient */
    .stApp {
        background: linear-gradient(135deg, #d6f0f7 0%, #a0d8ef 100%);
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Center the main container */
    .main-container {
        background: white;
        padding: 3rem 4rem;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        width: 100%;
        max-width: 600px;
        text-align: center;
    }

    /* Search input styling */
    .search-box > div > div > input {
        width: 100% !important;
        font-size: 1.25rem !important;
        padding: 0.8rem 1rem !important;
        border-radius: 12px !important;
        border: 2px solid #0078d7 !important;
        transition: border-color 0.3s ease;
    }
    .search-box > div > div > input:focus {
        outline: none !important;
        border-color: #004a9f !important;
        box-shadow: 0 0 8px #0078d7aa !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #0078d7;
        color: white;
        font-weight: 600;
        padding: 0.7rem 2.5rem;
        border-radius: 12px;
        border: none;
        font-size: 1.1rem;
        cursor: pointer;
        margin-top: 1rem;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #005a9e;
    }

    /* Title styling */
    .title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #004a9f;
        margin-bottom: 1rem;
    }

    /* Subtitle styling */
    .subtitle {
        font-size: 1.15rem;
        color: #333333dd;
        margin-bottom: 2rem;
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown('<div class="title">Medical Diagnostic Device Research</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Search the latest research and insights</div>', unsafe_allow_html=True)

    # Search input centered and styled
    search_query = st.text_input("Enter your search term...", key="search", label_visibility="collapsed", placeholder="E.g., point-of-care diagnostics, biosensors")

    # Search button
    if st.button("Search"):
        if search_query.strip() == "":
            st.warning("Please enter a search term to proceed.")
        else:
            # Placeholder for actual search logic
            st.success(f"Searching for: **{search_query}** ...")
            # Here you would trigger the actual search backend/process

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

