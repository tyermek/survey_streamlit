import time
import streamlit as st
import json
import requests

# Set page configuration
st.set_page_config(page_title="Сауалнаманы өңдеу", page_icon="📊")
st.sidebar.header("Сауалнаманы өңдеу")
st.markdown("# Сауалнаманы өңдеу")

# Check if the user is logged in
if not st.session_state.get("password_correct", False):
    st.error("Алдымен жүйеге кіру керек!")
    st.stop()

# File paths
QUESTIONS_FILE_URL = "https://raw.githubusercontent.com/tyermek/survey_streamlit/main/questions.json"
QUESTIONS_FILE_PATH = "questions.json"
GITHUB_REPO = "tyermek/survey_streamlit"
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{QUESTIONS_FILE_PATH}"

# Load questions
def load_questions(file_url):
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to load questions: {e}")
        return []

# Save questions to GitHub
def save_questions(questions, github_api_url, github_token):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    # Get the current file's SHA
    response = requests.get(github_api_url, headers=headers)
    response.raise_for_status()
    sha = response.json()["sha"]

    data = {
        "message": "Update questions",
        "content": json.dumps(questions, ensure_ascii=False, indent=4),  # Pretty-print JSON
        "sha": sha
    }
    response = requests.put(github_api_url, headers=headers, json=data)
    response.raise_for_status()

# Initialize session state for answer options and question text
if 'answer_options' not in st.session_state:
    st.session_state['answer_options'] = []

if 'question_text' not in st.session_state:
    st.session_state['question_text'] = ""

if 'new_option' not in st.session_state:
    st.session_state['new_option'] = ""

if 'question_type' not in st.session_state:
    st.session_state['question_type'] = "Бір жауабы бар"

if 'show_questions' not in st.session_state:
    st.session_state['show_questions'] = False

if 'clear_form' not in st.session_state:
    st.session_state['clear_form'] = False

if 'questions_with_options' not in st.session_state:
    st.session_state['questions_with_options'] = []

# Function to add an option
def add_option():
    if st.session_state['new_option']:
        st.session_state['answer_options'].append(st.session_state['new_option'])
        st.session_state['new_option'] = ""  # Clear the input after adding

# Function to add a new question
def add_question():
    new_question = {
        "question": st.session_state['question_text'],
        "options": st.session_state['answer_options'],
        "type": "RADIO" if st.session_state['question_type'] == "Бір жауабы бар" else "CHECKBOX"
    }
    st.session_state['questions_with_options'].append(new_question)
    save_questions(st.session_state['questions_with_options'], GITHUB_API_URL, GITHUB_TOKEN)
    st.success("Сұрақ қосылды!")
    st.session_state['clear_form'] = True
    time.sleep(2)
    st.experimental_rerun()

def clear_form():
    st.session_state['question_text'] = ""
    st.session_state['answer_options'] = []
    st.session_state['new_option'] = ""
    st.session_state['clear_form'] = False

# Function to show all questions
def show_all_questions():
    st.session_state['questions_with_options'] = load_questions(QUESTIONS_FILE_URL)
    st.session_state['show_questions'] = True
    st.experimental_rerun()

# Clear form if needed
if st.session_state['clear_form']:
    clear_form()

# Streamlit form for adding questions
if not st.session_state['show_questions']:
    st.subheader("Жаңа сұрақ қосу")
    st.selectbox("Сұрақ түрін таңдаңыз", options=["Бір жауабы бар", "Бір немесе бірнеше дұрыс жауабы бар"], key='question_type')
    st.text_input("Сұрақты енгізіңіз", key='question_text')

    # Section to add options one by one
    st.text_input("Жауап нұсқасын енгізіңіз", key='new_option')
    st.button("Жауап нұсқасын қосу", on_click=add_option)

    # Display the current question and added options
    if st.session_state['question_text']:
        st.write("Қосылған сұрақ:")
        st.write(st.session_state['question_text'])

    if st.session_state['answer_options']:
        st.write("Қосылған жауап нұсқалары:")
        for idx, option in enumerate(st.session_state['answer_options']):
            st.write(f"{idx + 1}. {option}")

    # Buttons for adding the question and showing the database
    if st.button("Сұрақты дерекқорға қосу"):
        if not st.session_state['question_text']:
            st.error("Сұрақты енгізіңіз")
        elif len(st.session_state['answer_options']) < 2:
            st.error("Кем дегенде екі жауап нұсқасын енгізіңіз")
        else:
            add_question()

    if st.button("Дерекқорды көрсету"):
        show_all_questions()

# Display all questions
else:
    st.subheader("Барлық сұрақтар")
    for q in st.session_state['questions_with_options']:
        st.write(f"Сұрақ: {q['question']}")
        for idx, option in enumerate(q['options']):
            st.write(f"{idx + 1}. {option}")
        st.write(f"Түрі: {'Бір жауабы бар' if q['type'] == 'RADIO' else 'Бір немесе бірнеше дұрыс жауабы бар'}")
        st.write("---")

    # Button to go back to the form
    if st.button("Жаңа сұрақ қосу"):
        st.session_state['show_questions'] = False
        st.experimental_rerun()
