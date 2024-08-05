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
st.set_page_config(page_title="Платформа туралы", page_icon="📈")

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

st.sidebar.header("Платформа туралы")

# Streamlit app
st.title("Сауалнама платформасына қош келдіңіз!")
st.write("Сауалнама жасау және талдау платформасына қош келдіңіз. Мұнда сіз оңай теңшелген сауалнамалар жасап, оларды мақсатты аудиторияңызға таратып және нәтижелерді қуатты құралдармен талдай аласыз.")
