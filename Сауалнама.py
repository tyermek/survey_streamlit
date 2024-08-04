import streamlit as st
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import qrcode
import io
import base64
import hmac
import requests
import time
from datetime import datetime

# Set page configuration at the very top
st.set_page_config(page_title="Сауалнама", page_icon="📈")

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Пайдаланушы аты", key="username")
            st.text_input("Құпия сөз", type="password", key="password")
            st.form_submit_button("Жүйеге кіру", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["passwords"] and hmac.compare_digest(
                st.session_state["password"],
                st.secrets.passwords[st.session_state["username"]]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

if not check_password():
    st.stop()

st.sidebar.header("Сауалнаманы құру")

# Function to create URL for Google Form
SCOPES = ["https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/forms.responses.readonly"]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
CREDENTIALS_FILE = "client_secrets.json"
TOKEN_FILE = "token.pickle"

# Streamlit app
st.title("Сауалнама платформасына қош келдіңіз!")

# Check if the form creation has started
if "form_creation_started" not in st.session_state:
    st.session_state.form_creation_started = False

# Only show the question selection UI if the form creation has not started
if not st.session_state.form_creation_started:
    selected_question = st.selectbox("Сұрақты таңдаңыз", options=optional_questions)

    if "show_text_input" not in st.session_state:
        st.session_state.show_text_input = False

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Сұрақты қосу"):
            st.session_state.show_text_input = True
    with col2:
        st.write(
            '<div style="display: flex; align-items: center; height: 38px;">📌 Егер іздеген сұрағыңызды таппасаңыз</div>',
            unsafe_allow_html=True)

    if st.session_state.show_text_input:
        new_question = st.text_input("Жаңа сұрақты енгізіңіз")

        if st.button("Сұрақты сақтаңыз"):
            if new_question:
                optional_questions.append(new_question)
                st.success(f"Сұрақ қосылды: {new_question}")
                selected_question = new_question
                st.session_state.show_text_input = False
                X = vectorizer.fit_transform(optional_questions)
                X_pca = pca.fit_transform(X.toarray())
            else:
                st.error("Сұрақты енгізіңіз")

    col3, col4 = st.columns([1, 3])
    with col3:
        if st.button("Сауалнаманы құру"):
            st.session_state.form_creation_started = True
            with st.spinner("Сауалнама құрылуда..."):
                form_url, form_id = create_google_form(mandatory_questions_with_options, find_similar_questions(selected_question, optional_questions, X_pca))
            st.session_state.form_url = form_url
            st.session_state.form_id = form_id

            commit_survey_link_to_github(form_url, form_id)

            st.experimental_rerun()
    with col4:
        st.write(
            f'<div style="display: flex; align-items: center; height: 38px;">📌 Сіз таңдаған сұрақ: {selected_question}</div>',
            unsafe_allow_html=True)

# Show the form URL and QR code once the form creation is done
if st.session_state.form_creation_started:
    st.write("Сауалнамаға сілтеме:")
    st.write(st.session_state.form_url)

    # Generate and display QR code
    qr_code_img = generate_qr_code(st.session_state.form_url)
    qr_code_base64 = base64.b64encode(qr_code_img).decode('utf-8')
    st.markdown(
        f'<div style="display: flex; justify-content: center;"><img src="data:image/png;base64,{qr_code_base64}" alt="QR Code"></div>',
        unsafe_allow_html=True
    )
