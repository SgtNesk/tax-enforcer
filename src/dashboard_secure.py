import streamlit as st
import pandas as pd
import hashlib
from ai_analysis import analyze_verbali  # Modulo AI per l'analisi dei verbali

# =========================
# Sezione Autenticazione
# =========================

def hash_password(password: str) -> str:
    """Genera l'hash SHA-256 della password."""
    return hashlib.sha256(password.encode()).hexdigest()

# Database simulato degli utenti (in produzione, usare un database sicuro)
users = {
    "mario.rossi": hash_password("password123"),
    "luigi.verdi": hash_password("secret456")
}

def check_login(username: str, password: str) -> bool:
    """
    Verifica se l'utente esiste e se la password (hashata) corrisponde.
    """
    return username in users and users[username] == hash_password(password)

# Inizializza lo state per gestire la sessione (se non già presente)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''

# Se l'utente non è autenticato, mostra il form di login
if not st.session_state.logged_in:
    st.title("Area Personale del Cittadino - Login")
    st.write("Accedi con le tue credenziali oppure scegli l'accesso SPID (in sviluppo).")
    
    # Form di login tradizionale
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Accedi"):
            if check_login(username_input, password_input):
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success("Login effettuato con successo!")
                st.experimental_rerun()
            else:
                st.error("Credenziali non valide")
    with col2:
        st.markdown("[Accedi con SPID](http://localhost:5000/sso)")
    
    st.stop()  # Blocca l'esecuzione del resto della dashboard se non loggato

# =========================
# Area Personale (Post-Login)
# =========================

st.title("Area Personale del Cittadino")
st.write(f"Benvenuto, **{st.session_state.username}**!")

# -------------------------
# Sezione Visualizzazione Verbali
# -------------------------
# Qui i dati sono statici per ora; in produzione verranno caricati da un database.
verbali = [
    {
        "ID Verbale": "VBL-123456",
        "Codice Fiscale": "RSSMRA85M01H501Z",
        "Targa Veicolo": "AB123CD",
        "Importo": "150 EUR",
        "Motivo": "Mancato pagamento tassa circolazione",
        "Stato": "Non Pagato",
        "Data Emissione": "2025-02-13 10:30:00"
    },
    {
        "ID Verbale": "VBL-789012",
        "Codice Fiscale": "VRDLNZ99L11F205T",
        "Targa Veicolo": "DE456FG",
        "Importo": "200 EUR",
        "Motivo": "Eccesso di velocità",
        "Stato": "Non Pagato",
        "Data Emissione": "2025-02-13 11:00:00"
    }
]
df_verbali = pd.DataFrame(verbali)
st.subheader("I tuoi Verbali Fiscali")
st.dataframe(df_verbali)

# -------------------------
# Sezione Analisi AI dei Verbali
# -------------------------
st.markdown("## Analisi AI dei Verbali")
if st.button("Esegui Analisi AI"):
    # Applichiamo il modulo AI per analizzare gli importi
    df_result = analyze_verbali(df_verbali.copy())
    st.write("Risultato Analisi:")
    st.dataframe(df_result)
else:
    st.info("Clicca sul pulsante per eseguire l'analisi AI dei tuoi verbali.")

# -------------------------
# Sezione Logout
# -------------------------
if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.experimental_rerun()
