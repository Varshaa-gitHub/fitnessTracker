import streamlit as st
import sqlite3
import pickle
import numpy as np

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE,
                      password TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.signup_mode = False
    st.session_state.selected_section = ""

def login():
    st.title("🔑 Login Page")
    username = st.text_input("👤 Username", value="")
    password = st.text_input("🔒 Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Login", use_container_width=True):
            if check_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("🎉 Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    with col2:
        if st.button("🆕 Sign Up", use_container_width=True):
            st.session_state.signup_mode = True
            st.rerun()

def signup():
    st.title("📝 Sign Up")
    new_username = st.text_input("👤 New Username", value="")
    new_password = st.text_input("🔒 New Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Register", use_container_width=True):
            if add_user(new_username, new_password):
                st.success("🎉 Signup successful! Please log in.")
                st.session_state.signup_mode = False
                st.rerun()
            else:
                st.error("❌ Username already exists.")
    
    with col2:
        if st.button("🔙 Back to Login", use_container_width=True):
            st.session_state.signup_mode = False
            st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.selected_section = ""
    st.rerun()

def load_models():
    """Load trained models from .pkl files."""
    try:
        models = [
            pickle.load(open("CHD.pkl", "rb")),
            pickle.load(open("hypoxemia.pkl", "rb")),
            pickle.load(open("bronchi.pkl", "rb")),
            pickle.load(open("asthma.pkl", "rb"))
        ]
        return models
    except Exception as e:
        st.error("Error loading models: " + str(e))
        return None

def physical_review():
    """Handles Physical Review section."""
    st.title("💪 Physical Health Assessment")
    models = load_models()
    if models is None:
        return
    
    # User inputs
    breaths_per_minute = st.number_input("Breaths per Minute", min_value=5, max_value=40, value=16)
    breath_shortness_severity = st.slider("Breath Shortness Severity (0-10)", 0, 10, 5)
    cough_frequency = st.slider("Cough Frequency (0-10)", 0, 10, 5)
    cough_severity = st.slider("Cough Severity (0-10)", 0, 10, 5)
    oxygen_saturation = st.number_input("Oxygen Saturation (%)", min_value=80, max_value=100, value=98)
    heart_rate = st.number_input("Heart Rate (bpm)", min_value=50, max_value=200, value=72)
    blood_pressure_sys = st.number_input("Systolic Blood Pressure (mmHg)", min_value=80, max_value=200, value=120)
    blood_pressure_dia = st.number_input("Diastolic Blood Pressure (mmHg)", min_value=50, max_value=120, value=80)
    cholesterol = st.number_input("Cholesterol (mg/dL)", min_value=100, max_value=300, value=180)
    
    if st.button("🔍 Assess Health", use_container_width=True):
        model_inputs = {
            "bronchi": np.array([[breaths_per_minute, breath_shortness_severity, cough_frequency, cough_severity]]),
            "hypoxemia": np.array([[oxygen_saturation]]),
            "asthma": np.array([[oxygen_saturation, heart_rate, breaths_per_minute]]),
            "CHD": np.array([[blood_pressure_sys, blood_pressure_dia, heart_rate, cholesterol]])
        }
        
        model_names = ["CHD", "hypoxemia", "bronchi", "asthma"]
        predictions = {}
        
        for model, name in zip(models, model_names):
            predictions[name] = model.predict(model_inputs[name])[0]
        
        # Display results
        for condition, result in predictions.items():
            if result == 1:
                st.warning(f"⚠️ {condition.upper()} risk detected! Please consult a doctor.")
                st.title("Coimbatore Therapists Location")

                # Embed Google Maps using iframe in markdown
                st.markdown("""<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3916.4695233855154!2d76.95583017483678!3d11.01684495593948!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ba859a08c8e83cb%3A0xf60dbf8ec9f15a3e!2sFUN%20Republic%20Mall%2C%20Avinashi%20Rd%2C%20Nehru%20St%2C%20Peelamedu%2C%20Coimbatore%2C%20Tamil%20Nadu%20641004!5e0!3m2!1sen!2sin!4v1696561353432!5m2!1sen!2sin"  width="600"  height="450"  style="border:0;"  allowfullscreen=""  loading="lazy"></iframe>""",
                unsafe_allow_html=True)

    

                # Add a link to Justdial
                st.markdown("""<a href="https://www.justdial.com/Coimbatore/Mental-Therapists" target="_blank">View on Justdial to book appointments !</a>""", unsafe_allow_html=True)

                
            else:
                st.success(f"✅ No significant risk of {condition.upper()}. Keep maintaining a healthy lifestyle!")


def dashboard():
    st.title(f"🎉 Welcome, {st.session_state.username}!")
    st.markdown("## Choose an option")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💪 Physical Review", use_container_width=True):
            st.session_state.selected_section = "physical_review"
            st.rerun()
    with col2:
        st.button("🧠 Mental Review", use_container_width=True)
    with col3:
        st.button("🎯 Goal Setting", use_container_width=True)
    
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# Main logic
if st.session_state.logged_in:
    if st.session_state.selected_section == "physical_review":
        physical_review()
    else:
        dashboard()
elif st.session_state.signup_mode:
    signup()
else:
    login()


