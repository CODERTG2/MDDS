import streamlit as st
import time

st.set_page_config(page_title="Medical Diagnostic Device Research")

# CSS for animated button adapted with your colors and sizes
st.markdown("""
<style>
.btn-12 {
  position: relative;
  border:none;
  box-shadow: none;
  width: 130px;
  height: 40px;
  line-height: 42px;
  perspective: 230px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  color: white;
  background: linear-gradient(0deg, rgba(14,17,23,1) 0%, rgba(14,17,23,1) 100%);
  border-radius: 5px;
  transition: color 0.3s;
  user-select: none;
}
.btn-12 span {
  display: block;
  position: absolute;
  width: 130px;
  height: 40px;
  box-shadow:
    inset 2px 2px 2px 0px rgba(255,255,255,.5),
    7px 7px 20px 0px rgba(0,0,0,.1),
    4px 4px 5px 0px rgba(0,0,0,.1);
  border-radius: 5px;
  margin: 0;
  text-align: center;
  box-sizing: border-box;
  transition: all .3s;
  left: 0;
  top: 0;
  line-height: 40px;
}
.btn-12 span:nth-child(1) {
  box-shadow:
    -7px -7px 20px 0px #fff9,
    -4px -4px 5px 0px #fff9,
    7px 7px 20px 0px #0002,
    4px 4px 5px 0px #0001;
  transform: rotateX(90deg);
  transform-origin: 50% 50% -20px;
  background: linear-gradient(0deg, rgba(0,172,238,1) 0%, rgba(2,126,251,1) 100%);
}
.btn-12 span:nth-child(2) {
  transform: rotateX(0deg);
  transform-origin: 50% 50% -20px;
  background: linear-gradient(0deg, rgba(14,17,23,1) 0%, rgba(14,17,23,1) 100%);
}
.btn-12:hover span:nth-child(1) {
  box-shadow:
    inset 2px 2px 2px 0px rgba(255,255,255,.5),
    7px 7px 20px 0px rgba(0,0,0,.1),
    4px 4px 5px 0px rgba(0,0,0,.1);
  transform: rotateX(0deg);
}
.btn-12:hover span:nth-child(2) {
  box-shadow:
    inset 2px 2px 2px 0px rgba(255,255,255,.5),
    7px 7px 20px 0px rgba(0,0,0,.1),
    4px 4px 5px 0px rgba(0,0,0,.1);
  color: transparent;
  transform: rotateX(-90deg);
}
</style>
""", unsafe_allow_html=True)

# Session state for search
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "loading" not in st.session_state:
    st.session_state.loading = False

# Main input
search_query = st.text_input(
    label="",
    value=st.session_state.search_query,
    key="search_query",
    placeholder="Search medical devices, papers, or terms...",
    label_visibility="collapsed"
)

# Custom button via HTML that triggers search
# We use a form and button with id and JS to trigger Streamlit callback
st.markdown("""
<form id="searchForm">
  <button type="submit" class="btn-12">
    <span>Search</span><span>Search</span>
  </button>
</form>
<script>
const form = window.parent.document.querySelector('#searchForm');
form.addEventListener('submit', e => {
    e.preventDefault();
    const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
    if(input){
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    // Trigger Streamlit rerun by clicking the hidden button below
    const hiddenBtn = window.parent.document.querySelector('#hiddenSearchBtn');
    if(hiddenBtn){
      hiddenBtn.click();
    }
});
</script>
""", unsafe_allow_html=True)

# Hidden real button to trigger Streamlit rerun when custom button clicked
search_button = st.button("hidden_search_button", key="hiddenSearchBtn", label_visibility="collapsed")

# Logic for starting loading on button press
if search_button and search_query.strip():
    st.session_state.loading = True
    st.session_state.search_query = search_query.strip()

# Loading animation and steps
if st.session_state.loading:
    loader_area = st.empty()
    message_area = st.empty()

    loader_area.markdown('<div style="margin: 20px auto; width:50px; height:50px; border:6px solid #f3f3f3; border-top:6px solid #3498db; border-radius:50%; animation:spin 1s linear infinite;"></div>', unsafe_allow_html=True)

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
        time.sleep(1)

    loader_area.empty()
    message_area.empty()
    st.success(f"Results for: **{st.session_state.search_query}**")
    st.session_state.loading = False

# CSS for loader spin animation
st.markdown("""
<style>
@keyframes spin {
  0% { transform: rotate(0deg);}
  100% { transform: rotate(360deg);}
}
</style>
""", unsafe_allow_html=True)
