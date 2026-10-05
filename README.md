# AI_short_gen

Applicazione desktop nativa (CustomTkinter) per la generazione automatica di mini video (Shorts/Reels/TikTok) a partire da video di lunga durata e storie testuali, con elaborazione completamente locale basata su AI.

## Architettura del Progetto

Il progetto adotta i principi della **Clean Architecture**, garantendo separazione delle responsabilità, modularità e compilabilità autonoma in un unico eseguibile `.exe`:

```
AI_short_gen/
├── models/                  # Pesi dei modelli AI scaricati localmente
│   └── tts/                 # Modelli Piper TTS (.onnx e .onnx.json)
├── stories/                 # File di testo (.txt) grezzi inseriti dall'utente
│   └── archive/             # Storie .txt già elaborate (prevenzione duplicati)
├── workspace/               # Gestione asset e pipeline di elaborazione
│   ├── input/               # Video originali caricati dall'utente
│   ├── output/              # Mini-video finali generati
│   └── temp/                # File temporanei (audio generato, clip intermedie)
├── src/                     # Core logico modulare
│   ├── __init__.py          # Package Python ed export dei componenti principali
│   ├── story_manager.py     # Gestione, lettura e archiviazione atomica delle storie
│   ├── tts_engine.py        # Sintesi vocale locale (Piper TTS API / CLI)
│   ├── video_cutter.py      # Scene detection e taglio automatico (PySceneDetect + MoviePy)
│   ├── editor.py            # Composizione, montaggio e sync audio/video (MoviePy)
│   ├── gui.py               # GUI desktop nativa CustomTkinter (Gaming/Cyber Dark)
│   └── test_tts.py          # Script di test isolato per StoryManager e PiperEngine
├── app.py                   # Entry point applicativo (avvio CustomTkinter mainloop)
├── build_exe.py             # Script di compilazione in eseguibile (.exe) con PyInstaller
├── requirements.txt         # Dipendenze Python del progetto
├── .gitignore               # Regole di esclusione file e directory
└── README.md                # Documentazione architetturale
```

---

## 1. Installazione Dipendenze

Nel tuo terminale PowerShell dentro `C:\Users\thomm\Desktop\AI_short_gen`:

```powershell
# 1. Crea l'ambiente virtuale (se non già presente)
python -m venv venv

# 2. Attiva l'ambiente virtuale
.\venv\Scripts\Activate.ps1

# Se PowerShell blocca l'esecuzione dello script:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Installa le dipendenze
pip install -r requirements.txt
```

---

## 2. Avvio dell'Applicazione Desktop Nativa

Per lanciare la GUI desktop nativa con estetica Gaming Cyberpunk:
```powershell
python app.py
```

---

## 3. Compilazione in Eseguibile Windows (.exe)

Per distribuire l'applicazione come software standalone senza richiedere l'installazione di Python all'utente:

```powershell
# Compilazione cartella distribuibile (consigliata, avvio istantaneo):
python build_exe.py

# Oppure compilazione in singolo file .exe:
python build_exe.py --onefile
```

L'eseguibile compilato e la struttura di cartelle operative saranno pronti in `dist/AI_short_gen/AI_short_gen.exe`.

---

## 4. Modelli Vocali Piper TTS

I modelli vocali per Piper TTS sono gratuiti e disponibili su HuggingFace:
- [HuggingFace Piper Voices](https://huggingface.co/rhasspy/piper-voices)
- Per la lingua italiana: scarica il file `.onnx` e il file `.onnx.json` da `it/it_IT/` (es. `it_IT-riccardo-x_low.onnx` o `it_IT-paola-medium.onnx`).
- Posizionali all'interno della cartella `models/tts/`.
