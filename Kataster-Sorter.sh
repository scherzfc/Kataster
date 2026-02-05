#!/bin/bash
echo ""
echo "========================================"
echo "   Kataster-Sorter wird gestartet..."
echo "========================================"
echo ""

# Ins Skript-Verzeichnis wechseln
cd "$(dirname "$0")"

# Prüfen ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    echo "[FEHLER] Python3 ist nicht installiert!"
    echo "Bitte installiere Python: sudo apt install python3 python3-venv python3-pip"
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

# Prüfen ob venv existiert, sonst erstellen
if [ ! -d "venv" ]; then
    echo "[INFO] Erstelle virtuelle Umgebung..."
    python3 -m venv venv
    echo "[INFO] Installiere Abhängigkeiten..."
    source venv/bin/activate
    pip install -r requirements.txt --quiet
else
    source venv/bin/activate
fi

echo ""
echo "[OK] App startet im Browser..."
echo "[OK] Zum Beenden: Strg+C drücken"
echo ""

# Streamlit starten
streamlit run app.py --server.headless true --browser.gatherUsageStats false
