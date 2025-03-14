# generazione_verbali.py
from verbali import genera_verbale
import pandas as pd

if __name__ == "__main__":
    verbali = [
        genera_verbale("RSSMRA85M01H501Z", "AB123CD", 150, "Mancato pagamento tassa circolazione"),
        genera_verbale("VRDLNZ99L11F205T", "DE456FG", 200, "Eccesso di velocità"),
        genera_verbale("BNCLRA78P12B819X", "GH789IJ", 300, "Parcheggio non autorizzato"),
        genera_verbale("PLMNST95C22D548K", "KL012MN", 500, "Mancato pagamento bollo auto"),
        genera_verbale("FRTMRC91H08G123R", "OP345QR", 1000, "Assicurazione scaduta")
    ]
    
    df_verbali = pd.DataFrame(verbali)
    print(df_verbali)
