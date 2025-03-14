# notifiche.py
import smtplib
from email.mime.text import MIMEText
from verbali import genera_verbale

def invia_notifica(email: str, verbale: dict):
    oggetto = f"Notifica di Verbale Fiscale - {verbale['ID Verbale']}"
    corpo = f"""
Gentile cittadino,

È stato emesso un verbale a suo carico:

- ID Verbale: {verbale['ID Verbale']}
- Targa Veicolo: {verbale['Targa Veicolo']}
- Motivo: {verbale['Motivo']}
- Importo: {verbale['Importo']}
- Stato: {verbale['Stato']}

La invitiamo a effettuare il pagamento entro 30 giorni.
"""
    msg = MIMEText(corpo)
    msg['Subject'] = oggetto
    msg['From'] = "noreply@tuo-dominio.com"
    msg['To'] = email

    # Simulazione invio email:
    print(f"📨 Notifica inviata a {email} per il verbale {verbale['ID Verbale']}")
    
    # Per inviare realmente l'email, configura il server SMTP:
    # with smtplib.SMTP('smtp.tuo-dominio.com', 587) as server:
    #     server.starttls()
    #     server.login("username", "password")
    #     server.send_message(msg)

if __name__ == "__main__":
    test_verbale = genera_verbale("RSSMRA85M01H501Z", "AB123CD", 150, "Mancato pagamento tassa circolazione")
    invia_notifica("cittadino@example.com", test_verbale)
