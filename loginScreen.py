import streamlit as st
import configparser
import psycopg2
import pandas as pd
from dotenv import load_dotenv

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

class LoginScreen:
    def __init__(self):
        load_dotenv()
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

    def getDbConnection(self):
        try:
            return psycopg2.connect(
                host=self.config['configuracoes']['host'],
                database=self.config['configuracoes']['database'],
                user=self.config['configuracoes']['user'],
                password=self.config['configuracoes']['password'],
                port=self.config['configuracoes']['port']
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

    def loginScreen(self):
        st.title("🔒 Portal do Cliente")
        st.subheader("Faça login para continuar")

        with st.form("loginForm"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitButton = st.form_submit_button("Entrar")

            if submitButton:
                companyId = self.authenticateUser(username, password)
                if companyId:
                    st.session_state["loggedIn"] = True
                    st.session_state["companyId"] = companyId
                    st.success("Login bem-sucedido! Redirecionando...")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")

    def execute(self):
        if "loggedIn" not in st.session_state:
            st.session_state["loggedIn"] = False

        if st.session_state["loggedIn"]:
            st.switch_page("pages/main.py")
        else:
            self.loginScreen()

if __name__ == "__main__":
    loginApp = LoginScreen()
    loginApp.execute()
