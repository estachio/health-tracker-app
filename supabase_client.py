import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    import streamlit as st
    if hasattr(st, "secrets"):
        if "SUPABASE_URL" in st.secrets:
            SUPABASE_URL = st.secrets["SUPABASE_URL"]
        if "SUPABASE_KEY" in st.secrets:
            SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing.")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)