"""Modulo per la gestione e l'archiviazione delle storie (file di testo).

Fornisce la classe StoryManager per rilevare, leggere e archiviare
in modo atomico i file .txt inseriti dall'utente nella directory delle storie.
"""

from __future__ import annotations

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_app_root() -> Path:
    """Restituisce il percorso radice dell'applicazione (supporta sia sorgente che PyInstaller frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parent.parent


class StoryManager:
    """Gestisce il ciclo di vita dei file di testo delle storie.
    
    Responsabile della scansione di file .txt non elaborati, della lettura del loro
    contenuto e dello spostamento sicuro nell'archivio una volta completata l'elaborazione.
    """

    def __init__(
        self,
        stories_dir: Optional[Path | str] = None,
        archive_dir: Optional[Path | str] = None,
    ) -> None:
        """Inizializza StoryManager con i percorsi delle directory di lavoro.

        Args:
            stories_dir: Percorso alla directory contenente le storie .txt grezze.
                Se non specificato, fa riferimento alla cartella 'stories' nella root del progetto.
            archive_dir: Percorso alla directory di archiviazione per le storie elaborate.
                Se non specificato, fa riferimento alla sottocartella 'archive' in stories_dir.
        """
        project_root = get_app_root()
        self.stories_dir = (
            Path(stories_dir).resolve() if stories_dir else (project_root / "stories").resolve()
        )
        self.archive_dir = (
            Path(archive_dir).resolve() if archive_dir else (self.stories_dir / "archive").resolve()
        )

        # Assicura l'esistenza delle directory operative
        self.stories_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def get_unprocessed_stories(self) -> list[Path]:
        """Scansiona la directory delle storie alla ricerca di file .txt non elaborati.

        Esclude la cartella di archivio e qualsiasi altra sottodirectory.

        Returns:
            Lista di Path assoluti ai file .txt disponibili, ordinati per data di modifica crescente.
        """
        if not self.stories_dir.exists():
            return []

        unprocessed: list[Path] = []
        for item in self.stories_dir.iterdir():
            # Considera solo file regolari con estensione .txt
            if item.is_file() and item.suffix.lower() == ".txt":
                # Assicura che non sia all'interno dell'archivio
                if self.archive_dir not in item.parents and item.parent == self.stories_dir:
                    unprocessed.append(item.resolve())

        # Ordina per data di modifica (dal più vecchio al più recente)
        unprocessed.sort(key=lambda p: p.stat().st_mtime)
        return unprocessed

    def read_story(self, file_path: Path | str, encoding: str = "utf-8") -> str:
        """Legge e restituisce il contenuto testuale di una storia.

        Args:
            file_path: Percorso del file .txt da leggere.
            encoding: Codifica del file (default 'utf-8').

        Returns:
            Stringa con il testo pulito (whitespace iniziale/finale rimosso).

        Raises:
            FileNotFoundError: Se il file specificato non esiste.
            ValueError: Se il file specificato non è un file regolare .txt.
            IOError: Se si verificano errori durante la lettura del file.
        """
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File della storia non trovato: {path}")

        if path.suffix.lower() != ".txt":
            raise ValueError(f"Il file specificato non ha estensione .txt: {path}")

        try:
            content = path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            logger.warning(
                "Decodifica UTF-8 fallita per %s, fallback su encoding con replace", path
            )
            content = path.read_text(encoding=encoding, errors="replace")

        return content.strip()

    def mark_as_processed(self, file_path: Path | str) -> Path:
        """Sposta in modo atomico il file elaborato nella cartella di archivio.

        In caso di collisione di nome con un file già presente nell'archivio,
        appende un timestamp ISO per preservare lo storico senza sovrascritture accidentali.

        Args:
            file_path: Percorso del file da archiviare.

        Returns:
            Path assoluto della nuova posizione del file in stories/archive/.

        Raises:
            FileNotFoundError: Se il file sorgente non esiste.
        """
        source = Path(file_path).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Impossibile archiviare: file sorgente inesistente ({source})")

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        target = self.archive_dir / source.name

        # Gestione collisione di nomi tramite timestamp
        if target.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = source.stem
            suffix = source.suffix
            collision_free_name = f"{stem}_{timestamp}{suffix}"
            target = self.archive_dir / collision_free_name

            # Fallback ulteriore con contatore se richiamato nello stesso secondo
            counter = 1
            while target.exists():
                target = self.archive_dir / f"{stem}_{timestamp}_{counter}{suffix}"
                counter += 1

        # Spostamento atomico
        shutil.move(str(source), str(target))
        logger.info("Storia archiviata: %s -> %s", source.name, target.name)
        return target.resolve()

