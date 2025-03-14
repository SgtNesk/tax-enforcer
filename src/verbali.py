# verbali.py
import random
import pandas as pd

def genera_verbale(codice_fiscale: str, targa: str, importo: float, motivo: str) -> dict:
    verbale_id = f"VBL-{random.randint(100000, 999999)}"
    return {
        "ID Verbale": verbale_id,
        "Codice Fiscale": codice_fiscale,
        "Targa Veicolo": targa,
        "Importo": f"{importo:.2f} EUR",
        "Motivo": motivo,
        "Stato": "Non Pagato",
        "Data Emissione": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
