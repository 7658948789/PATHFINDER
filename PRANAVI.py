import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import plotly.graph_objects as go
from audio_recorder_streamlit import audio_recorder
import json
import os

# --- 1. THE FOUNDATION: AUTO-DETECT MODEL (FIXES 404 ERROR) ---
API_KEY = "AIzaSyAue_vOZ9h3jztsrG9--sAnK7YTUUehqlM"
genai.configure(api_key=API_KEY)
DB_FILE = "users_db.json"

@st.cache_resource
def load_working_model():
    try:
        available_models = [m.name for m in genai.list_models() 
                            if 'generateContent' in m.supported_generation_methods]
        # Priority order for stable connection
        if 'models/gemini-1.5-flash' in available_models:
            model_name = 'models/gemini-1.5-flash'
        elif 'models/gemini-pro' in available_models:
            model_name = 'models/gemini-pro'
        else:
            model_name = available_models[0]
        return genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return None

model = load_working_model()

# --- 2. THEME & STYLING (Cyber Professional) ---
st.set_page_config(page_title="PathFinder AI", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b1120 0%, #001f3f 100%); color: #e0f2f1; }
    .google-logo { font-size: 45px; font-weight: 900; text-align: center; margin-bottom: 20px; }
    .g-blue { color: #00f2fe; } .g-red { color: #ff4b2b; } .g-yellow { color: #FBBC05; } .g-green { color: #34A853; }
    .stTextInput>div>div>input { border-radius: 24px; padding-left: 20px; background-color: white !important; color: black !important; }
    .sidebar-user { text-align: center; padding: 20px; border-bottom: 1px solid rgba(0, 242, 254, 0.3); }
    .score-box { background: rgba(15, 23, 42, 0.85); border-left: 10px solid #00f2fe; border-radius: 15px; padding: 25px; color: white; }
    label, p, h1, h2, h3, span { color: #e0f2f1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE LOGIC ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

# --- 4. AUTHENTICATION PORTAL ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<div class='google-logo'><span class='g-blue'>P</span>ath<span class='g-red'>F</span>inder <span class='g-blue'>AI</span></div>", unsafe_allow_html=True)
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
    
    with tab_signup:
        n_name = st.text_input("Full Name")
        n_occ = st.text_input("Occupation (e.g. Student)")
        n_email = st.text_input("Email")
        n_pwd = st.text_input("Password", type="password")
        allow_photo = st.checkbox("Enable Profile Photo?")
        photo = st.file_uploader("Upload Image", type=['jpg','png']) if allow_photo else None
        
        if st.button("Create Account"):
            db = load_db()
            db[n_email] = {"name": n_name, "occ": n_occ, "pwd": n_pwd, "has_photo": True if photo else False}
            save_db(db)
            st.success("Account created! Please Login.")

    with tab_login:
        l_email = st.text_input("Email", key="l_email")
        l_pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Access Dashboard"):
            db = load_db()
            user = db.get(l_email)
            if user and user.get("pwd") == l_pwd:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else: st.error("Invalid Credentials.")

# --- 5. DASHBOARD ---
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"<div class='sidebar-user'><h3>👤 {st.session_state.user['name']}</h3><p>{st.session_state.user['occ']}</p></div>", unsafe_allow_html=True)
        st.divider()
        menu = st.radio("NAVIGATION", ["Career Board", "Performance Graphs", "About PathFinder"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if menu == "Career Board":
        st.markdown("<div class='google-logo'><span class='g-blue'>C</span>AREER <span class='g-red'>I</span>NTELLECT</div>", unsafe_allow_html=True)
        
        # Google-Style Search with Mic
        c_mic, c_search = st.columns([1, 9])
        with c_mic:
            audio_data = audio_recorder(text="", icon_size="2x", icon_name="microphone")
        with c_search:
            query = st.text_input("Search career doubts or resume tips...", placeholder="Ask me anything...")
        
        if query or audio_data:
            if model:
                search_term = query if query else "Resume building tips"
                resp = model.generate_content(f"Professional advice for: {search_term}")
                st.info(resp.text)

        st.divider()

        # Resume Intelligence
        st.subheader("📄 Instant Resume Analysis")
        pdf_file = st.file_uploader("Upload Profile (PDF)", type="pdf")
        target_role = st.text_input("Target Job Role")

        if st.button("Execute Deep Analysis") and pdf_file and target_role:
            with st.spinner("PathFinder is decoding your profile..."):
                try:
                    reader = PdfReader(pdf_file)
                    resume_text = "".join([page.extract_text() for page in reader.pages])
                    
                    # Deep Analysis Prompt (Your initial logic)
                    prompt = f"Analyze this resume for {target_role}. Provide Score/100, 'What to Improve', 'Where to Improve', and a Roadmap."
                    response = model.generate_content([prompt, resume_text])
                    
                    st.markdown(f'<div class="score-box">{response.text}</div>', unsafe_allow_html=True)
                    st.session_state.chart_data = {"Tech": 85, "Soft": 75, "Domain": 90, "Tools": 65, "Exp": 80}
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    elif menu == "Performance Graphs":
        st.header("📊 Skill Architecture")
        if "chart_data" in st.session_state:
            data = st.session_state.chart_data
            fig = go.Figure(data=go.Scatterpolar(r=list(data.values()), theta=list(data.keys()), fill='toself'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig)
        else: st.warning("Please analyze a resume first.")

    elif menu == "About PathFinder":
        st.header("ℹ️ About PathFinder AI")
        st.write("PathFinder AI is an intelligent platform powered by Google Gemini, designed for Aditya University students to bridge the gap between education and industry through voice-enabled coaching and deep resume analytics.")