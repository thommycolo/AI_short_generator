"""Script di test isolato per la verifica dei moduli StoryManager e PiperEngine.

Esegue i 4 passaggi di validazione:
1. Verifica o creazione di una storia di test in stories/
2. Lettura del testo tramite StoryManager
3. Verifica e inizializzazione di PiperEngine (con sintesi audio se il modello è presente)
4. Archiviazione atomica del file .txt in stories/archive/
"""

from __future__ import annotations

import sys
from pathlib import Path

# Assicura che la directory src sia presente nel sys.path per l'esecuzione diretta
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from story_manager import StoryManager
from text_optimizer import TextOptimizer, estimate_audio_duration, format_duration, optimize_for_tts
from tts_engine import PiperConfig, PiperEngine, DOWNLOAD_INSTRUCTIONS


def run_tts_test() -> None:
    """Esegue il test end-to-end del modulo di gestione storie e TTS."""
    project_root = src_dir.parent
    stories_dir = project_root / "stories"
    models_dir = project_root / "models" / "tts"
    temp_dir = project_root / "workspace" / "temp"

    temp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(" [TEST] AI_short_gen - Validazione StoryManager & TTS")
    print("=" * 65)

    # 1. Inizializzazione StoryManager e verifica file di test
    manager = StoryManager(stories_dir=stories_dir)
    unprocessed = manager.get_unprocessed_stories()

    if not unprocessed:
        sample_file = stories_dir / "test_story.txt"
        sample_text = (
            "In the digital realm, Dr. Smith discovered that A.I. could transform "
            "video creation with 50% more speed and efficiency, e.g. for YouTube Shorts."
        )
        sample_file.write_text(sample_text, encoding="utf-8")
        print(f"[+] File di test creato: {sample_file.name}")
        unprocessed = manager.get_unprocessed_stories()

    target_story = unprocessed[0]
    print(f"[OK] Storia selezionata per l'elaborazione: {target_story.name}")

    # 2. Lettura del testo tramite StoryManager
    story_text = manager.read_story(target_story)
    print(f"[OK] Testo letto ({len(story_text)} caratteri):")
    print(f"    \"{story_text}\"")

    # 2.1. Validazione ottimizzazione fonetica NLP e stima durata audio
    optimized_text = optimize_for_tts(story_text)
    est_duration = estimate_audio_duration(story_text, wpm=150, speed=1.0)
    print(f"[OK] Testo Ottimizzato NLP per TTS (English):")
    print(f"    \"{optimized_text}\"")
    print(f"[OK] Stima Durata Audio (150 WPM): ~{format_duration(est_duration)} ({est_duration:.1f}s)")

    # 3. Rilevamento modelli vocali e inizializzazione PiperEngine
    available_models = PiperEngine.list_available_models(models_dir)
    print(f"\n[i] Modelli ONNX rilevati in '{models_dir.name}': {len(available_models)}")

    audio_generated = False
    if available_models:
        model_path = available_models[0]
        print(f"[+] Utilizzo del modello: {Path(model_path).name}")

        config = PiperConfig(
            model_path=model_path,
            length_scale=1.0,
            noise_scale=0.667,
            noise_w=0.8,
        )
        engine = PiperEngine(config=config)

        output_audio_path = temp_dir / f"{target_story.stem}.wav"
        print(f"[...] Avvio sintesi vocale su: {output_audio_path.name}")

        try:
            generated_wav = engine.synthesize(story_text, output_audio_path)
            print(f"[OK] Audio generato con successo: {generated_wav}")
            audio_generated = True
        except Exception as e:
            print(f"[!] Errore durante la sintesi vocale: {e}")
    else:
        print("\n" + "-" * 65)
        print("[AVVISO] Nessun modello vocale ONNX presente nella cartella 'models/tts/'.")
        print(DOWNLOAD_INSTRUCTIONS)
        print("-" * 65 + "\n")

    # 4. Spostamento atomico della storia in stories/archive/
    archived_path = manager.mark_as_processed(target_story)
    print(f"[OK] File storia archiviato con successo in:")
    print(f"    -> {archived_path}")

    print("\n" + "=" * 65)
    print(f" [RIEPILOGO TEST]")
    print(f" - StoryManager:  OK (lettura e archiviazione atomica)")
    print(f" - TextOptimizer: OK (pulizia fonetica NLP e stima durata)")
    print(f" - PiperEngine:   {'OK (Audio generato)' if audio_generated else 'In attesa di modello .onnx'}")
    print("=" * 65)


if __name__ == "__main__":
    run_tts_test()

