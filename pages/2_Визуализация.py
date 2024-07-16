import streamlit as st
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Визуализация", page_icon="📊")
st.sidebar.header("Визуализация мен графиктер")
st.markdown("# Визуализация")

# Function to create URL for Google Form
SCOPES = ["https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/forms.responses.readonly"]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
# Get the current directory of the script
current_directory = os.path.dirname(__file__)

# Construct the path to the parent directory
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))

# Construct the full paths to the necessary files in the parent directory
CREDENTIALS_FILE = os.path.join(parent_directory, "client_secrets.json")
TOKEN_FILE = "../token.pickle"


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_console()  # Use run_console instead of run_local_server

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_form_details(form_id, service):
    response = service.forms().get(formId=form_id).execute()
    items = response.get('items', [])
    questions = {item['questionItem']['question']['questionId']: item['title'] for item in items if
                 'questionItem' in item}
    return questions


def get_form_responses(form_id, service):
    response = service.forms().responses().list(formId=form_id).execute()
    return response.get('responses', [])


def display_responses_as_dataframe(responses, questions_map):
    data = []
    for response in responses:
        response_data = {"Response ID": response['responseId'], "Submitted at": response['lastSubmittedTime']}
        answers = response.get('answers', {})
        for question_id, answer in answers.items():
            question = questions_map.get(question_id, "Unknown question")
            answer_text = ", ".join(a['value'] for a in answer['textAnswers']['answers'])
            response_data[question] = answer_text
        data.append(response_data)
    return pd.DataFrame(data)


def plot_overall_stats(df, total_questions):
    st.subheader("Статистика")
    col1, col2 = st.columns(2)
    # Count of responses
    col1.metric("Жауаптар саны", len(df))
    # Count of total questions
    col2.metric("Сұрақтар саны", total_questions)


def plot_responses(df):
    st.subheader("Визуализация")

    for question in df.columns[2:]:
        with st.expander(f"Көрсету/Жасыру - {question}"):
            st.markdown(f"### {question}")

            # Bar chart with Plotly
            fig = px.bar(df, x=question)
            fig.update_layout(title="")
            st.plotly_chart(fig)

            # Pie chart
            pie_fig = px.pie(df, names=question)
            pie_fig.update_layout(title="")
            st.plotly_chart(pie_fig)


# Try-except block to handle session state attribute error
try:
    if st.session_state.form_creation_started:
        if st.button("Сауалнама жауаптарын алу"):
            creds = get_credentials()
            service = build('forms', 'v1', credentials=creds, discoveryServiceUrl=DISCOVERY_DOC)
            with st.spinner("Сауалнама жауаптары талдануда..."):
                questions_map = get_form_details(st.session_state.form_id, service)
                responses = get_form_responses(st.session_state.form_id, service)
                df = display_responses_as_dataframe(responses, questions_map)
                st.session_state.responses_df = df
                st.session_state.questions_map = questions_map  # Save questions_map to session state

        if 'responses_df' in st.session_state and 'questions_map' in st.session_state:
            df = st.session_state.responses_df
            questions_map = st.session_state.questions_map

            # Define aliases for the specified questions
            question_aliases = {
                "Өзіңіздің аймағыңызды таңдаңыз": "Аймақ",
                "Сіз қандай мектепте оқисыз?": "Мектеп",
                "Мектептегі оқыту тілін белгілеңіз": "Оқыту тілі",
                "Өз статусыңызды көрсетіңіз": "Статус"
            }

            # Display filter options for the specified questions using their aliases
            filters = {}
            for question, alias in question_aliases.items():
                if question in df.columns:
                    unique_values = df[question].unique().tolist()
                    filters[question] = st.sidebar.multiselect(f"Сүзгі: {alias}", options=unique_values)

            # Apply filters
            filtered_df = df.copy()
            for question, selected_values in filters.items():
                if selected_values:
                    filtered_df = filtered_df[filtered_df[question].isin(selected_values)]

            # Plot overall statistics
            plot_overall_stats(filtered_df, len(questions_map))
            if not filtered_df.empty:
                # Plot responses
                plot_responses(filtered_df)
            else:
                st.warning("Фильтрлерге сәйкес келетін жауаптар жоқ.")
    else:
        st.write("Алдымен сауалнаманы құру керек!")
except AttributeError as e:
    if "form_creation_started" in str(e):
        st.error("Алдымен жүйеге кіру керек!")
        st.stop()
    else:
        st.write(f"Қате: {e}")
except KeyError as e:
    st.error(f"Қате: '{e}' сұрағы жоқ. Дұрыс сұрақтарды тексеріңіз.")
