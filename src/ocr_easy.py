# src/ocr_easy.py
import easyocr
import cv2

def extract_license_plate_easy(image_path: str) -> str:
    """
    Estrae il testo (numero di targa) da un'immagine usando EasyOCR.
    
    Parametri:
        image_path (str): Percorso dell'immagine contenente la targa.
    
    Ritorna:
        str: Numero di targa rilevato (stringa vuota se non rilevato).
    """
    # Carica l'immagine
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Immagine non trovata: {image_path}")
    
    # Inizializza il lettore EasyOCR (specifica la lingua, es. "en")
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Esegui il riconoscimento
    results = reader.readtext(image)
    
    # Filtra i risultati in base a criteri: ad esempio, lunghezza, presenza di numeri e lettere
    license_plate = ""
    for (bbox, text, conf) in results:
        # Possiamo applicare un filtro di confidenza, ad esempio conf > 0.5
        if conf > 0.5 and 4 <= len(text.replace(" ", "")) <= 10:
            license_plate = text.strip().upper()
            break
    return license_plate

if __name__ == "__main__":
    # Test: sostituisci 'path/to/test_image.jpg' con il percorso reale dell'immagine
    plate = extract_license_plate_easy("/home/sgtnesk/Laboratorio/tax-enforce/foto/auto.jpg")
    print("Targa rilevata con EasyOCR:", plate)
