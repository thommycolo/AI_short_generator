"""Entry point desktop nativo dell'applicazione AI_short_gen.

Inizializza i moduli di backend (StoryManager, PiperEngine)
e avvia l'interfaccia grafica desktop nativa basata su CustomTkinter.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app")

# Gestione percorsi per esecuzione diretta o compilata con PyInstaller
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent.resolve()
else:
    PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.story_manager import StoryManager
from src.tts_engine import PiperEngine

try:
    from src.gui import MainWindow, create_gui
except ModuleNotFoundError as err:
    if "customtkinter" in str(err):
        print("\n" + "=" * 65)
        print(" [ERRORE DIPENDENZA] Il pacchetto 'customtkinter' non risulta installato.")
        print("=" * 65)
        print(" Per installare i requisiti per la nuova GUI nativa desktop:")
        print("     pip install -r requirements.txt")
        print("\n Oppure:")
        print("     pip install customtkinter pyinstaller")
        print("=" * 65 + "\n")
        sys.exit(1)
    raise


def main() -> None:
    """Inizializza i servizi e lancia il loop desktop CustomTkinter."""
    logger.info("Inizializzazione di AI_short_gen Desktop Studio...")

    # Assicura le cartelle di lavoro
    (PROJECT_ROOT / "models" / "tts").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "stories" / "archive").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "workspace" / "input").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "workspace" / "output").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "workspace" / "temp").mkdir(parents=True, exist_ok=True)

    # 1. Inizializzazione classi di backend
    story_manager = StoryManager()
    tts_engine = PiperEngine()

    # 2. Creazione della finestra CustomTkinter
    app = MainWindow(tts_engine=tts_engine, story_manager=story_manager)

    # 3. Avvio del mainloop nativo dell'interfaccia desktop
    logger.info("Avvio desktop mainloop...")
    app.mainloop()


if __name__ == "__main__":
    main()
