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
from utils.DataExporter import DataExporter
import time
st.set_page_config(page_title="Portal IMND", layout="wide")
pagesAcess = st.session_state.get("pagesAcess")
if not pagesAcess:
    st.switch_page("loginScreen.py")
access = pagesAcess[0]
st.markdown("""
    <style>
        div.block-container {padding-top: 20px !important;}
        }
    </style>
    """, unsafe_allow_html=True)
if 'admin' not in access:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
        .e14lo1l1  {
            display: none !important;
        }
     
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: block;}
     
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
        self.headers = os.getenv('IMND_ACCESS_TOKEN')
        self.teste = DataExporter()
    def getAllDataFromDb(self):
        try:
            query = """
                SELECT tag.name, tag_value.string_value, tag_value.int_value, tag_value.registration_date
                FROM tag_value
                JOIN tag ON tag_value.tag_id = tag.id
                WHERE tag.name IN (
                    'IMND_MES_ATUAL_APROVADOS',
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
            'IMND_MES_ATUAL_APROVADOS': 'Aprovados',
            'IMND_MES_ATUAL_PENDENTES': 'Pendentes',
            'IMND_MES_ATUAL_INELEGIVEIS': 'Inelegíveis',
            'IMND_MES_ATUAL_NEGADOS': 'Negados'
        }
        dfFiltered = df[df['name'].isin(labels.keys())]
        dfFiltered['label'] = dfFiltered['name'].map(labels)
        dfFiltered = dfFiltered[['label', 'int_value']]

        # Ordenando para garantir que "Aprovados" seja o primeiro
        dfFiltered = dfFiltered.set_index('label').loc[['Aprovados',  'Pendentes', 'Inelegíveis', 'Negados']].reset_index()

        total = dfFiltered['int_value'].sum()

        # Definindo a paleta de cores para garantir que "Aprovados" será verde
        palette = ['#4CAF50', '#F44336', '#FF9800', '#9E9E9E', '#2196F3']

        plt.figure(figsize=(8, 6), facecolor='#0E1117')
        ax = sns.barplot(x='label', y='int_value', data=dfFiltered,
                        palette=palette,
                        edgecolor='white', linewidth=2)
        
        ax.set_facecolor('#0E1117')
        plt.ylabel('Quantidade', color='white')
        plt.title('Autorizações (Mês Atual)', color='white')
        plt.xticks(rotation=45, ha='right', color='white')
        plt.yticks(color='white')
        plt.grid(axis='y', linestyle='--', alpha=0.7, color='gray')
        
        for i, (label, value) in enumerate(zip(dfFiltered['label'], dfFiltered['int_value'])):
            percentage = (value / total) * 100 if total > 0 else 0
            # Ajuste da margem com valor maior para o 'y'
            ax.text(i, value + 200, f"{value} ({percentage:.1f}%)", ha='center', fontsize=12, fontweight='bold', color='white')
        
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
                    width: 100px;
                    padding: 10px;
                    margin: 10px auto;
                    margin-left: 0px;
                }
                .table-box table {
                    width: 100px;
                    border-collapse: collapse;
                }
                .table-box th, .table-box td {
                    border: 1px solid #ccc;
                    padding: 8px;
                }
                .table-box th {
                    background-color: #585858;
                }
                .bold-value {
                    font-weight: bold;
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
                        <td class="bold-value"><strong>{faturaveisAutorizadas}</strong></td>
                        <td class="bold-value"><strong>{faturaveisNaoAutorizadas}</strong></td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)


    def showPendingTable(self, df):
        pending_value = df.loc[df["name"] == "IMND_AUTORIZACAO_PENDENTES_ATRASADOS_MES_ATUAL", "int_value"].values[0]

        st.markdown("""
            <style>
                .table-box {
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 25px;
                    width: 420px; 
                    padding: 10px;
                    height: 200px;
                    margin: 10px auto;
                    margin-left: 0px;
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

                .table-box h2 {
                    font-size: 20px;
                }

                .pending-value {
                    font-size: 55px;
                    font-weight: bold;
                    margin-top: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="table-box">
                <h2>Consultas Pendentes Atrasadas</h2>
                <div class="pending-value"><strong>{pending_value}</strong></div>
            </div>
        """, unsafe_allow_html=True)

    
    def showLastExecutionDate(self, df):
        last_execution_date = df.loc[df["name"] == "IMND_DATA_DA_ULTIMA_EXECUCAO", "string_value"].values[0]
        
        st.markdown(f"""
            <style>
                .last-execution {{
                    text-align: center;
                    margin-top: 20px;
                }}
                .last-execution h3 {{
                    font-size: 20px;
                }}
                .last-execution h2 {{
                    font-size: 20px;
                }}
            </style>
            <div class="last-execution">
                <h3>📅 Data da Última Execução:</h3>
                <h2>{last_execution_date}</h2>
            </div>
        """, unsafe_allow_html=True)


    
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
                inner_col1, inner_col2 = st.columns(2)
                with inner_col1:
                    self.showBillingTable(df)
                with inner_col2:
                    self.showPendingTable(df)
 
                # Adicionando espaço antes dos botões e centralizando-os
                st.markdown("""
                    <style>
                        .custom-button-container {
                            display: flex;
                            gap: 20px;
                            margin: auto;
 
                        }
                    </style>
                """, unsafe_allow_html=True)
 
                # Criando um container para os botões centralizados
                st.markdown('<div class="custom-button-container">', unsafe_allow_html=True)
                
                # 📥 Instância do DataExporter
                exporter = DataExporter()

                # 📊 Exportação de Planilhas
                st.subheader("📌 Exportar Planilhas")
                col_exp1, col_exp2, col_exp3 = st.columns(3)

                # 🚫 Consulta apenas ao clicar no botão
                with col_exp1:
                    if st.button('Solicitar Consultas Não Autorizadas'):
                        st.toast('Gerando arquivo...', icon="⏳")
                        output, filename = exporter.processNotBillableQueries()
                        if output:
                            st.download_button(
                                label="📥  Baixar Consultas Não Autorizadas",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")

                with col_exp2:
                    if st.button('Solicitar Consultas Pendentes Atrasadas'):
                        st.toast('Gerando arquivo Pendentes Atrasadas...', icon="⏳")
                        output, filename = exporter.checkPendingAuthorizationForCurrentMonth()
                        if output:
                            st.download_button(
                                label="📥 Baixar  Consultas Pendentes Atrasadas",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")
                with col_exp3:
                    if st.button('Solicitar Consultas Autorizadas'):
                        st.toast('Gerando arquivo Consultas Autorizadas...', icon="⏳")
                        output, filename = exporter.processBillableQueries()
                        if output:
                            st.download_button(
                                label="📥 Baixar Consultas Autorizadas",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")
            with col2:
                st.subheader("📈 Aprovação de Consultas")
                self.showApprovalChart(df)
                self.showLastExecutionDate(df)
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    app = main()
    app.main()
