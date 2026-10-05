"""Script di automazione per il packaging di AI_short_gen in un eseguibile (.exe) standalone.

Utilizza PyInstaller per impacchettare l'applicazione con:
- Finestra nativa senza console (--noconsole / --windowed)
- Inclusione automatica di tutte le risorse grafiche di CustomTkinter (--collect-all customtkinter)
- Predisposizione delle cartelle operative (models/tts, stories, workspace) accanto all'eseguibile.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def build(onefile: bool = False) -> None:
    """Esegue il processo di compilazione con PyInstaller."""
    try:
        import PyInstaller.__main__
        import customtkinter
    except ImportError as e:
        print("\n" + "=" * 65)
        print(f" [ERRORE] Dipendenza mancante per la compilazione: {e}")
        print(" Assicurati di aver installato i requisiti con:")
        print("     pip install customtkinter pyinstaller")
        print("=" * 65 + "\n")
        sys.exit(1)

    print("=" * 65)
    print(" [BUILD] Avvio compilazione AI_short_gen (.exe standalone)")
    print(f" Modalita': {'File Singolo (--onefile)' if onefile else 'Directory Distribuibile (--onedir)'}")
    print("=" * 65)

    entry_point = PROJECT_ROOT / "app.py"
    dist_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build"

    # Percorso cartella package customtkinter per garantire inclusione temi
    ctk_dir = Path(customtkinter.__file__).parent

    args = [
        str(entry_point),
        "--name=AI_short_gen",
        "--noconsole",
        "--clean",
        "--noconfirm",
        "--collect-all=customtkinter",
        f"--add-data={ctk_dir}{os.pathsep}customtkinter",
        f"--paths={PROJECT_ROOT}",
    ]

    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    print(f"[i] Esecuzione PyInstaller con argomenti:\n    {' '.join(args[:6])} ...")
    PyInstaller.__main__.run(args)

    # Identifica la cartella di destinazione accanto all'eseguibile
    if onefile:
        target_root = dist_dir
    else:
        target_root = dist_dir / "AI_short_gen"

    print("\n[+] Configurazione cartelle operative accanto all'eseguibile...")
    folders_to_create = [
        target_root / "models" / "tts",
        target_root / "stories" / "archive",
        target_root / "workspace" / "input",
        target_root / "workspace" / "output",
        target_root / "workspace" / "temp",
    ]

    for folder in folders_to_create:
        folder.mkdir(parents=True, exist_ok=True)
        # Crea .gitkeep per consistenza
        (folder / ".gitkeep").touch(exist_ok=True)

    # Crea un file guida nella cartella models/tts di destinazione
    guide_file = target_root / "models" / "tts" / "ISTRUZIONI_MODELLI_VOCALI.txt"
    guide_file.write_text(
        "Inserisci qui i modelli vocali Piper ONNX scaricati da HuggingFace:\n"
        "https://huggingface.co/rhasspy/piper-voices/tree/main/it/it_IT\n\n"
        "Esempio:\n"
        "- it_IT-riccardo-x_low.onnx\n"
        "- it_IT-riccardo-x_low.onnx.json\n",
        encoding="utf-8",
    )

    # Copia eventuali storie esistenti
    source_stories = PROJECT_ROOT / "stories"
    if source_stories.exists():
        for txt_file in source_stories.glob("*.txt"):
            shutil.copy2(str(txt_file), str(target_root / "stories" / txt_file.name))

    print("=" * 65)
    print(" [SUCCESSO] Compilazione completata con successo!")
    print(f" Eseguibile disponibile in:")
    if onefile:
        print(f" -> {dist_dir / 'AI_short_gen.exe'}")
    else:
        print(f" -> {target_root / 'AI_short_gen.exe'}")
    print("=" * 65)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compila AI_short_gen in un eseguibile Windows .exe")
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Crea un singolo file .exe compresso anziché una directory (avvio leggermente più lento ma file unico).",
    )
    args = parser.parse_args()
    build(onefile=args.onefile)


if __name__ == "__main__":
    main()

