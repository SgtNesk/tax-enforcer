# dashboard.py
import streamlit as st
import pandas as pd

# Dati di esempio (in un sistema reale questi dati verrebbero caricati da un database o API)
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

st.title("🚦 Sistema Fiscale AI-Powered - Dashboard Utenti")

codice_fiscale = st.text_input("Inserisci il tuo Codice Fiscale:")

if codice_fiscale:
    verbali_cittadino = df_verbali[df_verbali["Codice Fiscale"] == codice_fiscale]

    if not verbali_cittadino.empty:
        st.write("📋 **I tuoi verbali:**")
        st.dataframe(verbali_cittadino)

        verbale_selezionato = st.selectbox("Seleziona un verbale", verbali_cittadino["ID Verbale"].values)
        if verbale_selezionato:
            verbale = verbali_cittadino[verbali_cittadino["ID Verbale"] == verbale_selezionato].iloc[0]
            st.write(f"🔹 **Verbale:** {verbale['ID Verbale']}")
            st.write(f"📍 **Motivo:** {verbale['Motivo']}")
            st.write(f"💰 **Importo:** {verbale['Importo']}")
            st.write(f"📅 **Data Emissione:** {verbale['Data Emissione']}")
            st.write(f"⚠️ **Stato:** {verbale['Stato']}")

            if verbale["Stato"] == "Non Pagato":
                if st.button("💳 Paga ora"):
                    df_verbali.loc[df_verbali["ID Verbale"] == verbale_selezionato, "Stato"] = "Pagato"
                    st.success("✅ Pagamento effettuato con successo!")
                    st.experimental_rerun()
    else:
        st.warning("Nessun verbale trovato per il Codice Fiscale inserito.")
