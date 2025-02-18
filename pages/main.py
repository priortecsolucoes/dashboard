import streamlit as st
import pandas as pd
import psycopg2

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta
from pytz import timezone
import configparser
import os
from dotenv import load_dotenv


st.set_page_config(page_title="Portal IMND", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #0E1117;
            color: white;
        }
        .stApp {
            background-color: #0E1117;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)


class main:
    def __init__(self):
        load_dotenv()
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
    
    def getAllDataFromDb(self):
        try:
            query = """
                SELECT tag.name, tag_value.string_value, tag_value.int_value, tag_value.registration_date
                FROM tag_value
                JOIN tag ON tag_value.tag_id = tag.id
                WHERE tag.name IN (
                    'IMND_MES_ATUAL_REALIZADOS_APROVADOS',
                    'IMND_MES_ATUAL_REALIZADOS_NAO_APROVADOS',
                    'IMND_MES_ATUAL_PENDENTES',
                    'IMND_MES_ATUAL_INELEGIVEIS',
                    'IMND_MES_ATUAL_NEGADOS',
                    'IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_MES_ATUAL_FATURAVEIS_AUTORIZADAS',
                    'IMND_MES_ATUAL_FATURAVEIS_NAO_AUTORIZADAS',
                    'IMND_AUTORIZACAO_PENDENTES_ATRASADOS_MES_ATUAL',
                    'IMND_DATA_DA_ULTIMA_EXECUCAO'
                )
            """
            df = pd.read_sql_query(query, self.conn)
            if df.empty:
                raise ValueError("A consulta não retornou dados.")
            return df
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados ou executar a consulta: {str(e)}")
            return pd.DataFrame()
    
    def showStatusTable(self, df):
         data = {
             "COMPUTADOR": ["IMND_ROBO3", "IMND_ROBO5", "IMND_ROBO6", "IMND_ROBO7", "IMND_ROBO8"],
             "ÚLTIMA AUTORIZAÇÃO": [
                 df.loc[df["name"] == "IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                 df.loc[df["name"] == "IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                 df.loc[df["name"] == "IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                 df.loc[df["name"] == "IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                 df.loc[df["name"] == "IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
             ],
         }
         statusDf = pd.DataFrame(data)
         currentTime = datetime.now(timezone('America/Sao_Paulo')).replace(tzinfo=None)
         statusDf['datetime_value'] = pd.to_datetime(statusDf['ÚLTIMA AUTORIZAÇÃO'], format='%d/%m/%Y %H:%M:%S')
         statusDf['STATUS'] = statusDf['datetime_value'].apply(
             lambda x: '🟢 ATIVO' if currentTime - x <= timedelta(hours=1) else '🔴 INATIVO'
         )
         statusDf = statusDf[['COMPUTADOR', 'STATUS', 'ÚLTIMA AUTORIZAÇÃO']]
         st.dataframe(statusDf, use_container_width=True)
    
    def showApprovalChart(self, df):
         labels = {
             'IMND_MES_ATUAL_REALIZADOS_APROVADOS': 'Realizados Aprovados',
             'IMND_MES_ATUAL_REALIZADOS_NAO_APROVADOS': 'Realizados Não Aprovados',
             'IMND_MES_ATUAL_PENDENTES': 'Pendentes',
             'IMND_MES_ATUAL_INELEGIVEIS': 'Inelegíveis',
             'IMND_MES_ATUAL_NEGADOS': 'Negados'
         }
         dfFiltered = df[df['name'].isin(labels.keys())]
         dfFiltered['label'] = dfFiltered['name'].map(labels)
         dfFiltered = dfFiltered[['label', 'int_value']]
         total = dfFiltered['int_value'].sum()
 
         plt.figure(figsize=(8, 6))
         ax = sns.barplot(x='label', y='int_value', data=dfFiltered,
                          palette=['#4CAF50', '#F44336', '#FF9800', '#9E9E9E', '#2196F3'], edgecolor='white', linewidth=2)
         plt.ylabel('Quantidade')
         plt.title('Autorizações (Mês Atual)')
         plt.xticks(rotation=45, ha='right')
         plt.grid(axis='y', linestyle='--', alpha=0.7)
 
         for i, (label, value) in enumerate(zip(dfFiltered['label'], dfFiltered['int_value'])):
             percentage = (value / total) * 100 if total > 0 else 0
             ax.text(i, value + 2, f"{value} ({percentage:.1f}%)", ha='center', fontsize=10, fontweight='bold')
 
         st.pyplot(plt)
    
    def showBillingTable(self, df):
        faturaveisAutorizadas = df.loc[df["name"] == "IMND_MES_ATUAL_FATURAVEIS_AUTORIZADAS", "int_value"].values[0]
        faturaveisNaoAutorizadas = df.loc[df["name"] == "IMND_MES_ATUAL_FATURAVEIS_NAO_AUTORIZADAS", "int_value"].values[0]

        st.markdown("""
            <style>
                .table-box {
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 14px;
                    width: 100%;
                    padding: 10px;
                    margin: 10px auto;
                }
                .table-box table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .table-box th, .table-box td {
                    border: 1px solid #ccc;
                    padding: 8px;
                }
                .table-box th {
                    background-color: #585858;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="table-box">
                <h2>Consultas Faturáveis</h2>
                <table>
                    <tr>
                        <th>Autorizadas</th>
                        <th>Não Autorizadas</th>
                    </tr>
                    <tr>
                        <td>{faturaveisAutorizadas}</td>
                        <td>{faturaveisNaoAutorizadas}</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(
            """
            <style>
                .stButton>button {
                    background-color: #0E1117 !important;
                    color: #f1f1f1 !important;
                    border: none !important;
                    border-radius: 5px !important;
                    padding: 10px 20px !important;
                    font-size: 16px !important;
                }
                .stButton>button:hover {
                    background-color: #333 !important;
                }
            </style>
            """,
            unsafe_allow_html=True
        )




    def showPendingTable(self, df):
        pending_value = df.loc[df["name"] == "IMND_AUTORIZACAO_PENDENTES_ATRASADOS_MES_ATUAL", "int_value"].values[0]

        st.markdown("""
            <style>
                .table-box {
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 14px;
                    width: 100%;
                    padding: 10px;
                    margin: 10px auto;
                }
                .table-box h2 {
                    margin-bottom: 10px;
                }
                .pending-value {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px;
                    border-top: 1px solid #ccc;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="table-box">
                <h2>Consultas Pendentes Atrasadas</h2>
                <div class="pending-value">{pending_value}</div>
            </div>
        """, unsafe_allow_html=True)

    
    def showLastExecutionDate(self, df):
        last_execution_date = df.loc[df["name"] == "IMND_DATA_DA_ULTIMA_EXECUCAO", "string_value"].values[0]
        
        st.markdown("""
            <div style='text-align: center; margin-top: 20px;'>
                <h3>📅 Data da Última Execução:</h3>
                <h2>{}</h2>
            </div>
        """.format(last_execution_date), unsafe_allow_html=True)
    
    def main(self):
        st.subheader("📊 IMND - Portal do Cliente - Priortec")
        
        try:
            with st.spinner('Carregando dados...'):
                df = self.getAllDataFromDb()
            if df.empty:
                st.warning("Nenhum dado foi retornado da consulta.")
                return

            col1, col2 = st.columns([1, 0.5])
            with col1:
                st.subheader("📌 Status dos Computadores")
                self.showStatusTable(df)
                self.showBillingTable(df)
                self.showPendingTable(df)
            with col2:
                st.subheader("📈 Aprovação de Consultas")
                self.showApprovalChart(df)
                self.showLastExecutionDate(df)

        
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    app = main()
    app.main()
