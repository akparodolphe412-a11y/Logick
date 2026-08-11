timport hashlib
import os
import sqlite3
import streamlit as st
import base64
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Logick - ERP Dépôt", layout="wide", initial_sidebar_state="expanded"
)

# --- GESTION DE LA BASE DE DONNÉES ---
DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "logick.db")
if not os.path.isdir(DB_DIR): os.makedirs(DB_DIR, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'admin',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                code TEXT,
                name TEXT NOT NULL,
                buy_price REAL DEFAULT 0,
                sell_price REAL DEFAULT 0,
                stock_qty REAL DEFAULT 0,
                min_qty REAL DEFAULT 5
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL, -- 'vente', 'achat', 'recette', 'depense', 'retour', 'perte'
                description TEXT,
                amount REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()

init_db()

# --- GESTION DE LA SESSION ---
if "user" not in st.session_state: st.session_state.user = None
if "auth_mode" not in st.session_state: st.session_state.auth_mode = "login"
if "active_tab" not in st.session_state: st.session_state.active_tab = "Tableau de bord"

def validate_password(password: str) -> str:
    if len(password) < 8: return "Au moins 8 caractères."
    if not re.search(r"[A-Z]", password): return "Au moins une majuscule."
    if not re.search(r"[a-z]", password): return "Au moins une minuscule."
    if not re.search(r"[0-9]", password): return "Au moins un chiffre."
    if not re.search(r"[@#&¢~^∆§=.,']", password): return "Au moins un caractère spécial."
    return None

def login_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row and row["password_hash"] == hash_password(password):
        st.session_state.user = {
            "username": row["username"], "full_name": row["full_name"], "role": row["role"]
        }
        return True
    return False

def logout_user():
    st.session_state.user = None
    st.session_state.active_tab = "Tableau de bord"

# --- APPLICATION ---

if not st.session_state.user:
    # --- AUTHENTIFICATION ---
    _, col_m, _ = st.columns([1, 0.8, 1])
    with col_m:
        st.markdown("<h2 style='text-align: center; color: #0F172A;'>Connexion Logick</h2>", unsafe_allow_html=True)
        
        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                username = st.text_input("Identifiant")
                password = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter"):
                    if login_user(username, password):
                        st.rerun()
                    else:
                        st.error("Identifiant ou mot de passe incorrect.")
            if st.button("Créer un espace"):
                st.session_state.auth_mode = "register"
                st.rerun()

        elif st.session_state.auth_mode == "register":
            with st.form("register_form"):
                reg_name = st.text_input("Nom complet")
                reg_email = st.text_input("Identifiant / Gmail")
                reg_pass = st.text_input("Mot de passe", type="password")
                reg_confirm = st.text_input("Confirmer le mot de passe", type="password")
                if st.form_submit_button("S'inscrire"):
                    if reg_pass != reg_confirm:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        err = validate_password(reg_pass)
                        if err:
                            st.error(err)
                        else:
                            try:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("INSERT INTO users (username, full_name, password_hash) VALUES (?, ?, ?)",
                                            (reg_email, reg_name, hash_password(reg_pass)))
                                conn.commit()
                                conn.close()
                                st.session_state.user = {"username": reg_email, "full_name": reg_name, "role": "admin"}
                                st.success("Espace créé avec succès !")
                                st.rerun()
                            except Exception:
                                st.error("Cet identifiant existe déjà.")
            if st.button("Retour"):
                st.session_state.auth_mode = "login"
                st.rerun()

else:
    # --- INTERFACE PRINCIPALE TYPE LOGICIEL DÉPÔT ---
    
    st.sidebar.title("📦 Logick ERP")
    st.sidebar.write(f"Espace : **{st.session_state.user['full_name']}**")
    st.sidebar.markdown("---")
    
    # Menu latéral structuré
    menu_choice = st.sidebar.radio("Navigation", [
        "Tableau de bord",
        "Facture / Vente",
        "Réception / Achat",
        "Retours (Client / Fournisseur)",
        "Recettes / Dépenses",
        "Pertes / Emballages",
        "Stock et logistique",
        "Créances et dettes",
        "Comptabilité",
        "Trésorerie",
        "RH et paie",
        "Fiscalité",
        "Paramètres / Archives"
    ])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔴 Se déconnecter"):
        logout_user()
        st.rerun()

    # --- BARRE D'ACTIONS RAPIDES SUPÉRIEURE ---
    st.markdown("### ⚡ Accès Rapide Dépôt")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        if st.button("📄 Facture / Vente", use_container_width=True):
            st.session_state.active_tab = "Facture / Vente"
    with c2:
        if st.button("📦 Réception / Achat", use_container_width=True):
            st.session_state.active_tab = "Réception / Achat"
    with c3:
        if st.button("🔄 Retours", use_container_width=True):
            st.session_state.active_tab = "Retours (Client / Fournisseur)"
    with c4:
        if st.button("💵 Recettes / Dépenses", use_container_width=True):
            st.session_state.active_tab = "Recettes / Dépenses"
    with c5:
        if st.button("⚠️ Pertes / Emballages", use_container_width=True):
            st.session_state.active_tab = "Pertes / Emballages"
    with c6:
        if st.button("📊 Tableau de bord", use_container_width=True):
            st.session_state.active_tab = "Tableau de bord"

    st.markdown("---")

    # Synchronisation menu / boutons rapides
    if st.session_state.active_tab in [
        "Facture / Vente", "Réception / Achat", "Retours (Client / Fournisseur)", 
        "Recettes / Dépenses", "Pertes / Emballages", "Tableau de bord"
    ] and menu_choice == "Tableau de bord":
        current_view = st.session_state.active_tab
    else:
        current_view = menu_choice

    user_id = st.session_state.user['username']
    conn = get_db_connection()

    # --- 1. TABLEAU DE BORD (PILOTAGE ACTIF) ---
    if current_view == "Tableau de bord":
        st.title("📈 Tableau de Bord & Pilotage")
        
        cur = conn.cursor()
        # Calculs stock
        cur.execute("SELECT COUNT(*) as total, SUM(stock_qty * sell_price) as val_stock FROM products WHERE user_id = ?", (user_id,))
        res_stock = cur.fetchone()
        
        # Calculs ventes
        cur.execute("SELECT SUM(amount) as total_ventes FROM transactions WHERE user_id = ? AND type = 'vente'", (user_id,))
        res_ventes = cur.fetchone()

        # Calculs caisse (Recettes + Ventes - Dépenses - Achats cash)
        cur.execute("SELECT SUM(amount) as recettes FROM transactions WHERE user_id = ? AND type IN ('vente', 'recette')", (user_id,))
        res_rec = cur.fetchone()
        cur.execute("SELECT SUM(amount) as depenses FROM transactions WHERE user_id = ? AND type IN ('depense', 'achat')", (user_id,))
        res_dep = cur.fetchone()
        
        solde_caisse = (res_rec["recettes"] or 0) - (res_dep["depenses"] or 0)

        # Affichage des métriques clés en haut
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Chiffre d'Affaires Ventes", f"{res_ventes['total_ventes'] or 0:,.0f} FCFA")
        col_m2.metric("Solde Caisse Estimé", f"{solde_caisse:,.0f} FCFA")
        col_m3.metric("Valeur Totale Stock", f"{res_stock['val_stock'] or 0:,.0f} FCFA")
        col_m4.metric("Références Articles", res_stock["total"] or 0)

        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("⚠️ Alertes Rupture de Stock")
            cur.execute("SELECT name AS Article, stock_qty AS Stock FROM products WHERE user_id = ? AND stock_qty <= min_qty", (user_id,))
            low_stock = cur.fetchall()
            if low_stock:
                st.dataframe([dict(x) for x in low_stock], use_container_width=True)
            else:
                st.success("Aucun article en alerte de rupture de stock.")

        with col_g2:
            st.subheader("🕒 Derniers Mouvements")
            cur.execute("SELECT type AS Type, description AS Description, amount AS Montant, created_at AS Date FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
            mouvements = cur.fetchall()
            if mouvements:
                st.dataframe([dict(m) for m in mouvements], use_container_width=True)
            else:
                st.info("Aucun mouvement récent enregistré.")

    # --- 2. FACTURE / VENTE ---
    elif current_view == "Facture / Vente":
        st.title("📄 Facture / Vente")
        st.write("Enregistrer une sortie de marchandises et éditer la facture du client.")
        
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE user_id = ?", (user_id,))
        prods = cur.fetchall()
        if not prods:
            st.warning("Veuillez d'abord enregistrer des produits dans le module 'Stock et logistique'.")
        else:
            p_dict = {p["name"]: p for p in prods}
            chosen = st.selectbox("Choisir l'article", list(p_dict.keys()))
            qty = st.number_input("Quantité vendue", min_value=1.0, value=1.0)
            
            selected_item = p_dict[chosen]
            total_amt = selected_item["sell_price"] * qty
            st.markdown(f"**Prix unitaire :** {selected_item['sell_price']:,.0f} FCFA | **Total à payer :** `{total_amt:,.0f} FCFA`")
            
            if st.button("Valider la Vente et Éditer la Facture"):
                if selected_item["stock_qty"] < qty:
                    st.error("Stock insuffisant pour honorer cette vente !")
                else:
                    new_q = selected_item["stock_qty"] - qty
                    cur.execute("UPDATE products SET stock_qty = ? WHERE id = ?", (new_q, selected_item["id"]))
                    cur.execute("INSERT INTO transactions (user_id, type, description, amount) VALUES (?, ?, ?, ?)",
                                (user_id, "vente", f"Facture vente: {qty}x {chosen}", total_amt))
                    conn.commit()
                    st.success("Vente enregistrée avec succès ! Stock mis à jour.")
                    st.rerun()

    # --- 3. RÉCEPTION / ACHAT ---
    elif current_view == "Réception / Achat":
        st.title("📦 Réception / Achat")
        st.write("Enregistrer l'entrée de nouveaux produits reçus des fournisseurs.")
        
        with st.form("reception_form"):
            r_name = st.text_input("Nom de l'article / Produit reçu")
            r_qty = st.number_input("Quantité reçue", min_value=1.0, value=1.0)
            r_buy = st.number_input("Prix d'achat unitaire (FCFA)", min_value=0.0)
            r_sell = st.number_input("Prix de vente unitaire (FCFA)", min_value=0.0)
            
            if st.form_submit_button("Enregistrer la Réception"):
                if r_name:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM products WHERE user_id = ? AND name = ?", (user_id, r_name))
                    existing = cur.fetchone()
                    if existing:
                        new_qty = existing["stock_qty"] + r_qty
                        cur.execute("UPDATE products SET stock_qty = ?, buy_price = ?, sell_price = ? WHERE id = ?",
                                    (new_qty, r_buy, r_sell, existing["id"]))
                    else:
                        cur.execute("INSERT INTO products (user_id, name, buy_price, sell_price, stock_qty) VALUES (?, ?, ?, ?, ?)",
                                    (user_id, r_name, r_buy, r_sell, r_qty))
                    
                    cur.execute("INSERT INTO transactions (user_id, type, description, amount) VALUES (?, ?, ?, ?)",
                                (user_id, "achat", f"Réception fournisseur: {r_qty}x {r_name}", r_buy * r_qty))
                    conn.commit()
                    st.success("Réception de stock enregistrée avec succès !")
                    st.rerun()

    # --- 4. RETOURS (CLIENT / FOURNISSEUR) ---
    elif current_view == "Retours (Client / Fournisseur)":
        st.title("🔄 Retours (Client / Fournisseur)")
        st.write("Pour gérer les marchandises qu'on te ramène ou que tu renvoies.")
        
        with st.form("retour_form"):
            r_type = st.selectbox("Type de retour", ["Retour Client (Remet en stock)", "Retour Fournisseur (Sortie de stock)"])
            r_desc = st.text_input("Motif du retour & Article concerné")
            r_amt = st.number_input("Montant ou valeur estimée (FCFA)", min_value=0.0)
            
            if st.form_submit_button("Enregistrer le Retour"):
                if r_desc:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO transactions (user_id, type, description, amount) VALUES (?, ?, ?, ?)",
                                (user_id, "retour", f"{r_type}: {r_desc}", r_amt))
                    conn.commit()
                    st.success("Retour enregistré avec succès !")
                    st.rerun()

    # --- 5. RECETTES / DÉPENSES ---
    elif current_view == "Recettes / Dépenses":
        st.title("💵 Recettes / Dépenses")
        st.write("Pour suivre l'argent qui entre et qui sort de la caisse au jour le jour.")
        
        t_type = st.selectbox("Type d'opération de caisse", ["Recette (Entrée d'argent)", "Dépense (Sortie d'argent)"])
        t_desc = st.text_input("Motif / Description")
        t_amt = st.number_input("Montant (FCFA)", min_value=0.0)
        
        if st.button("Enregistrer dans la Caisse"):
            if t_desc and t_amt > 0:
                op_type = "recette" if "Recette" in t_type else "depense"
                cur = conn.cursor()
                cur.execute("INSERT INTO transactions (user_id, type, description, amount) VALUES (?, ?, ?, ?)",
                            (user_id, op_type, t_desc, t_amt))
                conn.commit()
                st.success("Opération de caisse enregistrée avec succès !")
                st.rerun()

    # --- 6. PERTES / EMBALLAGES ---
    elif current_view == "Pertes / Emballages":
        st.title("⚠️ Pertes / Emballages")
        st.write("Pour suivre la casse, les produits périmés ou la gestion des consignes.")
        
        with st.form("perte_form"):
            p_desc = st.text_input("Description de la perte ou avarie (ex: Casse bouteilles, périmé)")
            p_amt = st.number_input("Valeur de la perte (FCFA)", min_value=0.0)
            
            if st.form_submit_button("Enregistrer la Perte"):
                if p_desc:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO transactions (user_id, type, description, amount) VALUES (?, ?, ?, ?)",
                                (user_id, "perte", f"Pertes/Casse: {p_desc}", p_amt))
                    conn.commit()
                    st.success("Déclaration de perte enregistrée.")
                    st.rerun()

    # --- 7. STOCK ET LOGISTIQUE ---
    elif current_view == "Stock et logistique":
        st.title("📋 Stock et Logistique")
        
        with st.expander("➕ Ajouter un nouvel article en stock"):
            with st.form("add_p"):
                name = st.text_input("Désignation du produit")
                code = st.text_input("Code article")
                c1, c2, c3 = st.columns(3)
                b_price = c1.number_input("Prix d'achat", min_value=0.0)
                s_price = c2.number_input("Prix de vente", min_value=0.0)
                init_q = c3.number_input("Quantité initiale", min_value=0.0)
                
                if st.form_submit_button("Enregistrer"):
                    if name:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO products (user_id, code, name, buy_price, sell_price, stock_qty) VALUES (?, ?, ?, ?, ?, ?)",
                                    (user_id, code, name, b_price, s_price, init_q))
                        conn.commit()
                        st.success("Article enregistré !")
                        st.rerun()

        cur = conn.cursor()
        cur.execute("SELECT code AS Code, name AS Article, buy_price AS 'P. Achat', sell_price AS 'P. Vente', stock_qty AS 'Stock Actuel' FROM products WHERE user_id = ?", (user_id,))
        data = cur.fetchall()
        if data:
            st.dataframe([dict(d) for d in data], use_container_width=True)
        else:
            st.info("Aucun produit enregistré.")

    # --- 8. CRÉANCES ET DETTES ---
    elif current_view == "Créances et dettes":
        st.title("🤝 Gestion des Créances et Dettes")
        st.info("Suivi des comptes clients (crédits en cours) et fournisseurs.")

    # --- 9. COMPTABILITÉ ---
    elif current_view == "Comptabilité":
        st.title("📊 Comptabilité")
        st.tabs(["Journal comptable", "Plan des comptes", "Bilan", "Compte de résultat", "S-SEF (télédéclaration)"])
        st.info("Modules comptables et états financiers réglementaires.")

    # --- 10. TRÉSORERIE ---
    elif current_view == "Trésorerie":
        st.title("💰 Trésorerie")
        st.info("Suivi des comptes bancaires, rapprochements et liquidités globales.")

    # --- 11. RH ET PAIE ---
    elif current_view == "RH et paie":
        st.title("👥 Ressources Humaines et Paie")
        st.info("Gestion des employés, bulletins de paie, congés et absences.")

    # --- 12. FISCALITÉ ---
    elif current_view == "Fiscalité":
        st.title("📑 Fiscalité")
        st.info("Déclarations et suivi fiscal.")

    # --- 13. PARAMÈTRES / ARCHIVES ---
    elif current_view == "Paramètres / Archives":
        st.title("⚙️ Paramètres et Archives")
        st.info("Conservation des documents, exports et gestion des exercices.")

    conn.close()
    st.markdown("""
<style>
    /* Cache le bouton Deploy en haut à droite */
    .stAppDeployButton {
        display: none;
    }
</style>
""", unsafe_allow_html=True)
import streamlit as st

# Cette configuration force la disparition des éléments de menu de Streamlit
hide_streamlit_style = """
    <style>
    /* Masque le bouton Fork et le logo GitHub */
    div[data-testid="stToolbar"] {
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
    }
    /* Masque le menu principal et le footer */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)