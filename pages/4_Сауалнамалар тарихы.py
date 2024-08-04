import streamlit as st
import json
import base64
import requests
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Survey History", page_icon="📜")

# Function to load survey links from GitHub
def load_survey_links():
    GITHUB_REPO = "tyermek/survey_streamlit"
    GITHUB_FILE_PATH = "survey_links.json"
    GITHUB_TOKEN = st.secrets["github"]["token"]
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_API_URL, headers=headers)
    
    if response.status_code != 200:
        st.error("Failed to fetch survey links from GitHub.")
        return []
    
    content = response.json()

    # If the content exists, load it, otherwise return an empty list
    try:
        if content.get("content"):
            survey_links = json.loads(base64.b64decode(content["content"]).decode("utf-8"))
        else:
            survey_links = []
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON from GitHub: {e}")
        survey_links = []

    return survey_links

# Load survey links
survey_links = load_survey_links()

# Display survey links
st.title("Сауалнамалар тарихы")

if survey_links:
    st.subheader("Сауалнама сілтемелері:")

    # Create a DataFrame for the survey links
    df = pd.DataFrame(survey_links)
    df.index += 1  # Start index from 1 for numeration
    df.reset_index(inplace=True)
    df.columns = ["№", "link_survey", "Сауалнама құрылған дата"]
    
    # Make links clickable
    df["Сілтеме"] = df["link_survey"].apply(lambda x: f"[Сілтеме]({x})")
    df.drop(columns=["link_survey"], inplace=True)

    # Display the DataFrame as a table
    st.markdown(df.to_markdown(index=False))
else:
    st.write("No survey links found.")
