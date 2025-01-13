import streamlit as st
import pandas as pd


def main():
    # Configuração da página
    st.set_page_config(page_title="Portal do Cliente", layout="wide")

    # Título do dashboard
    st.title("IMND - Portal do Cliente ")

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
        "STATUS": [
            "Ativo",
            "Inativo",
            "Ativo",
            "Inativo",
            "Ativo",
            "Ativo",
        ],
        "Última Autorização": [
            "08/01/2025 13:00",
            "08/01/2025 08:00",
            "08/01/2025 13:20",
            "01/01/2025 09:15",
            "08/01/2025 14:01",
            "08/01/2025 14:05",
        ],
    }

    # Criação do DataFrame
    df = pd.DataFrame(data)

    # Exibição da tabela
    st.table(df.style.applymap(lambda x: "background-color: #dff0d8;" if x ==
             "Ativo" else "background-color: #f2dede;", subset=["STATUS"]))


if __name__ == "__main__":
    main()
