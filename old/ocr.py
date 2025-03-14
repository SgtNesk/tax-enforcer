# src/ocr.py
import cv2
import pytesseract

def extract_license_plate(image_path: str) -> str:
    """
    Estrae il testo (numero di targa) da un'immagine usando OCR.
    
    Parametri:
      image_path (str): Percorso dell'immagine contenente la targa.
    
    Ritorna:
      str: Numero di targa rilevato (stringa vuota se non rilevato).
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Immagine non trovata: {image_path}")
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    config = "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    text = pytesseract.image_to_string(thresh, config=config)
    return text.strip()

if __name__ == "__main__":
    # Test: sostituisci 'path/to/test_image.jpg' con l'immagine di prova
    license_plate = extract_license_plate("/home/sgtnesk/Laboratorio/tax-enforce/foto/auto.jpg")
    print("Targa rilevata:", license_plate)
