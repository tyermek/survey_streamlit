import time
import streamlit as st
import json
import requests
import base64

# Set page configuration
st.set_page_config(page_title="Сауалнаманы өңдеу", page_icon="📊")
st.sidebar.header("Сауалнаманы өңдеу")
st.markdown("# Сауалнаманы өңдеу")

# Check if the user is logged in
if not st.session_state.get("password_correct", False):
    st.error("Алдымен жүйеге кіру керек!")
    st.stop()

# File paths
QUESTIONS_FILE_PATH = "questions.json"
GITHUB_REPO = "tyermek/survey_streamlit"
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{QUESTIONS_FILE_PATH}"

# Load questions from GitHub with authentication
def load_questions(github_api_url, github_token):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(github_api_url, headers=headers)
        response.raise_for_status()
        content = response.json()
        # Decode the base64 content to get the JSON string
        questions_json = json.loads(base64.b64decode(content["content"]).decode("utf-8"))
        return questions_json, content["sha"]
    except requests.RequestException as e:
        st.error(f"Failed to load questions: {e}")
        return [], None

# Save questions to GitHub with authentication
def save_questions(questions, github_api_url, github_token, sha):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "message": "Update questions",
        "content": base64.b64encode(json.dumps(questions, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8'),
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
    questions_with_options.append(new_question)
    save_questions(questions_with_options, GITHUB_API_URL, GITHUB_TOKEN, sha)
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
    questions_with_options, sha = load_questions(GITHUB_API_URL, GITHUB_TOKEN)
    st.session_state['questions_with_options'] = questions_with_options
    st.session_state['sha'] = sha
    st.session_state['show_questions'] = True
    st.experimental_rerun()

# Clear form if needed
if st.session_state['clear_form']:
    clear_form()

# Load existing questions if not already loaded
if 'questions_with_options' not in st.session_state:
    questions_with_options, sha = load_questions(GITHUB_API_URL, GITHUB_TOKEN)
    st.session_state['questions_with_options'] = questions_with_options
    st.session_state['sha'] = sha

questions_with_options = st.session_state['questions_with_options']
sha = st.session_state['sha']

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
