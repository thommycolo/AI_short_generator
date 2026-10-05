"""Modulo per la generazione audio Text-to-Speech (TTS) in locale tramite Piper.

Fornisce la dataclass PiperConfig per la parametrizzazione del modello vocale
e la classe PiperEngine per la sintesi vocale e la gestione dei modelli ONNX.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from src.text_optimizer import optimize_for_tts
except ImportError:
    from text_optimizer import optimize_for_tts

logger = logging.getLogger(__name__)

DOWNLOAD_INSTRUCTIONS = (
    "Nessun modello vocale Piper ONNX trovato. "
    "Puoi scaricare modelli gratuiti in varie lingue (incluso l'italiano) da HuggingFace:\n"
    "https://huggingface.co/rhasspy/piper-voices\n"
    "Scarica sia il file .onnx sia il file .onnx.json e posizionali in 'models/tts/'."
)


@dataclass
class PiperConfig:
    """Configurazione dei parametri di sintesi vocale per Piper TTS.

    Attributes:
        model_path: Percorso del file .onnx del modello vocale.
        config_path: Percorso del file .onnx.json associato (opzionale se deducibile).
        speaker_id: ID del parlante per modelli multi-speaker (default 0 o None).
        length_scale: Velocità del parlato (default 1.0; < 1.0 velocizza, > 1.0 rallenta).
        noise_scale: Variabilità fonetica ed espressività (default 0.667).
        noise_w: Variabilità della durata dei fonemi (default 0.8).
    """

    model_path: Path | str
    config_path: Optional[Path | str] = None
    speaker_id: Optional[int] = None
    length_scale: float = 1.0
    noise_scale: float = 0.667
    noise_w: float = 0.8

    def __post_init__(self) -> None:
        """Normalizza e valida i percorsi dei modelli."""
        self.model_path = Path(self.model_path).resolve()

        if self.config_path is not None:
            self.config_path = Path(self.config_path).resolve()
        else:
            # Deduce automaticamente il file .json associato se presente
            candidate_onnx_json = self.model_path.with_name(f"{self.model_path.name}.json")
            candidate_json = self.model_path.with_suffix(".json")

            if candidate_onnx_json.is_file():
                self.config_path = candidate_onnx_json
            elif candidate_json.is_file():
                self.config_path = candidate_json


def get_app_root() -> Path:
    """Restituisce il percorso radice dell'applicazione (supporta sia sorgente che PyInstaller frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parent.parent


class PiperEngine:
    """Wrapper modulare per la sintesi vocale con Piper TTS."""

    def __init__(self, config: Optional[PiperConfig] = None) -> None:
        """Inizializza il motore TTS con una configurazione specifica.

        Args:
            config: Istanza di PiperConfig. Se None, richiede l'impostazione prima della sintesi.
        """
        self.config = config

    @staticmethod
    def list_available_models(models_dir: Optional[str | Path] = None) -> list[str]:
        """Restituisce la lista dei percorsi dei modelli vocali (.onnx) disponibili.

        Args:
            models_dir: Cartella in cui cercare i modelli. Se None, cerca in models/tts/.

        Returns:
            Lista di stringhe contenenti i percorsi assoluti ai modelli .onnx trovati.
        """
        if models_dir is None:
            project_root = get_app_root()
            search_dir = project_root / "models" / "tts"
        else:
            search_dir = Path(models_dir).resolve()

        if not search_dir.exists():
            return []

        models: list[str] = [
            str(p.resolve()) for p in search_dir.glob("*.onnx") if p.is_file()
        ]
        models.sort()
        return models

    def synthesize(self, text: str, output_path: str | Path) -> str:
        """Genera un file audio .wav dal testo fornito.

        Tenta primariamente l'utilizzo della libreria Python 'piper-tts',
        con fallback trasparente sull'eseguibile CLI via subprocess.

        Args:
            text: Testo da sintetizzare in parlato.
            output_path: Percorso del file .wav da generare.

        Returns:
            Percorso assoluto come stringa del file audio generato.

        Raises:
            ValueError: Se il testo è vuoto o la configurazione non è valida.
            FileNotFoundError: Se il file del modello ONNX non esiste.
            RuntimeError: Se entrambi i metodi di sintesi falliscono.
        """
        if not text or not text.strip():
            raise ValueError("Il testo da sintetizzare non può essere vuoto.")

        if self.config is None:
            raise ValueError("Configurazione Piper non impostata in PiperEngine.")

        model_file = Path(self.config.model_path)
        if not model_file.is_file():
            raise FileNotFoundError(
                f"Modello ONNX non trovato al percorso: {model_file}\n{DOWNLOAD_INSTRUCTIONS}"
            )

        target_path = Path(output_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Ottimizzazione fonetica e pre-processing NLP del testo prima del passaggio a Piper
        clean_text = optimize_for_tts(text)
        if not clean_text or not clean_text.strip():
            raise ValueError("Il testo da sintetizzare non contiene caratteri fonetici validi dopo l'ottimizzazione.")

        logger.info("Testo ottimizzato per TTS: '%s'", clean_text)

        # Tentativo 1: Libreria Python nativa (piper / piper.voice)
        try:
            return self._synthesize_via_python_lib(clean_text, target_path)
        except (ImportError, Exception) as py_err:
            logger.debug(
                "Sintesi tramite modulo Python piper non riuscita (%s), tentativo via subprocess CLI...",
                py_err,
            )

        # Tentativo 2: CLI piper / python -m piper via subprocess
        try:
            return self._synthesize_via_subprocess(clean_text, target_path)
        except Exception as sub_err:
            raise RuntimeError(
                f"Sintesi TTS fallita sia via libreria Python sia via CLI.\n"
                f"Dettaglio errore: {sub_err}"
            ) from sub_err

    def _synthesize_via_python_lib(self, text: str, output_path: Path) -> str:
        """Esegue la sintesi vocale usando le API Python della libreria piper-tts."""
        try:
            from piper.voice import PiperVoice
        except ImportError:
            from piper import PiperVoice  # type: ignore

        assert self.config is not None

        cfg_str = str(self.config.config_path) if self.config.config_path else None
        voice = PiperVoice.load(str(self.config.model_path), config_path=cfg_str)

        with wave.open(str(output_path), "wb") as wav_file:
            # Chiama la sintesi configurata
            kwargs = {
                "length_scale": self.config.length_scale,
                "noise_scale": self.config.noise_scale,
                "noise_w": self.config.noise_w,
            }
            if self.config.speaker_id is not None:
                kwargs["speaker_id"] = self.config.speaker_id

            voice.synthesize(text, wav_file, **kwargs)

        logger.info("Audio generato con successo via Python API: %s", output_path)
        return str(output_path)

    def _synthesize_via_subprocess(self, text: str, output_path: Path) -> str:
        """Esegue la sintesi vocale richiamando l'eseguibile piper via subprocess."""
        assert self.config is not None

        # Determina il comando base: eseguibile piper nel PATH o modulo python
        piper_bin = shutil.which("piper")
        if piper_bin:
            cmd = [piper_bin]
        else:
            cmd = [sys.executable, "-m", "piper"]

        cmd.extend([
            "--model", str(self.config.model_path),
            "--output_file", str(output_path),
            "--length-scale", str(self.config.length_scale),
            "--noise-scale", str(self.config.noise_scale),
            "--noise-w", str(self.config.noise_w),
        ])

        if self.config.config_path:
            cmd.extend(["--config", str(self.config.config_path)])

        if self.config.speaker_id is not None:
            cmd.extend(["--speaker", str(self.config.speaker_id)])

        process = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if process.returncode != 0:
            err_msg = process.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Comando piper terminato con codice {process.returncode}: {err_msg}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Il file audio di output non è stato generato o è vuoto: {output_path}")

        logger.info("Audio generato con successo via subprocess CLI: %s", output_path)
        return str(output_path)
