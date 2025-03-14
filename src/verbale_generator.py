# src/verbale_generator.py
def generate_verbale(license_plate, violation_details, timestamp, location):
    """
    Genera un verbale formale basato sui dati forniti.
    
    Parametri:
      license_plate (str): Targa del veicolo.
      violation_details (str): Dettagli dell'infrazione (es. "passaggio con il rosso").
      timestamp (str): Data e ora dell'infrazione.
      location (str): Posizione dell'infrazione.
      
    Ritorna:
      str: Testo formale del verbale.
    """
    verbale = (
        f"Verbale di Infrazione\n"
        f"Data e Ora: {timestamp}\n"
        f"Posizione: {location}\n"
        f"Veicolo con Targa: {license_plate}\n"
        f"Infrazione: {violation_details}\n\n"
        "Il cittadino è invitato a regolarizzare la propria posizione entro 30 giorni.\n"
        "Questo verbale è emesso in conformità alle normative vigenti."
    )
    return verbale

if __name__ == "__main__":
    # Test rapido del modulo
    test_verbale = generate_verbale("AB123CD", "Passaggio col rosso", "2025-02-13 10:30:00", "Intersezione Via Roma, Milano")
    print(test_verbale)
