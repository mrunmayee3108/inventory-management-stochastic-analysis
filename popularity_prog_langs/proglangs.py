import streamlit as st
import pandas as pd
import requests
st.title("Programming languages popularity")
st.set_page_config(page_title="Popularity dashboard")
df = pd.read_csv("popularity.csv")
if not df.empty:
    st.subheader("Data preview")
    st.dataframe(df)
    st.toast("Data loaded successfully")
    st.subheader("Summary Statistics: ")
    st.write(df.describe())
    st.write("Choose any programming language(s): ")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    selected_langs = []
    for lang in df.columns[1:]:     
        if st.checkbox(lang):
            selected_langs.append(lang)

    if selected_langs:
        st.subheader("Selected Data")
        st.line_chart(df[selected_langs])
        st.write("x-axis: Year,  y-axis: Popularity score")


st.header("⭐ Live GitHub Popularity (Stars per Language)")

# Only the 6 most popular/important languages
repos = {
    "Python": "python/cpython",
    "JavaScript": "nodejs/node",
    "Java": "openjdk/jdk",
    "C++": "cplusplus/draft",
    "C#": "dotnet/runtime",
    "TypeScript": "microsoft/TypeScript"
}

cols = st.columns(3)
i = 0
for lang, repo in repos.items():
    url = f"https://api.github.com/repos/{repo}"
    r = requests.get(url).json()
    stars = r.get("stargazers_count", "N/A")

    with cols[i % 3]:
        st.metric(lang, stars)

    i += 1
