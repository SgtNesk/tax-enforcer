# src/simulate.py
from db import SessionLocal, init_db, Verbale
from verbali import genera_verbale
import datetime

def simulate():
    # Inizializza il database (crea le tabelle, se non esistono)
    init_db()
    
    # Crea una sessione per interagire con il DB
    session = SessionLocal()
    
    # Genera due verbali di prova
    v1 = genera_verbale("RSSMRA85M01H501Z", "AB123CD", 150, "Mancato pagamento tassa circolazione")
    v2 = genera_verbale("VRDLNZ99L11F205T", "DE456FG", 200, "Eccesso di velocità")
    
    # Estrai il valore numerico dall'importo (rimuovendo "EUR")
    v1_importo = float(v1["Importo"].split()[0])
    v2_importo = float(v2["Importo"].split()[0])
    
    # Crea istanze del modello Verbale
    verbale1 = Verbale(
        verbale_id=v1["ID Verbale"],
        codice_fiscale=v1["Codice Fiscale"],
        targa=v1["Targa Veicolo"],
        importo=v1_importo,
        motivo=v1["Motivo"],
        stato=v1["Stato"],
        data_emissione=datetime.datetime.strptime(v1["Data Emissione"], "%Y-%m-%d %H:%M:%S")
    )
    
    verbale2 = Verbale(
        verbale_id=v2["ID Verbale"],
        codice_fiscale=v2["Codice Fiscale"],
        targa=v2["Targa Veicolo"],
        importo=v2_importo,
        motivo=v2["Motivo"],
        stato=v2["Stato"],
        data_emissione=datetime.datetime.strptime(v2["Data Emissione"], "%Y-%m-%d %H:%M:%S")
    )
    
    # Salva i verbali nel database
    session.add(verbale1)
    session.add(verbale2)
    session.commit()
    
    # Recupera e stampa tutti i verbali presenti
    verbali = session.query(Verbale).all()
    for v in verbali:
        print(f"{v.verbale_id}: {v.codice_fiscale}, {v.targa}, {v.importo} EUR, {v.motivo}, {v.stato}, {v.data_emissione}")
    
    session.close()

if __name__ == "__main__":
    simulate()
