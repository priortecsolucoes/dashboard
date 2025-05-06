import streamlit as st
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv
 
# Configuração visual da página
st.set_page_config(page_title="Portal do Cliente", layout="wide")
 
# Oculta o menu lateral e outros elementos
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
        .e14lo1l1 {display: none !important;}
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        div.block-container {padding-top: 2rem !important; max-width: 800px; margin: 0 auto;}
        div[data-testid="stForm"] {
            background-color: rgba(0, 0, 0, 0.2);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        div.stButton button {
            width: 100%;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)
 
class LoginScreen:
    def __init__(self):
        load_dotenv()
        self.dbHost = os.getenv('DBHOST')
        self.dbName = os.getenv('DBNAME')
        self.dbUser = os.getenv('DBUSER')
        self.dbPassword = os.getenv('DBPASSWORD')
        self.dbPort = os.getenv('DBPORT')
       
    def getDbConnection(self):
        try:
            return psycopg2.connect(
                host='roundhouse.proxy.rlwy.net',
                database='railway',
                user='postgres',
                password="XWhTqAztzzYuAqvUcgWCUJUJmnEJliDK",
                port='28938'
            )
        except Exception as e:
            st.error(f"Erro ao conectar ao banco de dados: {e}")
            return None
 
    def authenticateUser(self, username, password):
        conn = self.getDbConnection()
        if conn is None:
            return None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "company_id", "password" FROM "company_user"
                WHERE "login" = %s
            """, (username,))
            result = cur.fetchone()
            cur.close()
            if result:
                companyId, hashedPassword = result
                if hashedPassword == password:
                    return companyId
            return None
        finally:
            conn.close()
 
    def get_user_access(self, username):
        conn = self.getDbConnection()
        if conn is None:
            return None
       
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT accesslevel FROM company_user
                WHERE login = %s
            """, (username,))
            dashboard_data = cur.fetchall()
        except Exception as e:
            st.error(f"Erro ao buscar acessos: {e}")
            return None
        finally:
            cur.close()
            conn.close()
 
        return dashboard_data
 
    def loginScreen(self):
        # Centraliza o ícone e o título
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://img.icons8.com/color/96/000000/lock--v1.png", width=80)
            st.title("Portal do Cliente")
            st.subheader("Faça login para continuar")
 
        # Formulário de login centralizado
        with st.form("loginForm"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitButton = st.form_submit_button("Entrar")
 
            if submitButton:
                if not username or not password:
                    st.error("Por favor, preencha todos os campos!")
                else:
                    companyId = self.authenticateUser(username, password)
                    if companyId:
                        accessLevel = self.get_user_access(username)
                        st.session_state["loggedIn"] = True
                        st.session_state["companyId"] = companyId
                        st.session_state["pagesAcess"] = accessLevel
                        st.success("Login bem-sucedido! Redirecionando...")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")
               
    def execute(self):
        if "loggedIn" not in st.session_state:
            st.session_state["loggedIn"] = False
 
        if st.session_state["loggedIn"]:
            companyAccess = st.session_state["companyId"]
            if companyAccess == 2:
                st.switch_page("pages/main.py")
            elif companyAccess == 3:
                st.switch_page("pages/main.py")
            elif companyAccess == 4:
                st.switch_page("pages/amgdash.py")
        else:
            self.loginScreen()
 
if __name__ == "__main__":
    loginApp = LoginScreen()
    loginApp.execute()
 
