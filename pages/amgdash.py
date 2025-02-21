import streamlit as st
from PIL import Image
import requests
from io import BytesIO

# Configuração do modo escuro
st.set_page_config(page_title="Portal AMG", layout="wide")
pagesAcess = st.session_state.get("pagesAcess")
access = pagesAcess[0]
st.markdown("""
    <style>
        div.block-container {padding-top: 16px !important;}
        }
    </style>
    """, unsafe_allow_html=True)

if 'admin' not in access:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
        .e14lo1l1  {display: none !important;}
        }
    </style>
    """, unsafe_allow_html=True)

st.write("# 🛠️ Em Desenvolvimento 🛠️")
