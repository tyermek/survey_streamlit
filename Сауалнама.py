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
        username = st.session_state["username"]
        password = st.session_state["password"].encode('utf-8')  # Encode to bytes
        stored_password = st.secrets.passwords[username].encode('utf-8')  # Encode to bytes
        
        if username in st.secrets["passwords"] and hmac.compare_digest(password, stored_password):
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
SCOPES = ["https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/forms.responses.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
CREDENTIALS_FILE = "client_secrets.json"
TOKEN_FILE = "token.pickle"


def find_similar_questions(selected_question, questions, X_pca, top_n=5):
    selected_index = questions.index(selected_question)
    distances = cosine_similarity([X_pca[selected_index]], X_pca)[0]
    similar_indices = distances.argsort()[-top_n - 1:-1][::-1]
    return [questions[i] for i in similar_indices]


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                os.remove(TOKEN_FILE)  # Delete the token file and re-authenticate
                creds = None
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def create_question(title, options, index, question_type="RADIO"):
    return {
        "createItem": {
            "item": {
                "title": title,
                "questionItem": {
                    "question": {
                        "required": True,
                        "choiceQuestion": {
                            "type": question_type,
                            "options": [{"value": option} for option in options],
                            "shuffle": True,
                        },
                    }
                },
            },
            "location": {"index": index},
        }
    }


def create_google_form(mandatory_questions, similar_questions):
    creds = get_credentials()
    service = build('forms', 'v1', credentials=creds, discoveryServiceUrl=DISCOVERY_DOC)

    new_form = {
        "info": {
            "title": "Сауалнама",
        }
    }

    result = service.forms().create(body=new_form).execute()

    questions_requests = {
        "requests": []
    }

    # Add mandatory questions first
    for index, q in enumerate(mandatory_questions):
        questions_requests["requests"].append(
            create_question(q["question"], q["options"], index, q["type"])
        )

    # Add similar questions selected by the user
    start_index = len(mandatory_questions)
    for index, question in enumerate(similar_questions):
        for q in optional_questions_with_options:
            if q["question"] == question:
                questions_requests["requests"].append(
                    create_question(q["question"], q["options"], start_index + index, q["type"])
                )
                break

    service.forms().batchUpdate(formId=result["formId"], body=questions_requests).execute()
    form_url = service.forms().get(formId=result["formId"]).execute()["responderUri"]
    return form_url, result["formId"]


def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert PIL image to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return byte_im


def list_google_forms():
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    results = service.files().list(q="mimeType='application/vnd.google-apps.form'", fields="files(id, name, webViewLink)").execute()
    forms = results.get('files', [])

    form_links = []
    for form in forms:
        form_links.append({'name': form['name'], 'link': form['webViewLink']})

    return form_links


# Initialize session state attributes if not already present
if "form_creation_started" not in st.session_state:
    st.session_state.form_creation_started = False
if "form_url" not in st.session_state:
    st.session_state.form_url = None
if "form_id" not in st.session_state:
    st.session_state.form_id = None

# Load mandatory questions from external file
with open("questions_mandatory.json", "r", encoding="utf-8") as f:
    mandatory_questions_with_options = json.load(f)

# Load optional questions from external file
with open("questions.json", "r", encoding="utf-8") as f):
    optional_questions_with_options = json.load(f)

# Extract optional questions for processing
optional_questions = [q["question"] for q in optional_questions_with_options]

# Convert optional questions to TF-IDF matrix
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(optional_questions)

# Apply PCA for dimensionality reduction
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X.toarray())

# Streamlit app
st.title("Сұрақтарды таңдау немесе қосу")

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

    # Display the list of all Google Forms
    st.write("Барлық Google формалары:")
    forms = list_google_forms()
    for form in forms:
        st.write(f"[{form['name']}]({form['link']})")
