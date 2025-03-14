# tests/test_ai_analysis.py
import pandas as pd
from src.ai_analysis import analyze_verbali

def test_analyze_verbali():
    data = {
        "ID Verbale": ["VBL-1", "VBL-2", "VBL-3"],
        "Importo": ["100 EUR", "500 EUR", "1000 EUR"]
    }
    df = pd.DataFrame(data)
    df_result = analyze_verbali(df)
    # Verifica che le colonne aggiuntive siano state create
    assert "Importo_Num" in df_result.columns
    assert "Anomaly_Label" in df_result.columns
