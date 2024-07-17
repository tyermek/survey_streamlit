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

# Replace 'Нұр-Сұлтан қ.' with 'Астана қ.'
df.replace('Нұр-Сұлтан қ.', 'Астана қ.', inplace=True)

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
def plot_responses(df, plot_types):
    for plot_type in plot_types:
        if plot_type == "Үйде жұмыс орнының қолжетімділігі":
            st.markdown("### Үйде жұмыс орнының қолжетімділігі")
            fig = px.pie(df,
                         names="Қашықтықтан оқыту кезінде сабақтарды орындау үшін Сіздің үйде жұмыс орны бар ма? ",
                         title="Cабақтарды орындау үшін Сіздің үйде жұмыс орны бар ма?")
            st.plotly_chart(fig)
            table_data = df["Қашықтықтан оқыту кезінде сабақтарды орындау үшін Сіздің үйде жұмыс орны бар ма? "].value_counts().reset_index()
            table_data.columns = ["Жауап", "Саны"]
            st.write(table_data)
        elif plot_type == "Компьютерде күніне қанша сағат отырасыз?":
            st.markdown("### Компьютерде күніне қанша сағат отырасыз?")
            fig1 = px.bar(df,
                          x="16.\tКомпьютерде күніне қанша сағат отырасыз? / Сколько часов в день Вы сидите за компьютером?",
                          title="Компьютерде күніне қанша сағат отырасыз?")
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1)
            table_data1 = df["16.\tКомпьютерде күніне қанша сағат отырасыз? / Сколько часов в день Вы сидите за компьютером?"].value_counts().reset_index()
            table_data1.columns = ["Жауап", "Саны"]
            st.write(table_data1)
            
            st.markdown("### Қашықтықтан оқыту кезінде гимнастикалық жаттығуды Сіз күніне неше рет жасайсыз?")
            fig2 = px.bar(df,
                          x="16.\tКомпьютерде күніне қанша сағат отырасыз? / Сколько часов в день Вы сидите за компьютером?",
                          y="Қашықтықтан оқыту кезінде гимнастикалық жаттығуды Сіз күніне неше рет жасайсыз? / Сколько раз в день Вы делаете гимнастические упражнения во время дистанционного обучения?",
                          title="Қашықтықтан оқыту кезінде гимнастикалық жаттығуды Сіз күніне неше рет жасайсыз?")
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2)
            table_data2 = df.groupby(["16.\tКомпьютерде күніне қанша сағат отырасыз? / Сколько часов в день Вы сидите за компьютером?", "Қашықтықтан оқыту кезінде гимнастикалық жаттығуды Сіз күніне неше рет жасайсыз? / Сколько раз в день Вы делаете гимнастические упражнения во время дистанционного обучения?"]).size().reset_index(name='Саны')
            st.write(table_data2)
        elif plot_type == "Сізге онлайн сабақтарға қатысу ыңғайлы ма?":
            fig = px.bar(df,
                         x="15.\tҮй жағдайында Сізге онлайн сабақтарға қатысу ыңғайлы ма? / Удобно ли Вам в домашних условиях участвовать в онлайн уроках? ",
                         title="Сізге онлайн сабақтарға қатысу ыңғайлы ма?")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig)
            table_data = df["15.\tҮй жағдайында Сізге онлайн сабақтарға қатысу ыңғайлы ма? / Удобно ли Вам в домашних условиях участвовать в онлайн уроках? "].value_counts().reset_index()
            table_data.columns = ["Жауап", "Саны"]
            st.write(table_data)
        elif plot_type == "Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма?":
            fig = px.pie(df,
                         names="27.\tКомпьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма? / Возникают ли ссоры с членами семьи из-за компьютера или гаджета?",
                         title="Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма?")
            st.plotly_chart(fig)
            table_data = df["27.\tКомпьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма? / Возникают ли ссоры с членами семьи из-за компьютера или гаджета?"].value_counts().reset_index()
            table_data.columns = ["Жауап", "Саны"]
            st.write(table_data)
        elif plot_type == "Мұғалімнің тапсырмаларын қалай жиі орындайсыз?":
            fig = px.pie(df,
                         names="10.\tМұғалімнің тапсырмаларын қалай жиі орындайсыз? / Как часто Вы выполняете задания учителя?",
                         title="Мұғалімнің тапсырмаларын қалай жиі орындайсыз?")
            st.plotly_chart(fig)
            table_data = df["10.\tМұғалімнің тапсырмаларын қалай жиі орындайсыз? / Как часто Вы выполняете задания учителя?"].value_counts().reset_index()
            table_data.columns = ["Жауап", "Саны"]
            st.write(table_data)
        elif plot_type == "Сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба?":
            fig = px.bar(df,
                         x="13.\tСіз қалай ойлайсыз, сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба? / Как вы считате, Вы стали активнее при дистанционном обучении?",
                         title="Сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба?")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig)
            table_data = df["13.\tСіз қалай ойлайсыз, сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба? / Как вы считате, Вы стали активнее при дистанционном обучении?"].value_counts().reset_index()
            table_data.columns = ["Жауап", "Саны"]
            st.write(table_data)

# Display statistics and visualizations
plot_overall_stats(filtered_df)

# Multiselect for selecting the type of plots
plot_types = st.multiselect(
    "Қандай графиктерді көрсету керек?",
    ["Үйде жұмыс орнының қолжетімділігі", 
     "Компьютерде күніне қанша сағат отырасыз?", 
     "Сізге онлайн сабақтарға қатысу ыңғайлы ма?", 
     "Компьютер немесе гаджет салдарынан отбасы мүшелерімен жанжал туындайды ма?",
     "Мұғалімнің тапсырмаларын қалай жиі орындайсыз?", 
     "Сіз қашықтықтан оқыту кезінде белсенді бола алдыңыз ба?"]
)

if not filtered_df.empty:
    plot_responses(filtered_df, plot_types)
else:
    st.warning("Фильтрлерге сәйкес келетін жауаптар жоқ.")
