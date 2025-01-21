import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pytz import timezone

def get_all_data_from_db():
    # Configurações de conexão ao banco de dados
    conn = psycopg2.connect(
        host="roundhouse.proxy.rlwy.net",
        database="railway",
        user="postgres",  # Substitua pelo usuário correto
        password="XWhTqAztzzYuAqvUcgWCUJUJmnEJliDK",  # Substitua pela senha correta
        port=28938
    )

    # Consulta ao banco de dados para obter os valores das tags desejadas
    query = """
        SELECT
            name,
            string_value,
            int_value,
            double_value,
            registration_date
        FROM
            tag_value,
            tag
        WHERE
            tag_value.tag_id = tag.id AND
            tag.name IN (
                'IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO',
                'IMND_ROBO04_AUTORIZACAO_ULTIMO_REGISTRO',
                'IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO',
                'IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO',
                'IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO',
                'IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO',
                'IMND_MES_ATUAL_REALIZADOS_APROVADOS',
                'IMND_MES_ATUAL_REALIZADOS_NAO_APROVADOS',
                'IMND_MES_ATUAL_PENDENTES',
                'IMND_MES_ATUAL_APROVADOS'
            )
    """

    # Executa a consulta e retorna os dados
    df = pd.read_sql_query(query, conn)

    # Fecha a conexão
    conn.close()

    return df

def show_status_table(df):
    # Dados da tabela
    data = {
        "COMPUTADOR": [
            "IMND_ROBO3",
            "IMND_ROBO4",
            "IMND_ROBO5",
            "IMND_ROBO6",
            "IMND_ROBO7",
            "IMND_ROBO8",
        ],
        "ÚLTIMA AUTORIZAÇÃO": [
            df.loc[df["name"] == "IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO04_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO", "string_value"].values[0],
        ],
    }

    # Criação do DataFrame
    status_df = pd.DataFrame(data)

    # Calcula o status com base na data atual
    current_time = datetime.now(timezone('America/Sao_Paulo')).replace(tzinfo=None)
    status_df['datetime_value'] = pd.to_datetime(status_df['ÚLTIMA AUTORIZAÇÃO'], format='%d/%m/%Y %H:%M:%S')

    # Aplica a lógica para definir o STATUS
    status_df['STATUS'] = status_df['datetime_value'].apply(
        lambda x: 'ATIVO' if current_time - x <= timedelta(hours=1) else 'INATIVO'
    )

    # Remove a coluna datetime_value antes da exibição
    status_df = status_df[['COMPUTADOR', 'STATUS', 'ÚLTIMA AUTORIZAÇÃO']]

    return status_df

def show_pie_chart(df):
    # Obter valores das tags do banco de dados
    #realizados_aprovados = df.loc[df["name"] == "IMND_MES_ATUAL_REALIZADOS_APROVADOS", "int_value"].values
    #realizados_nao_aprovados = df.loc[df["name"] == "IMND_MES_ATUAL_REALIZADOS_NAO_APROVADOS", "int_value"].values
    aprovados = df.loc[df["name"] == "IMND_MES_ATUAL_APROVADOS", "int_value"].values
    pendentes = df.loc[df["name"] == "IMND_MES_ATUAL_PENDENTES", "int_value"].values

    # Verificar se os valores foram encontrados no banco
    #realizados_aprovados = realizados_aprovados[0] if len(realizados_aprovados) > 0 else 0
    #realizados_nao_aprovados = realizados_nao_aprovados[0] if len(realizados_nao_aprovados) > 0 else 0
    aprovados = aprovados[0] if len(aprovados) > 0 else 0
    pendentes = pendentes[0] if len(pendentes) > 0 else 0

    # Criar os dados do gráfico
    labels = ["Aprovados", "Pendentes"]
    sizes = [aprovados, pendentes]
    total = sum(sizes)

    if total > 0:
        # Criar gráfico de pizza
        fig, ax = plt.subplots(figsize=(4, 4))  # Definição do tamanho menor do gráfico
        ax.pie(
            sizes,
            labels=[f"{labels[0]}: {sizes[0]} ({sizes[0]/total:.1%})",
                    f"{labels[1]}: {sizes[1]} ({sizes[1]/total:.1%})"],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={"edgecolor": "white"}
        )
        ax.axis('equal')  # Mantém a proporção do gráfico

        return fig, sizes
    else:
        return None, None

def main():
    # Configuração da página
    st.set_page_config(page_title="Portal do Cliente", layout="wide")

    # Título do dashboard
    st.title("IMND - Portal do Cliente")

    # Obter dados do banco de dados
    try:
        df = get_all_data_from_db()
        
        # Criar layout com colunas
        col1, col2 = st.columns([2, 1])  # Define proporção 2:1 para tabela e gráfico

        with col1:
            status_df = show_status_table(df)
            st.table(status_df.style.applymap(
                lambda x: "background-color: #dff0d8;" if x == "ATIVO"
                else "background-color: #f2dede;", subset=["STATUS"]
            ))

        with col2:
            fig, sizes = show_pie_chart(df)
            if fig:
                st.subheader("Aprovação de Consulta")
                st.pyplot(fig)
                #st.write(f"**Aprovados:** {sizes[0]}")
                #st.write(f"**Pendentes:** {sizes[1]}")
            else:
                st.warning("Não há consultas realizadas para exibir o gráfico.")

    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")

if __name__ == "__main__":
    main()
