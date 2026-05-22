"""Modulo de machine learning: modelo, retreinamento, datasets."""

CLASSES = ["PET", "PEAD", "papel", "metal", "organico", "rejeito"]

# Cores BGR distintas por classe (usadas no dashboard).
CORES_CLASSES = {
    "PET":      (255, 200,   0),  # azul claro
    "PEAD":     (  0, 200, 255),  # amarelo
    "papel":    (  0, 165, 255),  # laranja
    "metal":    (200, 200, 200),  # cinza
    "organico": (  0, 200,   0),  # verde
    "rejeito":  (  0,   0, 255),  # vermelho
}

# Icones (texto curto) para nao depender so da cor.
ICONES_CLASSES = {
    "PET":      "[PET]",
    "PEAD":     "[HDPE]",
    "papel":    "[PAP]",
    "metal":    "[MET]",
    "organico": "[ORG]",
    "rejeito":  "[REJ]",
}
