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
        div.block-container {
            padding-top: 20px !important;
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
                    'IMND_MES_ATUAL_PENDENCIAS_IMEDIATAS',
                    'IMND_MES_ATUAL_FATURAVEIS_NEGADOS',
                    'IMND_MES_ATUAL_FATURAVEIS_INELEGIVEIS',
                    'IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO16_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO17_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO18_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO19_AUTORIZACAO_ULTIMO_REGISTRO',
                    'IMND_ROBO03_HEARTBEAT',
                    'IMND_ROBO05_HEARTBEAT',
                    'IMND_ROBO06_HEARTBEAT',
                    'IMND_ROBO07_HEARTBEAT',
                    'IMND_ROBO08_HEARTBEAT',
                    'IMND_ROBO16_HEARTBEAT',
                    'IMND_ROBO17_HEARTBEAT',
                    'IMND_ROBO18_HEARTBEAT',
                    'IMND_ROBO19_HEARTBEAT',
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

    def determineStatus(self, row, currentTime):
        authMinutes = (currentTime - row['authorization_datetime_value']).total_seconds() / 60
        heartbeatMinutes = (currentTime - row['heartbeat_datetime_value']).total_seconds() / 60
        
        if authMinutes < 10:
            return '🟢 AUTORIZANDO'
        elif heartbeatMinutes < 10 and authMinutes >= 10:
            return '🟡 ATIVO'
        else:
            return '🔴 INATIVO'
    
    def showStatusTable(self, df):
        data = {
            "COMPUTADOR": ["IMND_ROBO3", "IMND_ROBO5", "IMND_ROBO6", "IMND_ROBO7", "IMND_ROBO8", "IMND_ROBO16", "IMND_ROBO17", "IMND_ROBO18", "IMND_ROBO19"],
            "ÚLTIMA AUTORIZAÇÃO": [
                df.loc[df["name"] == "IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO16_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO17_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO18_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO19_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
            ],
            "HEARTBEAT": [
                df.loc[df["name"] == "IMND_ROBO03_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO05_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO06_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO07_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO08_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO16_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO17_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO18_HEARTBEAT", "string_value"].values[0],
                df.loc[df["name"] == "IMND_ROBO19_HEARTBEAT", "string_value"].values[0],
            ],
        }
        statusDf = pd.DataFrame(data)
        
        statusDf['authorization_datetime_value'] = pd.to_datetime(statusDf['ÚLTIMA AUTORIZAÇÃO'], format='%d/%m/%Y %H:%M:%S')
        statusDf['heartbeat_datetime_value'] = pd.to_datetime(statusDf['HEARTBEAT'], format='%d/%m/%Y %H:%M:%S')

        currentTime = datetime.now(timezone('America/Sao_Paulo')).replace(tzinfo=None)
        statusDf['STATUS'] = statusDf.apply(self.determineStatus, axis=1, currentTime=currentTime)
        
        statusDf = statusDf[['COMPUTADOR', 'STATUS', 'ÚLTIMA AUTORIZAÇÃO']]
        st.dataframe(statusDf, use_container_width=True)
    
    def showApprovalChart(self, df):
        labels = {
            'IMND_MES_ATUAL_APROVADOS': 'Aprovados',
            'IMND_MES_ATUAL_PENDENTES': 'Pendentes',
            'IMND_MES_ATUAL_PENDENCIAS_IMEDIATAS': 'Pendências Imediatas',
            'IMND_MES_ATUAL_INELEGIVEIS': 'Inelegíveis',
            'IMND_MES_ATUAL_NEGADOS': 'Negados'
        }
        dfFiltered = df[df['name'].isin(labels.keys())]
        dfFiltered['label'] = dfFiltered['name'].map(labels)
        dfFiltered = dfFiltered[['label', 'int_value']]

        # Ordenando para garantir que "Aprovados" seja o primeiro
        order = ['Aprovados', 'Pendentes', 'Pendências Imediatas', 'Inelegíveis', 'Negados']
        dfFiltered = (
            dfFiltered
            .set_index('label')
            .reindex(order, fill_value=0)
            .reset_index()
        )

        total = dfFiltered['int_value'].sum()
        # Definindo a paleta de cores para garantir que "Aprovados" será verde
        palette = ['#4CAF50', '#F44336', '#FF7A00', '#FF9800', '#9E9E9E', '#2196F3']

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
        faturaveisAutorizadas = int(
            df.loc[df["name"] == "IMND_MES_ATUAL_FATURAVEIS_AUTORIZADAS", "int_value"]
            .fillna(0)
            .head(1)
            .iloc[0]
        )
        faturaveisNaoAutorizadas = int(
            df.loc[df["name"] == "IMND_MES_ATUAL_FATURAVEIS_NAO_AUTORIZADAS", "int_value"]
            .fillna(0)
            .head(1)
            .iloc[0]
        )
        faturaveisInelegiveis = int(
            df.loc[df["name"] == "IMND_MES_ATUAL_FATURAVEIS_INELEGIVEIS", "int_value"]
            .fillna(0)
            .head(1)
            .iloc[0]
        )

        faturaveisNegadas = int(
            df.loc[df["name"] == "IMND_MES_ATUAL_FATURAVEIS_NEGADOS", "int_value"]
            .fillna(0)
            .head(1)
            .iloc[0]
        )

        st.markdown("""
            <style>
            .table-box {
                border: 2px solid #ccc;
                border-radius: 12px;
                text-align: center;
                font-size: 18px;
                padding: 16px;
                width: 600px;
                box-sizing: border-box;
                overflow-x: auto;
            }
            .table-box h2 {
                margin-bottom: 12px;
                font-size: 20px;
            }
            .table-wrapper {
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }

            .table-box table {
                /* 🔥 Alteração: table-layout definido como 'fixed' */
                table-layout: fixed;
                width: 100%;
                min-width: fit-content;
            }

            .table-box th {
                background-color: #585858;
                font-weight: 500;          /* 🔽 menos "grosso" */
                padding: 6px 6px 6px 10px; /* 🔽 menos altura + mais à esquerda */
                font-size: 11px;           /* 🔽 texto menor */
                line-height: 1.15;         /* 🔽 reduz altura da linha */
                text-align: left;          /* ✅ alinha à esquerda */
                white-space: normal;
                border: 1px solid #555;
            }


            .table-box td {
                border: 1px solid #555;
                padding: 12px 8px;
                font-size: 16px;
                white-space: normal;
            }

            .bold-value {
                font-weight: bold;
                font-size: 17px;
            }

            .table-box th:nth-child(1) { min-width: 170px; }
            .table-box th:nth-child(2) { min-width: 130px; }
            .table-box th:nth-child(3) { min-width: 100px; }
            .table-box th:nth-child(4) { min-width: 100px; }

            /* 📱 Mobile */
            @media (max-width: 768px) {
                .table-box {
                    padding: 12px;
                }
                
                .table-box h2 {
                    font-size: 18px;
                }

                .table-box table {
                    min-width: 400px;
                }

                .table-box th,
                .table-box td {
                    font-size: 14px;
                    padding: 10px 6px;
                }
                
                .bold-value {
                    font-size: 15px;
                }
                
                .table-box th:nth-child(1) { min-width: 90px; }
                .table-box th:nth-child(2) { min-width: 110px; }
                .table-box th:nth-child(3) { min-width: 90px; }
                .table-box th:nth-child(4) { min-width: 80px; }
            }
            
            /* 📱 Mobile muito pequeno */
            @media (max-width: 480px) {
                .table-box table {
                    min-width: 350px;
                }
                
                .table-box th,
                .table-box td {
                    font-size: 13px;
                    padding: 8px 4px;
                }
                
                .table-box th:nth-child(2) { 
                    font-size: 12.5px; /* Reduz um pouco para "Não Autorizadas" */
                }
            }
            </style>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="table-box">
                <h2>Consultas Faturáveis</h2>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Aprovadas</th>
                                <th>Não Autorizadas</th>
                                <th>Inelegíveis</th>
                                <th>Negadas</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="bold-value">{faturaveisAutorizadas}</td>
                                <td class="bold-value">{faturaveisNaoAutorizadas}</td>
                                <td class="bold-value">{faturaveisInelegiveis}</td>
                                <td class="bold-value">{faturaveisNegadas}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def showPendingTable(self, df):
        st.markdown("""
            <style>
                .table-box {
                    border: 2px solid #ccc;
                    border-radius: 12px;
                    text-align: center;

                    /* Responsividade */
                    width: 90%;
                    max-width: 320px;
                    padding: 16px;
                    margin: 12px auto;

                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }

                .table-box h2 {
                    font-size: clamp(16px, 4vw, 20px);
                    margin-bottom: 8px;
                }

                .pending-value {
                    font-size: clamp(36px, 8vw, 55px);
                    font-weight: bold;
                }
                @media (max-width: 768px) {
                    .table-box {
                        max-width: 90%;
                        padding: 12px;
                    }
                }
                @media (max-width: 480px) {
                    .table-box h2 {
                        font-size: 16px;
                    }
                    .pending-value {
                        font-size: 40px;
                    }
                }
            </style>
        """, unsafe_allow_html=True)

        pending_value = df.loc[
            df["name"] == "IMND_AUTORIZACAO_PENDENTES_ATRASADOS_MES_ATUAL",
            "int_value"
        ].values[0]

        st.markdown(f"""
            <div class="table-box">
                <h1>Consultas Pendentes Atrasadas (< D-3) </h1>
                <div class="pending-value">{pending_value}</div>
            </div>
        """, unsafe_allow_html=True)
    def showIntegratorPendingTable(self, df):
        st.markdown("""
            <style>
                .table-box {
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 25px;
                    width: 280px; 
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
        
        try:
            query = """
                SELECT count(*) AS total_pendentes
                FROM imnd_authorization
                WHERE imnd_write_status is null or imnd_write_status != 'SUCESSO'
            """
            df = pd.read_sql_query(query, self.conn)
            if df.empty or 'total_pendentes' not in df.columns:
                raise ValueError("A consulta não retornou dados válidos.")

            integrator_pending_value = int(df.loc[0, 'total_pendentes'])
            
            st.markdown(f"""
                <div class="table-box">
                    <h2>Consultas a Integrar IMND</h2>
                    <div class="pending-value"><strong>{integrator_pending_value}</strong></div>
                </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados ou executar a consulta: {str(e)}")
            return pd.DataFrame()
    
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
                inner_col1, inner_col2, inner_col3 = st.columns(3)
                with inner_col1:
                    self.showBillingTable(df)
                with inner_col2:
                    self.showPendingTable(df)
                with inner_col3:
                    self.showIntegratorPendingTable(df)

 
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
                col_exp1, col_exp2, col_exp3, col_exp4, col_exp5 = st.columns(5)
                    
                st.markdown(
                    """
                    <style>
                    div.stButton > button {
                        width: 100% !important;  /* Garante que todos os botões tenham o mesmo tamanho */
                        height: 70px !important;
                        padding: 10px !important;
                        font-size: 16px !important;
                        font-weight: bold !important;
                        border-radius: 8px !important;
                        border: none !important;
                        transition: 0.3s ease-in-out;
                    }
                    
                    div.stButton > button:hover {
                        background-color: #fff !important; /* Azul mais escuro no hover */
                        color: #000 !important;
                    }
                    
                    div.stDownloadButton > button {
                        width: 100% !important; /* Mantém os botões de download alinhados */
                        padding: 8px !important;
                        font-size: 14px !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # 🔹 Simulando colunas para exibição
                col_exp1, col_exp2, col_exp3, col_exp4, col_exp5 = st.columns(5)

                # 🚫 Consulta apenas ao clicar no botão
                with col_exp1:
                    if st.button('Solicitar Consultas Não Autorizadas'):
                        st.toast('Gerando arquivo...', icon="⏳")
                        output, filename = exporter.processNotBillableQueries()
                        if output:
                            st.download_button(
                                label="📥 Baixar Consultas Não Autorizadas",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")

                with col_exp2:
                    if st.button('Solicitar Consultas Pendentes Atrasadas'):
                        st.toast('Gerando arquivo...', icon="⏳")
                        output, filename = exporter.checkPendingAuthorizationForCurrentMonth()
                        if output:
                            st.download_button(
                                label="📥 Baixar Consultas Pendentes Atrasadas",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")

                with col_exp3:
                    if st.button('Solicitar Consultas Autorizadas'):
                        st.toast('Gerando arquivo...', icon="⏳")
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

                with col_exp4:
                    if st.button('Solicitar Consultas Negadas'):  # 🔹 Removidos espaços extras
                        st.toast('Gerando arquivo...', icon="⏳")
                        output, filename = exporter.processDeniedQueries()
                        if output:
                            st.download_button(
                                label="📥 Baixar Consultas Negadas",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")

                with col_exp5:
                    if st.button('Solicitar Consultas Inelegíveis'):  # 🔹 Corrigido erro de digitação
                        st.toast('Gerando arquivo...', icon="⏳")
                        output, filename = exporter.processIneligibleQueries()
                        if output:
                            st.download_button(
                                label="📥 Baixar Consultas Inelegíveis",
                                data=output,
                                file_name=filename,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        else:
                            st.warning("Nenhum dado encontrado para exportação.")
                
            with col2:
                st.subheader(f"📈 Aprovação de Consultas")
                self.showApprovalChart(df)
                self.showLastExecutionDate(df)
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")

if __name__ == "__main__":
    app = main()
    app.main()
