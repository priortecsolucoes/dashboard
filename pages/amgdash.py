import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
from datetime import datetime, timezone
import pytz

# Configuração da página
st.set_page_config(page_title="Portal AMG", layout="wide")

# Verificação de acesso e configuração do sidebar
pagesAcess = st.session_state.get("pagesAcess", 0)
access = pagesAcess[0]
if "admin" not in access:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {display: none;}
            .e14lo1l1 {display: none !important;}
            div.block-container {padding-top: 50px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {display: block;}
            div.block-container {padding-top: 50px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

class AmgDash:
    def __init__(self):
        load_dotenv()
        self.dbHost = os.getenv('DBHOST_AMG')
        self.dbName = os.getenv('DBNAME_AMG')
        self.dbUser = os.getenv('DBUSER_AMG')
        self.dbPassword = os.getenv('DBPASSWORD_AMG')
        self.dbPort = os.getenv('DBPORT_AMG')
        self.conn = psycopg2.connect(
            host=self.dbHost,
            database=self.dbName,
            user=self.dbUser,
            password=self.dbPassword,
            port=self.dbPort
        )

    def getErrors(self):


        try:
            # Nova consulta para obter os erros
            query = """
                SELECT "ERROR", COUNT(*) AS total
                FROM "OCCUPATIONAL_FILE"
                WHERE "STATUS" IN ('PE','AR')
                GROUP BY "ERROR"
                ORDER BY total DESC;
            """
            df = pd.read_sql_query(query, self.conn)
            if df.empty:
                raise ValueError("A consulta não retornou dados.")
                
            # Renomeando as colunas para manter compatibilidade com o código existente
            df = df.rename(columns={"ERROR": "DESCRIÇÃO", "total": "QUANTIDADE"})
            return df
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados ou executar a consulta: {str(e)}")
            return pd.DataFrame()

    def display_errors_table(self):
        df = self.getErrors()
        if df.empty:
            st.info("\u2705 Nenhum erro encontrado.")
        else:
            st.write("### Erros encontrados")
            # Usando use_container_width=True para manter a largura completa
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}), use_container_width=True)

    def getAllDataFromDb(self):
        try:
            # Nova consulta para obter os status
            query = """
                SELECT "STATUS", COUNT(*) AS total_registros
                FROM "OCCUPATIONAL_FILE"
                WHERE "STATUS" IN ('PE', 'PM', 'AJ', 'DEL', 'AI', 'FI','AR')
                GROUP BY "STATUS";
            """
            df = pd.read_sql_query(query, self.conn)
            if df.empty:
                raise ValueError("A consulta não retornou dados.")
                
            # Convertendo os códigos de status para nomes mais descritivos
            status_map = {
                'PE': 'PENDENTES',
                'PM': 'EM_PROCESSAMENTO',
                'AJ': 'AJUSTADOS',
                'DEL': 'DELETADOS',
                'AI': 'INVALIDOS',
                'FI': 'FINALIZADOS',
                'AR': 'REICIDENTES'
            }
            
            # Criando uma nova coluna 'name' para manter compatibilidade com o código existente
            df['name'] = df['STATUS'].map(lambda x: f"AMG_{status_map.get(x, x)}")
            
            # Renomeando a coluna de valores para manter compatibilidade
            df = df.rename(columns={"total_registros": "int_value"})
            
            # Adicionando colunas vazias que existiam no DataFrame original
            df['string_value'] = ""
            df['registration_date'] = pd.Timestamp.now()
            
            return df
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados ou executar a consulta: {str(e)}")
            return pd.DataFrame()
    
    def getFileById(self, file_id):
        try:
            query = """
                SELECT "ID", "REGISTRATION_DATE", "FILE_NAME", "CPF", "EXAM_TYPE_AUTOMATIC", 
                "CRM_AUTOMATIC", "DOCTOR_DATE_AUTOMATIC", "ERROR", "STATUS", 
                "NEW_NAME", "CRM_MANUAL", "DOCTOR_DATE_MANUAL", "EMPLOYEE_CODE_MANUAL", 
                "EMPLOYEE_CODE_AUTOMATIC", "UF", "TEXT_READ" 
                FROM "OCCUPATIONAL_FILE"
                WHERE "ID" = %s
            """
            df = pd.read_sql_query(query, self.conn, params=(file_id,))
            return df
        except Exception as e:
            st.error(f"❌ Erro ao buscar arquivo com ID {file_id}: {str(e)}")
            return pd.DataFrame()

    def showSatusTable(self, df):
        st.write("### Tabela de Status")
        if df.empty:
            st.info("✅ Nenhum status encontrado.")
        else:
            # Selecionando apenas as colunas relevantes para exibição
            display_df = df[['name', 'int_value']].copy()
            
            # Renomeando as colunas para exibição
            display_df.columns = ['Status', 'Quantidade']
            
            # Removendo o prefixo "AMG_" para melhor visualização
            display_df['Status'] = display_df['Status'].str.replace('AMG_', '')
            
            st.dataframe(display_df.style.set_properties(**{'text-align': 'center'}), use_container_width=True)

    def plot_bar_chart(self, df):
        if df.empty:
            st.warning("⚠️ O DataFrame está vazio. Nenhum gráfico será exibido.")
            return

        # Verificando a coluna de valores numéricos
        if "int_value" in df.columns and not df["int_value"].isnull().all():
            value_col = "int_value"
        else:
            st.error("❌ Não há valores numéricos disponíveis para o gráfico.")
            return

        # Calcula o total e a porcentagem para cada valor
        total = df[value_col].sum()
        df["percentage"] = df[value_col] / total * 100 if total > 0 else 0
        
        # Definindo uma paleta de cores baseada no status
        palette = {
            'AMG_FINALIZADOS': '#4CAF50',      # Verde
            'AMG_PENDENTES': '#FF9800',        # Laranja
            'AMG_AJUSTADOS': '#9E9E9E',        # Cinza
            'AMG_DELETADOS': '#795548',        # Marrom
            'AMG_INVALIDOS': '#F44336',        # Vermelho
            'AMG_EM_PROCESSAMENTO': '#2196F3', # Azul
            'AMG_REICIDENTES': '#673AB7'       # Roxo
        }
        
        # Tamanho reduzido para o gráfico
        fig, ax = plt.subplots(figsize=(5, 3), facecolor='#0E1117')
        
        # Criando o gráfico de barras
        bars = sns.barplot(
            x="name", 
            y=value_col, 
            data=df,
            palette=[palette.get(name, '#777777') for name in df["name"]],
            edgecolor='white', 
            linewidth=0.5,
            ax=ax
        )
        
        # Ajustando o fundo do gráfico
        ax.set_facecolor('#0E1117')
        
        # Removendo labels para economizar espaço
        ax.set_xlabel("", fontsize=8)
        ax.set_ylabel("Quantidade", fontsize=8, color='white')
        
        # Ajustando os rótulos do eixo X para melhorar legibilidade
        # Removendo o prefixo "AMG_" para melhor visualização
        labels = [item.get_text().replace('AMG_', '') for item in ax.get_xticklabels()]
        ax.set_xticklabels(labels, rotation=45, ha='right', color='white', fontsize=7)
        ax.tick_params(axis='y', colors='white', labelsize=7)
        
        # Grid sutil
        ax.grid(axis='y', linestyle='--', alpha=0.1, color='gray')
        
        # Ajustando os limites do eixo Y
        y_max = df[value_col].max() * 1.1
        ax.set_ylim(0, y_max)
        
        # Adicionando os valores e percentuais nas barras de forma compacta
        for i, (name, value, percentage) in enumerate(zip(df["name"], df[value_col], df["percentage"])):
            # Formatando o texto para mostrar no topo da barra
            text = f"{value}\n({percentage:.1f}%)"
            
            # Posicionando o texto no topo da barra
            ax.text(
                i, 
                value + (y_max * 0.01),
                text,
                ha='center', 
                va='bottom',
                fontsize=7, 
                fontweight='bold', 
                color='white',
                bbox=dict(facecolor='#1E1E1E', alpha=0.5, boxstyle='round,pad=0.1', edgecolor='none')
            )
        
        # Removendo as bordas do gráfico
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Ajustando as margens para minimizar o espaço em branco
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.15)
        
        # Retornando a figura para controlar onde será exibida
        return fig
    
    '''
    def file_search_form(self):
        st.subheader("🔍 Buscar Arquivo")
        with st.form("file_search_form"):
            file_id = st.number_input("ID do Arquivo", min_value=1, step=1, value=6869)
            search_button = st.form_submit_button("Buscar")
            
            if search_button:
                file_data = self.getFileById(file_id)
                if not file_data.empty:
                    st.success(f"✅ Arquivo encontrado")
                    st.dataframe(file_data, use_container_width=True)
                else:
                    st.error(f"❌ Arquivo com ID {file_id} não encontrado")
    '''

    def get_tag_string_value(self):
        dbHost = os.getenv('DBHOST')
        dbName = os.getenv('DBNAME')
        dbUser = os.getenv('DBUSER')
        dbPassword = os.getenv('DBPASSWORD')
        dbPort = os.getenv('DBPORT')

        try:
            db_url = f"postgresql+psycopg2://{dbUser}:{dbPassword}@{dbHost}:{dbPort}/{dbName}"
            self.engine = create_engine(db_url)
        except Exception as e:
            st.error(f"Erro na conexão com o banco: {e}")
            self.engine = None

        query = """
        SELECT "string_value", "registration_date" FROM "tag_value"
        WHERE "tag_id" = 34
        ORDER BY "registration_date" DESC
        LIMIT 1;
        """
        
        try:
        df = pd.read_sql_query(query, self.engine)
        
        if df.empty:
            return pd.DataFrame({'status': ['🔴 INATIVO'], 'string_value': ['Sem dados']})
        
        # Obter o valor atual de string_value (que contém a data/hora)
        data_hora_str = df['string_value'].iloc[0]
        
        # Converter para datetime com formato brasileiro
        try:
            data_hora = datetime.strptime(data_hora_str, '%d/%m/%Y %H:%M:%S')
            
            # Se a data no banco não tem timezone, presumimos que está em horário local
            # Definir explicitamente como horário de Brasília
            timezone_brasil = pytz.timezone('America/Sao_Paulo')
            data_hora = timezone_brasil.localize(data_hora)
            
            # Obter a hora atual em UTC
            hora_atual_utc = datetime.now(timezone.utc)
            
            # Converter para o horário de Brasília
            hora_atual = hora_atual_utc.astimezone(timezone_brasil)
            
            # Calcular a diferença em segundos
            diferenca_segundos = (hora_atual - data_hora).total_seconds()
            
            # Remova os logs de depuração quando estiver funcionando
            st.text(f"DEBUG - Hora atual (Brasília): {hora_atual}")
            st.text(f"DEBUG - Data/hora do registro (Brasília): {data_hora}")
            st.text(f"DEBUG - Diferença em segundos: {diferenca_segundos}")
            st.text(f"DEBUG - Limite em segundos: 1800")
            
            # Determinar o status
            if diferenca_segundos < 1800:  # 30 minutos = 1800 segundos
                status = '🟢 ATIVO'
            else:
                status = '🔴 INATIVO'
            
            # Criar DataFrame com resultado
            result_df = pd.DataFrame({
                'status': [status],
                'string_value': [data_hora_str]
            })
            
            return result_df
            
        except ValueError:
            st.error(f"Formato de data inválido: '{data_hora_str}'")
            return pd.DataFrame({'status': ['🔴 INATIVO'], 'string_value': [data_hora_str]})
            
    except Exception as e:
        st.error(f"Erro ao buscar dados do banco: {e}")
        return pd.DataFrame({'status': ['🔴 INATIVO'], 'string_value': [f'Erro: {str(e)}']})
    
    # Aqui está a nova função separada para visualização do Status APISOC
    def display_api_status(self):
        st.header("🔄 Status APISOC")
        api_status_df = self.get_tag_string_value()
        if not api_status_df.empty:
            # Selecionando apenas as colunas de status e último registro
            api_status_df = api_status_df[['status', 'string_value']]
            
            # Renomeando as colunas para exibição
            api_status_df.columns = ['Status', 'Último Registro']
            
            # Aplicando estilo à tabela
            st.dataframe(
                api_status_df.style.set_properties(**{
                    'text-align': 'center',
                    'font-weight': 'bold',
                    'background-color': api_status_df['Status'].map(
                        lambda x: 'rgba(76, 175, 80, 0.2)' if x == '🟢 ATIVO' else 'rgba(244, 67, 54, 0.2)'
                    )
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhum dado de status APISOC disponível")

    def get_aso_reading_status(self):
        try:
            # Configurar conexão com o banco de dados do dashboard (onde está a tabela tag_value)
            dbHost = os.getenv('DBHOST')
            dbName = os.getenv('DBNAME')
            dbUser = os.getenv('DBUSER')
            dbPassword = os.getenv('DBPASSWORD')
            dbPort = os.getenv('DBPORT')
            
            # Criar conexão com o banco do dashboard
            db_url = f"postgresql+psycopg2://{dbUser}:{dbPassword}@{dbHost}:{dbPort}/{dbName}"
            dash_engine = create_engine(db_url)
            
            # Primeiro, obter o tamanho da pasta a partir da tabela tag_value do banco dashboard
            pasta_query = """
            SELECT int_value 
            FROM tag_value 
            WHERE id = 47 AND tag_id = 35;
            """
            
            # Obter os dados do último registro do banco principal
            tempo_query = """
            SELECT 
                EXTRACT(EPOCH FROM (NOW() - MAX("REGISTRATION_DATE"))) / 60 as minutos_desde_ultimo_registro,
                MAX("REGISTRATION_DATE") as ultimo_registro
            FROM 
                "OCCUPATIONAL_FILE";
            """
            
            # Executar as consultas nos bancos corretos
            pasta_df = pd.read_sql_query(pasta_query, dash_engine)
            tempo_df = pd.read_sql_query(tempo_query, self.conn)
            
            # Verificar se as consultas retornaram resultados
            if pasta_df.empty or tempo_df.empty:
                return pd.DataFrame({'status': ['🔴 INATIVO'], 'ultimo_registro': ['N/A'], 'tamanho_pasta': [0]})
            
            # Extrai os valores necessários
            tamanho_pasta = pasta_df['int_value'].iloc[0]
            minutos = tempo_df['minutos_desde_ultimo_registro'].iloc[0]
            ultimo_registro = tempo_df['ultimo_registro'].iloc[0]
            
            # Aplicar a lógica solicitada:
            # - Se tiver mais de 5 minutos e pasta vazia (=0): ATIVO (verde)
            # - Se tiver mais de 5 minutos e pasta com arquivos (>0): INATIVO (vermelho)
            # - Para menos de 5 minutos, mantém o comportamento atual (ATIVO)
            status = '🟢 ATIVO'
            if minutos > 5:
                if tamanho_pasta > 0:
                    status = '🔴 INATIVO'
            
            # Criar DataFrame com os resultados
            result_df = pd.DataFrame({
                'status': [status],
                'ultimo_registro': [pd.to_datetime(ultimo_registro).strftime('%d/%m/%Y %H:%M:%S')],
                'tamanho_pasta': [tamanho_pasta]
            })
            
            return result_df
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar status ASOReading: {str(e)}")
            return pd.DataFrame({'status': ['🔴 INATIVO'], 'ultimo_registro': ['Erro'], 'tamanho_pasta': [0]})

    def display_aso_reading_status(self):
        st.header("🔄 Status ASOReading")
        aso_status_df = self.get_aso_reading_status()
        
        if not aso_status_df.empty:
            # Renomeando as colunas para exibição
            aso_status_df.columns = ['Status', 'Último Registro', 'Arquivos na Pasta']
            
            # Aplicando estilo à tabela
            st.dataframe(
                aso_status_df.style.set_properties(**{
                    'text-align': 'center',
                    'font-weight': 'bold',
                    'background-color': aso_status_df['Status'].map(
                        lambda x: 'rgba(76, 175, 80, 0.2)' if x == '🟢 ATIVO' else 'rgba(244, 67, 54, 0.2)'
                    )
                }),
                use_container_width=True
            )
            
            # Adicionando uma explicação da lógica para facilitar a compreensão
            with st.expander("❓ Como funciona o status"):
                st.markdown("""
                - **🟢 ATIVO**: Sistema funcionando corretamente
                  - Último processamento há menos de 5 minutos, ou
                  - Último processamento há mais de 5 minutos e pasta vazia (0 arquivos)
                - **🔴 INATIVO**: Possível problema no sistema
                  - Último processamento há mais de 5 minutos e pasta com arquivos pendentes
                """)
        else:
            st.info("Nenhum dado de status ASOReading disponível")

    def execute(self):
        st.title("📊 AMG - Portal do Cliente - Priortec")
        
        # Obter dados
        df = self.getAllDataFromDb()
        
        # Seção 1: Tabela de Status
        st.header("📋 Tabela de Valores")
        self.showSatusTable(df)
        
        # Seção 2: Erros encontrados
        st.header("⚠️ Erros Encontrados")
        self.display_errors_table()

        # Seção 3: Status APISOC
        self.display_api_status()
        
        # Seção 4: Status ASOReading (nova seção)
        self.display_aso_reading_status()
        
        # Seção 5: Gráfico de barras
        st.header("📊 Visualização Gráfica")
        
        # Criando duas colunas para o gráfico, permitindo espaço em ambos os lados
        left_col, graph_col, right_col = st.columns([1, 2, 1])
        
        with graph_col:
            st.write("#### Distribuição das Tags")
            fig = self.plot_bar_chart(df)
            if fig:
                st.pyplot(fig)
        
        # # Seção 6: Formulário de busca de arquivo
        # st.divider()
        # self.file_search_form()

if __name__ == "__main__":
    loop = AmgDash()
    loop.execute()
