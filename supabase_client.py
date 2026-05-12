import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing.")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)