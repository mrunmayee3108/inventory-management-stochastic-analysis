import streamlit as st
import requests
from streamlit_lottie import st_lottie

st.set_page_config(
    page_title="Mrunmayee Potdar | Portfolio",
    page_icon="✨",
    layout="wide"
)

def load_lottie(url):
    r = requests.get(url)
    if r.status_code!=200:
        return None 
    return r.json()

lottie_hero = load_lottie("https://assets2.lottiefiles.com/packages/lf20_qp1q7mct.json")
lottie_about = load_lottie("https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json")
lottie_skills = load_lottie("https://assets3.lottiefiles.com/packages/lf20_fcfjwiyb.json")
lottie_projects = load_lottie("https://assets6.lottiefiles.com/packages/lf20_ysrn2iwp.json")
lottie_contact = load_lottie("https://assets3.lottiefiles.com/packages/lf20_u25cckyh.json")
lottie_divider = load_lottie("https://assets6.lottiefiles.com/packages/lf20_x62chJ.json")

st.sidebar.title("Navigation🔽")
section = st.sidebar.radio("Go to", ["Home", "About", "Skills", "Projects", "Contact"])

if section == "Home":
    col1, col2 = st.columns([1, 1.6])
    with col1: 
        st_lottie(lottie_hero, height=360)
    with col2:
        st.markdown("## Hi, I'm **Mrunmayee S. Potdar**👋🏻")
        st.markdown(
            """
            🎓 **AI & Data Science Undergraduate**  
            📊 Passionate about **Data Analysis, EDA & Visualization**  
            
            I build **end-to-end analytics projects** using  
            **Python, Pandas, SQL & Streamlit** to derive  
            **actionable insights from real-world datasets**.
            """
        )
    
    st_lottie(lottie_divider, height=150)

elif section == "About":
    col1, col2 = st.columns([1, 2])
    with col1:
        st_lottie(lottie_about, height = 300)
    with col2: 
        st.subheader("About Me")
        st.write(
            """
            I am pursuing **B.E. in Artificial Intelligence & Data Science**
            at **Thadomal Shahani Engineering College**  
            (Mumbai University).

            My interests lie in:
            - Exploratory Data Analysis (EDA)
            - Extracting useful insights from data
            - Data visualization & dashboards
            - Structured and clean analytics workflows
            """
        )

    st_lottie(lottie_divider, height=150)

elif section == "Skills":
    st.subheader("Technical Skills")
    st_lottie(lottie_skills, height=190)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 💻 Programming languages")
        st.write("🐍Python")
        st.write("🍵Java")
        st.write("🗄️SQL")
        st.write("🧑🏻‍💻C")
    with col2:
        st.markdown("### 📈📊 Data Science")
        st.write("👩🏻‍💻Numpy & Pandas")
        st.write("📊Matplotlib, Seaborn and Plotly")
        st.write("🧹Data cleaning and EDA")
        st.write("📐Statistics and Probability")
    with col3:
        st.markdown("### 🔨⛏️Tools")
        st.write("🗄️MySQL")
        st.write("📊Streamlit")
        st.write("📂Jupyter/colab")
        st.write("📈MS Excel")
        st.write("🔗GitHub")
    
    st_lottie(lottie_divider, height=150)

elif section == "Projects":
    st.subheader("Projects")
    st_lottie(lottie_projects, height=220)
    with st.expander("🚨 Mumbai Crime Data Analysis"):
        st.write(
            """
            **Tech:** Python, Pandas, MySQL, Matplotlib, Seaborn  

            - Cleaned and preprocessed crime datasets  
            - Performed EDA to identify crime patterns  
            - Built MySQL database for querying  
            - Created insightful visualizations  
            """
        )
        st.markdown("[🔗GitHub](https://github.com/mrunmayee3108/Mumbai-Crime-data-analysis)")
    
    with st.expander("🏥 Healthcare Data Analysis"):
        st.write(
            """
            **Tech:** Pandas, SQL, Matplotlib, Seaborn, Streamlit  

            - Cleaned healthcare datasets  
            - Analyzed disease trends & hospital stay duration  
            - Age-group based insights  
            - Built Streamlit dashboard for visualization  
            """
        )
    
    st.write("All projects are available on [🔗GitHub](https://github.com/mrunmayee3108)")

    st_lottie(lottie_divider, height = 150)

elif section == "Contact":
    col1, col2 = st.columns([1, 2])
    with col1:
        st_lottie(lottie_contact, height=300)

    with col2:
        st.subheader("📬 Contact Me")
        st.write("📧 **Email:** mrunmayeepotdar3108@gmail.com")
        st.write("💼 **GitHub:** https://github.com/mrunmayee3108")
        st.write("🔗 **LinkedIn:** https://www.linkedin.com/in/mrunmayee-potdar-536346340/")

        st.markdown("✨ *Open to internships*")
    st_lottie(lottie_divider, height = 150)



