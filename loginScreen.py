import streamlit as st
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
        .e14lo1l1  {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

class LoginScreen:
    def __init__(self):
        load_dotenv()
        self.dbHost = os.getenv('DBHOST')
        self.dbName = os.getenv('DBNAME')
        self.dbUser =  os.getenv('DBUSER')
        self.dbPassword = os.getenv('DBPASSWORD')
        self.dbPort =  os.getenv('DBPORT')
        

    def getDbConnection(self):
        try:
            return psycopg2.connect(
                host= self.dbHost,
                database= self.dbName,
                user= self.dbUser,
                password= self.dbPassword,
                port= self.dbPort
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
                companyId = self.authenticateUser(username,password)
           
                accessLevel = self.get_user_access(username)
                if companyId:
                    st.session_state["loggedIn"] = True
                    st.session_state["companyId"] = companyId
                    st.session_state["pagesAcess"] = accessLevel 
                    st.success("Login bem-sucedido! Redirecionando...")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")
                    
                    
    def get_user_access(self,username):
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
        finally:
            cur.close()
            conn.close()
 
        return dashboard_data

    def execute(self):
        if "loggedIn" not in st.session_state:
            st.session_state["loggedIn"] = False

        if st.session_state["loggedIn"]:
            comapnyAcess = st.session_state["companyId"]
            if comapnyAcess == 2:
                st.switch_page("pages/main.py")
            elif comapnyAcess == 3:
                st.switch_page("pages/main.py")
            elif comapnyAcess == 4:
                st.switch_page("pages/amgdash.py")
        else:
            self.loginScreen()
            

if __name__ == "__main__":
    loginApp = LoginScreen()
    loginApp.execute()
