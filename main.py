import streamlit as st
import pandas as pd
import psycopg2
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
            'IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO'
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
            df.loc[df["name"] == "IMND_ROBO03_AUTORIZACAO_ULTIMO_REGISTRO",
                   "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO04_AUTORIZACAO_ULTIMO_REGISTRO",
                   "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO05_AUTORIZACAO_ULTIMO_REGISTRO",
                   "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO06_AUTORIZACAO_ULTIMO_REGISTRO",
                   "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO07_AUTORIZACAO_ULTIMO_REGISTRO",
                   "string_value"].values[0],
            df.loc[df["name"] == "IMND_ROBO08_AUTORIZACAO_ULTIMO_REGISTRO",
                   "string_value"].values[0],
        ],
    }

    # Criação do DataFrame
    status_df = pd.DataFrame(data)

    # Calcula o status com base na data atual
    current_time = datetime.now(timezone('America/Sao_Paulo')).replace(tzinfo=None)
    # Converte string para datetime antes de aplicar a lógica
    status_df['datetime_value'] = pd.to_datetime(
        status_df['ÚLTIMA AUTORIZAÇÃO'],
        format='%d/%m/%Y %H:%M'
    )

    # Aplica a lógica para definir o STATUS
    status_df['STATUS'] = status_df['datetime_value'].apply(
        lambda x: 'ATIVO' if current_time -
        x <= timedelta(hours=1) else 'INATIVO'
    )

    # Remove a coluna datetime_value antes da exibição
    status_df = status_df[['COMPUTADOR', 'STATUS', 'ÚLTIMA AUTORIZAÇÃO']]

    # Exibição da tabela
    st.table(status_df.style.applymap(
        lambda x: "background-color: #dff0d8;" if x == "ATIVO"
        else "background-color: #f2dede;", subset=["STATUS"]
    ))


def main():
    # Configuração da página
    st.set_page_config(page_title="Portal do Cliente", layout="wide")

    # Título do dashboard
    st.title("IMND - Portal do Cliente")

    # Obter dados do banco de dados
    try:
        df = get_all_data_from_db()
        show_status_table(df)

    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")


if __name__ == "__main__":
    main()
