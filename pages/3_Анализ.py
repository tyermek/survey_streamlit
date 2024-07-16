import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Деректерді талдау", page_icon="📊")
st.sidebar.header("Деректерді талдау")
st.markdown("# Деректерді талдау")

# Check if the user is logged in
if not st.session_state.get("password_correct", False):
    st.error("Алдымен жүйеге кіру керек!")
    st.stop()

# Function to load the Excel file with caching
@st.cache_data
def load_data():
    return pd.read_excel("https://raw.githubusercontent.com/tyermek/survey_streamlit/main/dataset.xlsx", sheet_name="35950")  # Update the path as needed

# Load the data
df = load_data()

# Remove everything after "/" in the responses
for col in df.columns:
    df[col] = df[col].astype(str).str.split('/ ').str[0].str.strip()

# Define aliases for specific columns
question_aliases = {
    "Өзіңіздің аймағыңызды таңдаңыз:": "Аймақ",
    "Сіз қандай мектепте оқисыз?": "Мектеп",
    "4. Мектептегі оқыту тілін белгілеңіз / Укажите язык обучения в школе:": "Оқыту тілі",
    "Өз статусыңызды көрсетіңіз: ": "Статус"
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
def plot_overall_stats(df):
    st.subheader("Статистика")
    col1, col2 = st.columns(2)
    col1.metric("Жауаптар саны", len(df))
    col2.metric("Сұрақтар саны", len(df.columns) - 2)  # Subtract 2 for Response ID and Submitted at

# Plot responses based on user selection
def plot_responses(df, plot_type):
    if plot_type == "Үйде жұмыс орнының қолжетімділігі":
        st.markdown("### Үйде жұмыс орнының қолжетімділігі")
        fig = px.pie(df,
                     names="Қашықтықтан оқыту кезінде сабақтарды орындау үшін Сіздің үйде жұмыс орны бар ма? ",
                     title="Cабақтарды орындау үшін Сіздің үйде жұмыс орны бар ма?")
        st.plotly_chart(fig)
    elif plot_type == "Компьютерде күніне қанша сағат отырасыз?":
        fig = px.bar(df,
                     x="16.	Компьютерде күніне қанша сағат отырасыз? / Сколько часов в день Вы сидите за компьютером?",
                     title="Компьютерде күніне қанша сағат отырасыз?")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)
    elif plot_type == "Сізге онлайн сабақтарға қатысу ыңғайлы ма?":
        fig = px.bar(df,
                     x="15.	Үй жағдайында Сізге онлайн сабақтарға қатысу ыңғайлы ма? / Удобно ли Вам в домашних условиях участвовать в онлайн уроках? ",
                     title="Сізге онлайн сабақтарға қатысу ыңғайлы ма?")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)
    elif plot_type == "Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма?":
        fig = px.pie(df,
                     names="27.	Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма? / Возникают ли ссоры с членами семьи из-за компьютера или гаджета?",
                     title="Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма?")
        st.plotly_chart(fig)
    elif plot_type == "Мұғалімнің тапсырмаларын қалай жиі орындайсыз?":
        fig = px.pie(df,
                     names="10.	Мұғалімнің тапсырмаларын қалай жиі орындайсыз? / Как часто Вы выполняете задания учителя?",
                     title="Мұғалімнің тапсырмаларын қалай жиі орындайсыз?")
        st.plotly_chart(fig)
    elif plot_type == "Сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба?":
        fig = px.bar(df,
                     x="13.	Сіз қалай ойлайсыз, сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба? / Как вы считате, Вы стали активнее при дистанционном обучении?",
                     title="Сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба?")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)

# Dropdown for selecting the type of plot
plot_type = st.selectbox(
    "Қандай графикті көрсету керек?",
    ["Үйде жұмыс орнының қолжетімділігі", 
     "Компьютерде күніне қанша сағат отырасыз?", 
     "Сізге онлайн сабақтарға қатысу ыңғайлы ма?", 
     "Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма?",
     "Мұғалімнің тапсырмаларын қалай жиі орындайсыз?", 
     "Сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба?"]
)

# Display statistics and visualizations
plot_overall_stats(filtered_df)
if not filtered_df.empty:
    plot_responses(filtered_df, plot_type)
else:
    st.warning("Фильтрлерге сәйкес келетін жауаптар жоқ.")
