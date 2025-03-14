# src/photo_processor.py
import os
import shutil
import datetime
import cv2
import logging
import easyocr

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_license_plate(image):
    """
    Estrae la targa da un'immagine (array NumPy) utilizzando EasyOCR.
    """
    # Inizializza il lettore EasyOCR (senza GPU)
    reader = easyocr.Reader(['en'], gpu=False)

    # Esegui il riconoscimento
    results = reader.readtext(image)  # image è già un array NumPy caricato da cv2

    # Seleziona il risultato con confidenza alta che assomigli a una targa
    license_plate = ""
    for (bbox, text, conf) in results:
        # Ad esempio, se conf > 0.5 e la lunghezza del testo filtrato è tra 4 e 10
        if conf > 0.5 and 4 <= len(text.replace(" ", "")) <= 10:
            license_plate = text.strip().upper()
            break

    return license_plate

def archive_image(image_path, license_plate, archive_base_dir="archive"):
    """
    Archivia l'immagine in una struttura organizzata per targa e data.
    """
    if not license_plate:
        license_plate = "unknown"
    
    folder = os.path.join(archive_base_dir, license_plate)
    os.makedirs(folder, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}.jpg"
    archive_path = os.path.join(folder, file_name)
    
    shutil.copy(image_path, archive_path)
    logging.info(f"Immagine archiviata in: {archive_path}")
    return archive_path

def process_photo(image_path):
    """
    Processa una foto: legge l'immagine, estrae la targa con EasyOCR, archivia la foto.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Immagine non trovata: {image_path}")
        
        license_plate = extract_license_plate(image)
        logging.info(f"Targa rilevata: {license_plate}")
        
        archive_path = archive_image(image_path, license_plate)
        
        # Qui possiamo in futuro attivare altri processi, come la generazione del verbale
        return license_plate, archive_path
    except Exception as e:
        logging.error(f"Errore nel processare l'immagine {image_path}: {e}")
        return None, None

if __name__ == "__main__":
    # Test: sostituisci con il percorso reale di una foto di prova
    lp, archived = process_photo("/home/sgtnesk/Laboratorio/tax-enforce/foto/auto.jpg")
    print(f"Targa: {lp}, Immagine archiviata in: {archived}")
