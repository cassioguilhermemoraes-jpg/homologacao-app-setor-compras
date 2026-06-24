import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Teste Supabase", layout="wide")

st.write("URL configurada:", st.secrets["SUPABASE_URL"])

@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_ANON_KEY"].strip()
    return create_client(url, key)

supabase = get_supabase_client()

st.title("Teste de conexão com Supabase")

try:
    res = supabase.table("vw_pedidos_dashboard").select("*").execute()
    df = pd.DataFrame(res.data)

    st.success("Conexão funcionando.")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("Erro ao conectar no Supabase")
    st.exception(e)
