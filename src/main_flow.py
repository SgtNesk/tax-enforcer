# src/main_flow.py
import datetime
from photo_processor import process_photo
from verbale_generator import generate_verbale

def main_flow(image_path, violation_details, location):
    # Processa la foto per ottenere la targa e archivia l'immagine
    license_plate, archive_path = process_photo(image_path)
    if not license_plate:
        print("Impossibile estrarre la targa dalla foto.")
        return
    
    # Ottieni il timestamp corrente (oppure usa quello della foto se disponibile)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Genera il verbale basato sui dati raccolti
    verbale = generate_verbale(license_plate, violation_details, timestamp, location)
    
    # Qui possiamo salvare il verbale nel database, inviarlo via email, etc.
    print("Verbale generato:")
    print(verbale)
    # Ad esempio, potremmo archiviare il verbale su file o nel DB

if __name__ == "__main__":
    # Test: Sostituisci il percorso dell'immagine e i dettagli con dati di prova
    image_path = "/home/sgtnesk/Laboratorio/tax-enforce/foto/auto.jpg"
    violation_details = "Passaggio col rosso in prossimità di un incrocio."
    location = "Intersezione Via Roma, Milano"
    main_flow(image_path, violation_details, location)
