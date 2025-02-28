import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import os

# Configuração do modo escuro
st.set_page_config(page_title="Portal AMG", layout="wide")

pagesAcess = st.session_state.get("pagesAcess", 0)
access = pagesAcess[0]
if "admin" not in access:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {display: none;}
            .e14lo1l1  {display: none !important;}
            div.block-container {padding-top: 15px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {display: block;}
            div.block-container {padding-top: 15px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


class AmgDash:
    def __init__(self):
        load_dotenv()
        self.dbHostAmg = os.getenv("AMG_HOST_POSTGREE")
        self.dbNameAmg = os.getenv("AMG_DATABASE_POSTGREE")
        self.dbUserAmg = os.getenv("AMG_USER_POSTGREE")
        self.dbPasswordAmg = os.getenv("AMG_PASSWORD_POSTGREE")
        self.dbPortAmg = os.getenv("AMG_PORT_POSTGREE")
        self.connAMG = psycopg2.connect(
            host="26.173.234.118",
            database="AMG_SAUDE",
            user="postgres",
            password="1425",
            port="5432",
        )
        
        
        self.dbHost = os.getenv('DBHOST')
        self.dbName = os.getenv('DBNAME')
        self.dbUser =  os.getenv('DBUSER')
        self.dbPassword = os.getenv('DBPASSWORD')
        self.dbPort =  os.getenv('DBPORT')
        self.conn = psycopg2.connect(
            host=self.dbHost,
            database=self.dbName,
            user=self.dbUser,
            password=self.dbPassword,
            port=self.dbPort
        )

    def getErrors(self):
        try:
            query = """
                SELECT "ERROR", COUNT(*)
                    FROM "OCCUPATIONAL_FILE"
                    WHERE "STATUS" IN ('PE','AR','SM')
                    GROUP BY "ERROR";
            """
            df = pd.read_sql_query(query, self.connAMG)
            if df.empty:
                raise ValueError("A consulta não retornou dados.")
            return df
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados ou executar a consulta: {str(e)}")
            return pd.DataFrame()
        
    def display_errors_table(self):
        df = self.getErrors()
        if df.empty:
            st.info("✅ Nenhum erro encontrado.")
        else:
            st.write("### Erros encontrados")
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}))
        
        
    def getAllDataFromDb(self):
        try:
            query = """
                SELECT tag.name, tag_value.string_value, tag_value.int_value, tag_value.registration_date
                FROM tag_value
                JOIN tag ON tag_value.tag_id = tag.id
                WHERE tag.name IN (
                    'AMG_SUCESSO',
                    'AMG_PENDENTES',
                    'AMG_AJUSTADOS',
                    'AMG_EM_PROCESSAMENTO',
                    'AMG_INVALIDOS',
                    'AMG_REICIDENTES'
                )
            """
            df = pd.read_sql_query(query, self.conn)
            if df.empty:
                raise ValueError("A consulta não retornou dados.")
            return df
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados ou executar a consulta: {str(e)}")
            return pd.DataFrame()
        
        
    def showSatusTable(self,df):
        st.subheader("📋 Tabela de Valores")
        if df.empty:
            st.info("✅ Nenhum status encontrado.")
        else:
            st.write("### Tabela de Status")
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}))
        


    def plot_bar_chart(self, df):
        if df.empty:
            st.warning("⚠️ O DataFrame está vazio. Nenhum gráfico será exibido.")
            return

        # Verifica qual coluna contém os valores numéricos
        if "int_value" in df.columns and not df["int_value"].isnull().all():
            value_col = "int_value"
        elif "string_value" in df.columns and df["string_value"].str.isnumeric().all():
            df["string_value"] = df["string_value"].astype(int)
            value_col = "string_value"
        else:
            st.error("❌ Não há valores numéricos disponíveis para o gráfico.")
            return

        # Calcula o total e a porcentagem para cada valor
        total = df[value_col].sum()
        df["percentage"] = df[value_col] / total * 100 if total > 0 else 0
        df["display_text"] = df.apply(lambda row: f"{row[value_col]} ({row['percentage']:.1f}%)", axis=1)

        st.subheader("📊 Gráfico de Valores")
        palette = ['#4CAF50', '#F44336', '#FF9800', '#9E9E9E', '#2196F3', '#4156F7']
        max_value = df[value_col].max() if not df[value_col].empty else 1

        plt.figure(figsize=(3, 2), facecolor='#0E1117')  # Reduzindo tamanho da figura

        ax = sns.barplot(x=df["name"], y=df[value_col], data=df,
                        palette=palette, edgecolor='black', linewidth=0.5)

        # Ajuste proporcional do tamanho das fontes
        ax.set_xlabel("Categorias", fontsize=5, color='white')
        ax.set_ylabel("Valores", fontsize=5, color='white')
        ax.set_title("Distribuição das Tags", fontsize=6, color='white')

        ax.set_xticklabels(df["name"], rotation=45, ha='right', rotation_mode="anchor",
                        color='white', fontsize=4)  # Correção do alinhamento
        ax.tick_params(axis='y', colors='white', labelsize=4)

        # Ajustando os valores no topo das barras
        for i, (name, value, percentage) in enumerate(zip(df["name"], df[value_col], df["percentage"])):
            ax.text(i, value + (max_value * 0.03), f"{value} ({percentage:.1f}%)",
                    ha='center', fontsize=4, fontweight='bold', color='black')

        st.pyplot(plt)




    def execute(self):
        st.subheader("📊 AMG - Portal do Cliente - Priortec")
        df = self.getAllDataFromDb()
        col1, col2 = st.columns([1,1])
        with col1:
            self.showSatusTable(df)
            self.display_errors_table()
        with col2:
            self.plot_bar_chart(df)
        

if __name__ == "__main__":
    loop = AmgDash()
    loop.execute()
