import streamlit as st
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import subprocess
import sys

# Initialize session state variables
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "selected_section" not in st.session_state:
        st.session_state.selected_section = "dashboard"
    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False

# Call initialization at the start
init_session_state()

# Database functions
def get_db():
    return sqlite3.connect("fitness_tracker.db")

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        
        # Create goals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                username TEXT PRIMARY KEY,
                steps INTEGER DEFAULT 10000,
                calories_burnt INTEGER DEFAULT 2000,
                calorie_intake INTEGER DEFAULT 2000,
                water_intake INTEGER DEFAULT 2000,
                sleep_time REAL DEFAULT 8.0,
                weight_goal TEXT DEFAULT 'Maintain Weight',
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create progress table
        c.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                username TEXT,
                date TEXT,
                steps INTEGER DEFAULT 0,
                calories_burnt INTEGER DEFAULT 0,
                calorie_intake INTEGER DEFAULT 0,
                water_intake INTEGER DEFAULT 0,
                sleep_time REAL DEFAULT 0,
                PRIMARY KEY (username, date),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create mental health checks table
        c.execute('''
            CREATE TABLE IF NOT EXISTS mental_health_checks (
                username TEXT,
                check_date TEXT,
                mood_rating INTEGER,
                notes TEXT,
                PRIMARY KEY (username, check_date),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database initialization error: {e}")

def launch_mental_health_chatbot():
    """
    Launch the mental health chatbot in a new process
    """
    chatbot_path = r"C:\Users\varsh\Downloads\night\app.py"
    if os.path.exists(chatbot_path):
        try:
            python_executable = sys.executable
            subprocess.Popen([python_executable, chatbot_path])
            return True
        except Exception as e:
            st.error(f"Error launching chatbot: {e}")
            return False
    else:
        st.error("Chatbot file not found at specified path")
        return False

def log_mental_health_check(username):
    """
    Log mental health check activity
    """
    st.subheader("Mental Health Check-in")
    mood_rating = st.slider("How are you feeling today? (1-10)", 1, 10, 5)
    notes = st.text_area("Any notes about your mental state today?")
    
    if st.button("Save Mental Health Check-in"):
        conn = get_db()
        c = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            c.execute("""
                INSERT OR REPLACE INTO mental_health_checks 
                (username, check_date, mood_rating, notes)
                VALUES (?, ?, ?, ?)
            """, (username, today, mood_rating, notes))
            conn.commit()
            st.success("Mental health check-in logged successfully!")
        except Exception as e:
            st.error(f"Error logging mental health check: {e}")
        conn.close()
    
    # Add button to launch chatbot
    if st.button("Open Mental Health Chatbot"):
        if launch_mental_health_chatbot():
            st.success("Chatbot launched in a new window!")
        else:
            st.error("Failed to launch chatbot. Please check the file path.")

def show_mental_health_history(username):
    """
    Display mental health history and trends
    """
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT check_date, mood_rating, notes 
        FROM mental_health_checks 
        WHERE username = ?
        ORDER BY check_date DESC
    """, (username,))
    
    history = c.fetchall()
    conn.close()
    
    if history:
        df = pd.DataFrame(history, columns=['Date', 'Mood Rating', 'Notes'])
        
        # Show mood trend chart
        fig = px.line(df, x='Date', y='Mood Rating', 
                     title='Mood Rating Trend',
                     markers=True)
        st.plotly_chart(fig)
        
        # Show detailed history
        st.subheader("Mental Health Check-in History")
        st.dataframe(df)
    else:
        st.info("No mental health check-in history available.")

def user_exists(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_user(username, password):
    if not username or not password:
        return False, "Please enter both username and password"
    
    if user_exists(username):
        return False, "Username already exists"
    
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Add user
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, password))
        
        # Initialize goals
        c.execute("""
            INSERT INTO goals (username) VALUES (?)
        """, (username,))
        
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except Exception as e:
        return False, f"Error creating account: {e}"

def verify_user(username, password):
    if not username or not password:
        return False, "Please enter both username and password"
    
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        
        if result is None:
            return False, "Username not found"
        
        stored_password = result[0]
        if password == stored_password:
            return True, "Login successful!"
        else:
            return False, "Incorrect password"
    except Exception as e:
        return False, f"Login error: {e}"

def get_user_goals(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM goals WHERE username = ?", (username,))
    goals = c.fetchone()
    conn.close()
    
    if goals:
        return {
            'steps': goals[1],
            'calories_burnt': goals[2],
            'calorie_intake': goals[3],
            'water_intake': goals[4],
            'sleep_time': goals[5],
            'weight_goal': goals[6]
        }
    return None

def update_goals(username, goals_dict):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE goals 
        SET steps = ?, calories_burnt = ?, calorie_intake = ?, 
            water_intake = ?, sleep_time = ?, weight_goal = ?
        WHERE username = ?
    """, (
        goals_dict['steps'], goals_dict['calories_burnt'],
        goals_dict['calorie_intake'], goals_dict['water_intake'],
        goals_dict['sleep_time'], goals_dict['weight_goal'], username
    ))
    conn.commit()
    conn.close()

def log_daily_progress(username, progress_dict):
    conn = get_db()
    c = conn.cursor()
    
    # Check if entry exists for today
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("""
        INSERT OR REPLACE INTO progress 
        (username, date, steps, calories_burnt, calorie_intake, water_intake, sleep_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        username, today,
        progress_dict['steps'], progress_dict['calories_burnt'],
        progress_dict['calorie_intake'], progress_dict['water_intake'],
        progress_dict['sleep_time']
    ))
    conn.commit()
    conn.close()

def get_progress_history(username, days=7):
    conn = get_db()
    c = conn.cursor()
    
    # Get data for last n days
    date_limit = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
    c.execute("""
        SELECT date, steps, calories_burnt, calorie_intake, water_intake, sleep_time 
        FROM progress 
        WHERE username = ? AND date >= ?
        ORDER BY date ASC
    """, (username, date_limit))
    
    history = c.fetchall()
    conn.close()
    
    return pd.DataFrame(history, columns=['date', 'steps', 'calories_burnt', 
                                        'calorie_intake', 'water_intake', 'sleep_time'])

def login_page():
    st.title("🏃‍♂️ Fitness & Mental Health Tracker")
    
    if st.session_state.show_signup:
        show_signup_page()
    else:
        show_login_page()

def show_login_page():
    st.subheader("👤 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Login"):
                success, message = verify_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.form_submit_button("Switch to Sign Up"):
                st.session_state.show_signup = True
                st.rerun()

def show_signup_page():
    st.subheader("📝 Sign Up")
    
    with st.form("signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Create Account"):
                success, message = add_user(username, password)
                if success:
                    st.success(message)
                    st.session_state.show_signup = False
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.form_submit_button("Switch to Login"):
                st.session_state.show_signup = False
                st.rerun()

def show_dashboard():
    st.title(f"Welcome {st.session_state.username}! 🏃‍♂️")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    section = st.sidebar.radio("Go to", 
                             ["Dashboard", "Log Progress", "Set Goals", 
                              "Mental Health", "History"])
    
    if section == "Dashboard":
        show_dashboard_metrics()
    elif section == "Log Progress":
        show_progress_logging()
    elif section == "Set Goals":
        show_goals_section()
    elif section == "Mental Health":
        st.title("Mental Health Tracking 🧠")
        tab1, tab2 = st.tabs(["Check-in", "History"])
        with tab1:
            log_mental_health_check(st.session_state.username)
        with tab2:
            show_mental_health_history(st.session_state.username)
    else:
        show_history_section()
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.show_signup = False
        st.rerun()

def show_dashboard_metrics():
    st.subheader("Today's Progress 📊")
    
    # Get goals and today's progress
    goals = get_user_goals(st.session_state.username)
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT steps, calories_burnt, calorie_intake, water_intake, sleep_time 
        FROM progress 
        WHERE username = ? AND date = ?
    """, (st.session_state.username, today))
    progress = c.fetchone()
    
    # Get today's mood rating
    c.execute("""
        SELECT mood_rating 
        FROM mental_health_checks 
        WHERE username = ? AND check_date = ?
    """, (st.session_state.username, today))
    mood = c.fetchone()
    conn.close()
    
    if not progress:
        progress = [0, 0, 0, 0, 0]
    
    # Create metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Steps", f"{progress[0]:,}", 
                 f"Goal: {goals['steps']:,}")
        st.metric("Sleep (hours)", progress[4], 
                 f"Goal: {goals['sleep_time']}")
    
    with col2:
        st.metric("Calories Burnt", f"{progress[1]:,}", 
                 f"Goal: {goals['calories_burnt']:,}")
        st.metric("Water (ml)", f"{progress[3]:,}", 
                 f"Goal: {goals['water_intake']:,}")
    
    with col3:
        st.metric("Calories Intake", f"{progress[2]:,}", 
                 f"Goal: {goals['calorie_intake']:,}")
        st.metric("Today's Mood", f"{mood[0]}/10" if mood else "Not logged")
    
    # Show weekly progress charts
    st.subheader("Weekly Progress 📈")
    df = get_progress_history(st.session_state.username)
    
    if not df.empty:
        # Steps progress
        fig = px.line(df, x='date', y='steps', 
                     title='Steps Progress',
                     markers=True)
        fig.add_hline(y=goals['steps'], line_dash="dash", 
                     annotation_text="Goal")
        st.plotly_chart(fig)
        
        # Calories chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['date'], y=df['calories_burnt'],
                               name="Calories Burnt",mode='lines+markers'))
        fig.add_trace(go.Scatter(x=df['date'], y=df['calorie_intake'],
                               name="Calories Intake", mode='lines+markers'))
        fig.update_layout(title='Calories Progress')
        st.plotly_chart(fig)

def show_progress_logging():
    st.subheader("Log Today's Progress 📝")
    
    goals = get_user_goals(st.session_state.username)
    
    with st.form("progress_form"):
        steps = st.number_input("Steps", min_value=0, max_value=100000, 
                              help=f"Daily goal: {goals['steps']}")
        calories_burnt = st.number_input("Calories Burnt", min_value=0,
                                       help=f"Daily goal: {goals['calories_burnt']}")
        calorie_intake = st.number_input("Calorie Intake", min_value=0,
                                       help=f"Daily goal: {goals['calorie_intake']}")
        water_intake = st.number_input("Water Intake (ml)", min_value=0,
                                     help=f"Daily goal: {goals['water_intake']}")
        sleep_time = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0,
                                   help=f"Daily goal: {goals['sleep_time']}")
        
        if st.form_submit_button("Save Progress"):
            progress_dict = {
                'steps': steps,
                'calories_burnt': calories_burnt,
                'calorie_intake': calorie_intake,
                'water_intake': water_intake,
                'sleep_time': sleep_time
            }
            log_daily_progress(st.session_state.username, progress_dict)
            st.success("Progress logged successfully!")

def show_goals_section():
    st.subheader("Set Your Goals 🎯")
    
    current_goals = get_user_goals(st.session_state.username)
    
    with st.form("goals_form"):
        steps = st.number_input("Daily Steps Goal", min_value=1000, max_value=100000,
                              value=current_goals['steps'])
        calories_burnt = st.number_input("Daily Calories Burnt Goal", min_value=500,
                                       value=current_goals['calories_burnt'])
        calorie_intake = st.number_input("Daily Calorie Intake Goal", min_value=500,
                                       value=current_goals['calorie_intake'])
        water_intake = st.number_input("Daily Water Intake Goal (ml)", min_value=500,
                                     value=current_goals['water_intake'])
        sleep_time = st.number_input("Daily Sleep Goal (hours)", min_value=4.0,
                                   max_value=12.0, value=current_goals['sleep_time'])
        weight_goal = st.selectbox("Weight Goal",
                                 ["Maintain Weight", "Lose Weight", "Gain Weight"],
                                 index=["Maintain Weight", "Lose Weight", 
                                       "Gain Weight"].index(current_goals['weight_goal']))
        
        if st.form_submit_button("Update Goals"):
            goals_dict = {
                'steps': steps,
                'calories_burnt': calories_burnt,
                'calorie_intake': calorie_intake,
                'water_intake': water_intake,
                'sleep_time': sleep_time,
                'weight_goal': weight_goal
            }
            update_goals(st.session_state.username, goals_dict)
            st.success("Goals updated successfully!")

def show_history_section():
    st.subheader("Progress History 📅")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Time Period", [7, 14, 30, 90], index=0)
    
    # Get fitness progress
    df_fitness = get_progress_history(st.session_state.username, days)
    
    # Get mental health progress
    conn = get_db()
    c = conn.cursor()
    date_limit = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
    c.execute("""
        SELECT check_date, mood_rating, notes 
        FROM mental_health_checks 
        WHERE username = ? AND check_date >= ?
        ORDER BY check_date ASC
    """, (st.session_state.username, date_limit))
    mental_health_data = c.fetchall()
    conn.close()
    
    tab1, tab2 = st.tabs(["Fitness Progress", "Mental Health Progress"])
    
    with tab1:
        if not df_fitness.empty:
            # Show detailed stats
            st.subheader("Fitness Statistics")
            metrics_df = df_fitness.describe()
            st.dataframe(metrics_df)
            
            # Download option
            csv = df_fitness.to_csv(index=False)
            st.download_button(
                label="Download Fitness Progress",
                data=csv,
                file_name="fitness_progress.csv",
                mime="text/csv"
            )
        else:
            st.info("No fitness progress data available for the selected period.")
    
    with tab2:
        if mental_health_data:
            df_mental = pd.DataFrame(mental_health_data, 
                                   columns=['Date', 'Mood Rating', 'Notes'])
            
            # Show mood trend
            fig = px.line(df_mental, x='Date', y='Mood Rating',
                         title='Mood Rating History',
                         markers=True)
            st.plotly_chart(fig)
            
            # Show detailed history
            st.dataframe(df_mental)
            
            # Download option
            csv = df_mental.to_csv(index=False)
            st.download_button(
                label="Download Mental Health Progress",
                data=csv,
                file_name="mental_health_progress.csv",
                mime="text/csv"
            )
        else:
            st.info("No mental health data available for the selected period.")

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        
        # Create goals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                username TEXT PRIMARY KEY,
                steps INTEGER DEFAULT 10000,
                calories_burnt INTEGER DEFAULT 2000,
                calorie_intake INTEGER DEFAULT 2000,
                water_intake INTEGER DEFAULT 2000,
                sleep_time REAL DEFAULT 8.0,
                weight_goal TEXT DEFAULT 'Maintain Weight',
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create progress table
        c.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                username TEXT,
                date TEXT,
                steps INTEGER DEFAULT 0,
                calories_burnt INTEGER DEFAULT 0,
                calorie_intake INTEGER DEFAULT 0,
                water_intake INTEGER DEFAULT 0,
                sleep_time REAL DEFAULT 0,
                PRIMARY KEY (username, date),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create mental health checks table
        c.execute('''
            CREATE TABLE IF NOT EXISTS mental_health_checks (
                username TEXT,
                check_date TEXT,
                mood_rating INTEGER,
                notes TEXT,
                PRIMARY KEY (username, check_date),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Verify tables were created
        verify_tables()
        
    except Exception as e:
        st.error(f"Database initialization error: {e}")

def verify_tables():
    """Verify all required tables exist and create them if they don't"""
    conn = get_db()
    c = conn.cursor()
    
    # Get list of existing tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [table[0] for table in c.fetchall()]
    
    # Required tables
    required_tables = ['users', 'goals', 'progress', 'mental_health_checks']
    
    # Create any missing tables
    if 'mental_health_checks' not in existing_tables:
        c.execute('''
            CREATE TABLE IF NOT EXISTS mental_health_checks (
                username TEXT,
                check_date TEXT,
                mood_rating INTEGER,
                notes TEXT,
                PRIMARY KEY (username, check_date),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        conn.commit()
    
    conn.close()

def main():
    # Force recreation of mental health table if needed
    if os.path.exists("fitness_tracker.db"):
        verify_tables()
    else:
        init_db()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        show_dashboard()