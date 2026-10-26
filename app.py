import hashlib
import os
import sqlite3
import streamlit as st
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Logick", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stApp {background-color: #f8fafc;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    .stButton>button {border-radius: 5px; font-weight: 500;}
    </style>
""", unsafe_allow_html=True)

# --- GESTION DE LA BASE DE DONNÉES ---
DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "logick.db")

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users 
            (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, full_name TEXT, role TEXT DEFAULT 'admin')""")
        conn.execute("""CREATE TABLE IF NOT EXISTS products 
            (id INTEGER PRIMARY KEY, user_id TEXT, code TEXT, name TEXT, buy_price REAL, sell_price REAL, stock_qty REAL, min_qty REAL DEFAULT 5)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS transactions 
            (id INTEGER PRIMARY KEY, user_id TEXT, type TEXT, description TEXT, amount REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

init_db()

# --- INITIALISATION SESSION ---
if "user" not in st.session_state: st.session_state.user = None

# --- FONCTIONS D'AUTH ---
def login_user(username, password):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and user["password_hash"] == hash_password(password):
            st.session_state.user = dict(user)
            return True
    return False

# --- INTERFACE PRINCIPALE ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Authentification")
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            if login_user(username, password):
                st.rerun()
            else:
                st.error("Identifiants incorrects")
else:
    # Sidebar Navigation
    with st.sidebar:
        st.title("Logick")
        st.write(f"Utilisateur: {st.session_state.user['full_name']}")
        menu = ["Tableau de bord", "Facture / Vente", "Réception / Achat", "Stock et logistique", "Recettes / Dépenses"]
        choice = st.radio("Navigation", menu)
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.rerun()

    # Logique des vues
    if choice == "Tableau de bord":
        st.header("Tableau de bord")
        with get_db() as conn:
            stats = conn.execute("SELECT SUM(amount) as ca FROM transactions WHERE type='vente'").fetchone()
            st.metric("Chiffre d'Affaires Total", f"{stats['ca'] or 0:,.0f} FCFA")
            
    elif choice == "Stock et logistique":
        st.header("Gestion du Stock")
        with st.expander("Ajouter un article"):
            with st.form("add_product"):
                name = st.text_input("Nom du produit")
                buy = st.number_input("Prix Achat")
                sell = st.number_input("Prix Vente")
                qty = st.number_input("Quantité initiale")
                if st.form_submit_button("Enregistrer"):
                    with get_db() as conn:
                        conn.execute("INSERT INTO products (user_id, name, buy_price, sell_price, stock_qty) VALUES (?,?,?,?,?)",
                                     (st.session_state.user['username'], name, buy, sell, qty))
                        st.success("Produit ajouté")

        with get_db() as conn:
            data = conn.execute("SELECT * FROM products WHERE user_id = ?", (st.session_state.user['username'],)).fetchall()
            st.table([dict(d) for d in data])

    elif choice == "Facture / Vente":
        st.header("Enregistrer une vente")
        # Logique simplifiée pour l'exemple
        st.info("Module de vente actif.")
