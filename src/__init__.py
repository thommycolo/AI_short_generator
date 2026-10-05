"""AI_short_gen - Package sorgente principale."""

from src.story_manager import StoryManager
from src.tts_engine import PiperConfig, PiperEngine
from src.text_optimizer import (
    TextOptimizer,
    optimize_for_tts,
    estimate_audio_duration,
    format_duration,
)

__all__ = [
    "StoryManager",
    "PiperConfig",
    "PiperEngine",
    "TextOptimizer",
    "optimize_for_tts",
    "estimate_audio_duration",
    "format_duration",
]

try:
    from src.gui import MainWindow, create_gui
    __all__.extend(["MainWindow", "create_gui"])
except ImportError:
    # Consente l'utilizzo dei moduli non-GUI anche se customtkinter non è ancora installato
    MainWindow = None  # type: ignore
    create_gui = None  # type: ignore
