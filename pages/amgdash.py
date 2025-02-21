import streamlit as st
from PIL import Image
import requests
from io import BytesIO

# Configuração do modo escuro
st.set_page_config(page_title="Portal AMG", layout="wide")
pagesAcess = st.session_state.get("pagesAcess")
access = pagesAcess[0]
if 'admin' not in access:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
        .e14lo1l1  {
            display: none !important;
        }
        div.block-container {padding-top: 20px !important;}
     
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: block;}
        div.block-container {padding-top: 20px !important;}
     
        }
    </style>
""", unsafe_allow_html=True)

st.write("# 🛠️ Em Desenvolvimento 🛠️")
