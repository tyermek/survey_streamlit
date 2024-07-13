import time
import streamlit as st
import json
import os

# Set page configuration
st.set_page_config(page_title="Сауалнаманы өңдеу", page_icon="📊")
st.sidebar.header("Сауалнаманы өңдеу")
st.markdown("# Сауалнаманы өңдеу")

# Check if the user is logged in
if not st.session_state.get("password_correct", False):
    st.error("Алдымен жүйеге кіру керек!")
    st.stop()

# File paths
QUESTIONS_FILE = "../questions.json"


# Load questions
def load_questions(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Save questions
def save_questions(questions, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)


# Load existing questions
questions_with_options = load_questions(QUESTIONS_FILE)


# Function to add a new question
def add_question():
    new_question = {
        "question": st.session_state['question_text'],
        "options": st.session_state['answer_options'],
        "type": "RADIO" if st.session_state['question_type'] == "Бір жауабы бар" else "CHECKBOX"
    }
    questions_with_options.append(new_question)
    save_questions(questions_with_options, QUESTIONS_FILE)
    st.success("Сұрақ қосылды!")
    time.sleep(2)
    reset_form()


def reset_form():
    st.session_state.clear()
    st.experimental_rerun()


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


# Function to add an option
def add_option():
    if st.session_state['new_option']:
        st.session_state['answer_options'].append(st.session_state['new_option'])
        st.session_state['new_option'] = ""  # Clear the input after adding


# Function to show all questions
def show_all_questions():
    st.session_state['show_questions'] = True
    st.experimental_rerun()


# Streamlit form for adding questions
if not st.session_state['show_questions']:
    st.subheader("Жаңа сұрақ қосу")
    st.selectbox("Сұрақ түрін таңдаңыз", options=["Бір жауабы бар", "Бір немесе бірнеше дұрыс жауабы бар"],
                 key='question_type')
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

    # Use narrower columns to place buttons closer
    add_question_html = st.button("Сұрақты дерекқорға қосу", key="add_question_html")
    show_questions_html = st.button("Дерекқорды көрсету", key="show_questions_html")

    if add_question_html:
        if not st.session_state['question_text']:
            st.error("Сұрақты енгізіңіз")
        elif len(st.session_state['answer_options']) < 2:
            st.error("Кем дегенде екі жауап нұсқасын енгізіңіз")
        else:
            add_question()

    if show_questions_html:
        show_all_questions()

# Display all questions
else:
    st.subheader("Барлық сұрақтар")
    for q in questions_with_options:
        st.write(f"Сұрақ: {q['question']}")
        for idx, option in enumerate(q['options']):
            st.write(f"{idx + 1}. {option}")
        st.write(f"Түрі: {'Бір жауабы бар' if q['type'] == 'RADIO' else 'Бір немесе бірнеше дұрыс жауабы бар'}")
        st.write("---")

    # Button to go back to the form
    if st.button("Жаңа сұрақ қосу"):
        st.session_state['show_questions'] = False
        st.experimental_rerun()
