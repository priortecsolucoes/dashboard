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

        # Layout do Streamlit com colunas
        col1, col2 = st.columns([1, 1])  # Define duas colunas de tamanho igual

        # Exibir a tabela na primeira coluna
        with col1:
            st.subheader("📋 Tabela de Valores")
            df_display = df[["name", value_col, "display_text"]].rename(columns={"name": "Categoria", value_col: "Valor", "display_text": "Qtd (%)"})
            st.dataframe(df_display, hide_index=True)

        # Criar e exibir o gráfico na segunda coluna
        with col2:
            st.subheader("📊 Gráfico de Valores")
            palette = ['#4CAF50', '#F44336', '#FF9800', '#9E9E9E', '#2196F3', '#4156F7']
            plt.figure(figsize=(8, 6), facecolor='#0E1117')
            
            # Use 'name' (não renomeada) para o eixo X
            ax = sns.barplot(x=df["name"], y=df[value_col], data=df,
                            palette=palette,
                            edgecolor='black', linewidth=1)

            # Definir limite superior para "achatar" o gráfico verticalmente
            max_value = df[value_col].max()
            ax.set_ylim(0, max_value * 1.2)  # Aumenta apenas 20% acima do maior valor

            # Personalização do gráfico
            ax.set_xlabel("Categorias", fontsize=10, color='white')
            ax.set_ylabel("Valores", fontsize=10, color='white')
            ax.set_title("Distribuição das Tags", fontsize=12, color='white')
            ax.set_xticklabels(df["name"], rotation=45, color='white',fontsize=10,)
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.tick_params(axis='y', colors='white')
            ax.grid(axis="y", linestyle="--", alpha=0.7)

            # Adicionando os valores no topo das barras
            for i, (name, value, percentage) in enumerate(zip(df["name"], df[value_col], df["percentage"])):
                ax.text(i, value + (max_value * 0.05), f"{value} ({percentage:.1f}%)", ha='center', fontsize=10, fontweight='bold', color='black')

            st.pyplot(plt)


    def execute(self):
        st.subheader("📊 AMG - Portal do Cliente - Priortec")
        df = self.getAllDataFromDb()
        self.plot_bar_chart(df)


if __name__ == "__main__":
    loop = AmgDash()
    loop.execute()
