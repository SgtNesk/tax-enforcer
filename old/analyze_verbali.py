# ai_analysis.py
"""
Modulo di Analisi AI per i verbali fiscali.
Utilizzeremo l'algoritmo Isolation Forest per individuare anomalie nei dati degli importi.
"""

import pandas as pd
from sklearn.ensemble import IsolationForest

def analyze_verbali(df: pd.DataFrame) -> pd.DataFrame:
    """
    Esegue l'analisi dei verbali fiscali per identificare anomalie (es. importi sospetti).

    Parametri:
        df (pd.DataFrame): DataFrame contenente i verbali, con una colonna "Importo"
                           espressa come stringa (es. "150 EUR").

    Ritorna:
        pd.DataFrame: DataFrame con due colonne aggiuntive:
            - "Importo_Num": importo convertito in valore numerico
            - "Anomaly_Label": etichetta ("Anomalo" o "Normale") basata sull'algoritmo
    """
    # Estrai il valore numerico dalla colonna "Importo"
    df['Importo_Num'] = df['Importo'].str.extract(r'(\d+\.?\d*)').astype(float)
    
    # Inizializza e addestra il modello Isolation Forest
    model = IsolationForest(contamination=0.1, random_state=42)
    df['Anomaly'] = model.fit_predict(df[['Importo_Num']])
    
    # Interpretiamo il risultato: -1 indica un'anomalia, 1 indica un valore normale
    df['Anomaly_Label'] = df['Anomaly'].apply(lambda x: 'Anomalo' if x == -1 else 'Normale')
    
    return df

if __name__ == "__main__":
    # Test rapido del modulo
    data = {
        "ID Verbale": ["VBL-123456", "VBL-789012", "VBL-345678"],
        "Importo": ["150 EUR", "200 EUR", "1000 EUR"]
    }
    df_test = pd.DataFrame(data)
    df_result = analyze_verbali(df_test)
    print(df_result)
