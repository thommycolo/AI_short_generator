"""Interfaccia grafica desktop nativa per AI_short_gen basata su CustomTkinter.

Design: Estetica gaming / cyberpunk / futuristica, dark mode forzata.
UX: Flusso semplificato e intuitivo, impostazioni avanzate collassabili,
    elaborazione asincrona con threading per prevenire freeze della UI.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Optional

try:
    import winsound
except ImportError:
    winsound = None  # Fallback per ambienti non-Windows

import customtkinter as ctk

from src.story_manager import StoryManager, get_app_root
from src.tts_engine import DOWNLOAD_INSTRUCTIONS, PiperConfig, PiperEngine

try:
    from src.text_optimizer import estimate_audio_duration, format_duration
except ImportError:
    from text_optimizer import estimate_audio_duration, format_duration

logger = logging.getLogger(__name__)

# Configurazione globale CustomTkinter: Tema Gaming Scuro
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palette colori Cyber / Gaming
CLR_BG_DARK = "#0B0E14"       # Obsidian Black profondo
CLR_CARD_BG = "#131A26"       # Blu scuro grafite
CLR_CARD_BORDER = "#1E293B"   # Bordo sottile elegante
CLR_ACCENT_CYAN = "#00F0FF"   # Ciano neon
CLR_ACCENT_HOVER = "#00C2D6"  # Ciano intermedio
CLR_ACCENT_PURPLE = "#8B5CF6" # Viola neon
CLR_PURPLE_HOVER = "#7C3AED"  # Viola scuro
CLR_SUCCESS = "#10B981"       # Smeraldo neon
CLR_DANGER = "#EF4444"        # Rosso avviso
CLR_TEXT_MUTED = "#94A3B8"    # Testo secondario
CLR_TEXT_MAIN = "#F8FAFC"     # Bianco primario

# Pulsante generazione audio (tonalità sobria ed elegante, non appariscente)
CLR_BTN_AUDIO = "#2563EB"        # Blu professionale sobrio (sostituisce il ciano neon)
CLR_BTN_AUDIO_HOVER = "#1D4ED8"  # Blu scuro hover
CLR_BTN_AUDIO_TEXT = "#FFFFFF"   # Testo bianco ad alta leggibilità


class FuturisticDialog(ctk.CTkToplevel):
    """Finestra di avviso e dialogo con styling cyber/gaming."""

    def __init__(
        self,
        parent: ctk.CTk,
        title: str,
        message: str,
        is_error: bool = False,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("460x220")
        self.resizable(False, False)
        self.configure(fg_color=CLR_BG_DARK)
        self.transient(parent)
        self.grab_set()

        border_clr = CLR_DANGER if is_error else CLR_ACCENT_CYAN
        badge_text = "SYSTEM ALERT // ERROR" if is_error else "SYSTEM NOTIFICATION"
        badge_clr = CLR_DANGER if is_error else CLR_ACCENT_CYAN

        container = ctk.CTkFrame(
            self,
            fg_color=CLR_CARD_BG,
            border_width=1,
            border_color=border_clr,
            corner_radius=12,
        )
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            container,
            text=badge_text,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=badge_clr,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            container,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=CLR_TEXT_MUTED,
            wraplength=390,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkButton(
            container,
            text="CONFERMA",
            fg_color=badge_clr,
            hover_color=CLR_PURPLE_HOVER if not is_error else "#DC2626",
            text_color="#000000" if not is_error else "#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            width=120,
            command=self.destroy,
        ).pack(anchor="e", padx=16, pady=(0, 12))


class MainWindow(ctk.CTk):
    """Finestra principale dell'applicazione desktop AI_short_gen."""

    def __init__(
        self,
        tts_engine: Optional[PiperEngine] = None,
        story_manager: Optional[StoryManager] = None,
    ) -> None:
        super().__init__()

        self.project_root = get_app_root()
        self.temp_dir = self.project_root / "workspace" / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.story_manager = story_manager or StoryManager()
        self.tts_engine = tts_engine or PiperEngine()

        # Configurazione Finestra Desktop
        self.title("AI_short_gen // Cybernetic Studio")
        self.geometry("1120x760")
        self.minsize(980, 680)
        self.configure(fg_color=CLR_BG_DARK)

        # Stato interno
        self.is_generating: bool = False
        self.last_generated_audio: Optional[Path] = None
        self.is_playing_audio: bool = False
        self.advanced_visible: bool = False

        self._build_header()
        self._build_tabs()
        self._build_footer_status()

        # Inizializza dati
        self.refresh_stories_list()
        self.refresh_models_list()

    # =========================================================================
    # COSTRUZIONE UI: HEADER & TOP BAR
    # =========================================================================

    def _build_header(self) -> None:
        """Costruisce l'header in stile gaming launcher."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color=CLR_CARD_BG,
            corner_radius=0,
            height=70,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left", padx=24, pady=10)

        badge_frame = ctk.CTkFrame(
            left_box,
            fg_color="#1E1B4B",
            border_width=1,
            border_color=CLR_ACCENT_PURPLE,
            corner_radius=6,
        )
        badge_frame.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            badge_frame,
            text="STANDALONE v1.0",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=CLR_ACCENT_CYAN,
        ).pack(padx=8, pady=2)

        titles_box = ctk.CTkFrame(left_box, fg_color="transparent")
        titles_box.pack(side="left")

        ctk.CTkLabel(
            titles_box,
            text="AI_SHORT_GEN",
            font=ctk.CTkFont(family="Impact", size=22, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            titles_box,
            text="Local AI Video & Neural Voice Suite",
            font=ctk.CTkFont(size=11),
            text_color=CLR_TEXT_MUTED,
        ).pack(anchor="w")

        # Sezione Status Destra
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right", padx=24)

        self.engine_status_label = ctk.CTkLabel(
            right_box,
            text="● ENGINE ONLINE",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=CLR_SUCCESS,
        )
        self.engine_status_label.pack(side="right")

    # =========================================================================
    # COSTRUZIONE UI: SCHEDE (TABVIEW)
    # =========================================================================

    def _build_tabs(self) -> None:
        """Costruisce le schede principali dell'applicazione."""
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=CLR_BG_DARK,
            segmented_button_fg_color=CLR_CARD_BG,
            segmented_button_selected_color=CLR_ACCENT_PURPLE,
            segmented_button_selected_hover_color=CLR_PURPLE_HOVER,
            segmented_button_unselected_color=CLR_CARD_BG,
            segmented_button_unselected_hover_color="#1E293B",
            corner_radius=12,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(12, 6))

        self.tab_audio = self.tabview.add("🎙️ AUDIO & STORY STUDIO")
        self.tab_video = self.tabview.add("🎬 VIDEO ENGINE (PLACEHOLDER)")

        self._build_tab_audio_content()
        self._build_tab_video_content()

    # =========================================================================
    # TAB 1: AUDIO & STORY STUDIO (ATTIVO)
    # =========================================================================

    def _build_tab_audio_content(self) -> None:
        """Costruisce la UI del generatore TTS con UX semplificata ed estetica gaming."""
        main_layout = ctk.CTkFrame(self.tab_audio, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, padx=8, pady=8)

        # Barra Superiore Selezione Storia & File
        top_bar = ctk.CTkFrame(
            main_layout,
            fg_color=CLR_CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        top_bar.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(
            top_bar,
            text="STORIA:",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=CLR_ACCENT_CYAN,
        ).pack(side="left", padx=(14, 6), pady=10)

        self.story_selector = ctk.CTkOptionMenu(
            top_bar,
            values=["Nessuna storia rilevata"],
            width=260,
            command=self._on_story_selected,
            fg_color="#1E293B",
            button_color="#334155",
            button_hover_color=CLR_ACCENT_PURPLE,
            corner_radius=8,
        )
        self.story_selector.pack(side="left", padx=4, pady=10)

        self.btn_refresh_stories = ctk.CTkButton(
            top_bar,
            text="🔄",
            width=36,
            height=32,
            fg_color="#1E293B",
            hover_color=CLR_ACCENT_PURPLE,
            command=self.refresh_stories_list,
            corner_radius=8,
        )
        self.btn_refresh_stories.pack(side="left", padx=4, pady=10)

        self.btn_browse_txt = ctk.CTkButton(
            top_bar,
            text="📂 Carica .txt",
            width=110,
            height=32,
            fg_color="#1E293B",
            hover_color=CLR_ACCENT_CYAN,
            text_color=CLR_TEXT_MAIN,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._browse_and_load_file,
            corner_radius=8,
        )
        self.btn_browse_txt.pack(side="left", padx=8, pady=10)

        # Selettore Modello Vocale a Destra
        ctk.CTkLabel(
            top_bar,
            text="VOCE ONNX:",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=CLR_ACCENT_CYAN,
        ).pack(side="left", padx=(20, 6), pady=10)

        self.model_selector = ctk.CTkOptionMenu(
            top_bar,
            values=["Nessun modello in models/tts/"],
            width=240,
            fg_color="#1E293B",
            button_color="#334155",
            button_hover_color=CLR_ACCENT_PURPLE,
            corner_radius=8,
        )
        self.model_selector.pack(side="left", padx=4, pady=10)

        self.btn_refresh_models = ctk.CTkButton(
            top_bar,
            text="🔄",
            width=36,
            height=32,
            fg_color="#1E293B",
            hover_color=CLR_ACCENT_PURPLE,
            command=self.refresh_models_list,
            corner_radius=8,
        )
        self.btn_refresh_models.pack(side="left", padx=4, pady=10)

        # Area Centrale: Editor Testo Storia
        editor_frame = ctk.CTkFrame(
            main_layout,
            fg_color=CLR_CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        editor_frame.pack(fill="both", expand=True, pady=4, padx=2)

        editor_header = ctk.CTkFrame(editor_frame, fg_color="transparent")
        editor_header.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            editor_header,
            text="// SCRIPT DI NARRAZIONE (TESTO PER LA VOCE SINTETICA)",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=CLR_TEXT_MUTED,
        ).pack(side="left")

        self.duration_estimate_label = ctk.CTkLabel(
            editor_header,
            text="⏱️ Durata stimata: ~00:00",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=CLR_ACCENT_CYAN,
        )
        self.duration_estimate_label.pack(side="right")
        self.char_counter_label = self.duration_estimate_label  # Retrocompatibilità

        self.text_editor = ctk.CTkTextbox(
            editor_frame,
            fg_color="#0B0F17",
            text_color=CLR_TEXT_MAIN,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            border_width=1,
            border_color="#1E293B",
            corner_radius=8,
            wrap="word",
        )
        self.text_editor.pack(fill="both", expand=True, padx=14, pady=(2, 12))
        self.text_editor.bind("<KeyRelease>", self._update_duration_estimate)
        self.text_editor.bind("<ButtonRelease>", self._update_duration_estimate)

        # Sezione Avanzata Collassabile (Speed, Noise, Archive)
        self.advanced_frame = ctk.CTkFrame(
            main_layout,
            fg_color="#0E1420",
            corner_radius=10,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )

        adv_inner = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        adv_inner.pack(fill="x", padx=16, pady=12)

        # Slider Velocità
        s_box = ctk.CTkFrame(adv_inner, fg_color="transparent")
        s_box.pack(side="left", expand=True, fill="x", padx=6)
        self.lbl_speed = ctk.CTkLabel(
            s_box,
            text="Velocità (1.00x):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        )
        self.lbl_speed.pack(anchor="w")
        self.slider_speed = ctk.CTkSlider(
            s_box,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            progress_color=CLR_ACCENT_CYAN,
            button_color=CLR_ACCENT_CYAN,
            command=self._on_speed_slider_changed,
        )
        self.slider_speed.set(1.0)
        self.slider_speed.pack(fill="x", pady=4)

        # Slider Noise Scale
        n_box = ctk.CTkFrame(adv_inner, fg_color="transparent")
        n_box.pack(side="left", expand=True, fill="x", padx=6)
        self.lbl_noise = ctk.CTkLabel(
            n_box,
            text="Espressività (0.67):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        )
        self.lbl_noise.pack(anchor="w")
        self.slider_noise = ctk.CTkSlider(
            n_box,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            progress_color=CLR_ACCENT_PURPLE,
            button_color=CLR_ACCENT_PURPLE,
            command=lambda v: self.lbl_noise.configure(text=f"Espressività ({v:.2f}):"),
        )
        self.slider_noise.set(0.667)
        self.slider_noise.pack(fill="x", pady=4)

        # Slider Noise W
        w_box = ctk.CTkFrame(adv_inner, fg_color="transparent")
        w_box.pack(side="left", expand=True, fill="x", padx=6)
        self.lbl_noise_w = ctk.CTkLabel(
            w_box,
            text="Durata Fonemi (0.80):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        )
        self.lbl_noise_w.pack(anchor="w")
        self.slider_noise_w = ctk.CTkSlider(
            w_box,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            progress_color=CLR_ACCENT_PURPLE,
            button_color=CLR_ACCENT_PURPLE,
            command=lambda v: self.lbl_noise_w.configure(text=f"Durata Fonemi ({v:.2f}):"),
        )
        self.slider_noise_w.set(0.8)
        self.slider_noise_w.pack(fill="x", pady=4)

        # Checkbox Archiviazione
        self.chk_archive = ctk.CTkCheckBox(
            adv_inner,
            text="Archivia .txt in stories/archive/",
            text_color=CLR_TEXT_MAIN,
            fg_color=CLR_ACCENT_CYAN,
            hover_color=CLR_ACCENT_HOVER,
            corner_radius=6,
        )
        self.chk_archive.select()
        self.chk_archive.pack(side="right", padx=(10, 0), pady=4)

        # Barra di Controllo Inferiore: Toggle Avanzate + Pulsantone + Player
        action_bar = ctk.CTkFrame(main_layout, fg_color="transparent")
        action_bar.pack(fill="x", pady=(8, 4), padx=2)

        # Bottone Toggle Impostazioni Avanzate
        self.btn_toggle_advanced = ctk.CTkButton(
            action_bar,
            text="⚙️ Impostazioni Avanzate ▼",
            width=180,
            height=46,
            fg_color="#1E293B",
            hover_color="#334155",
            text_color=CLR_TEXT_MUTED,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_advanced_settings,
            corner_radius=10,
        )
        self.btn_toggle_advanced.pack(side="left", padx=(0, 10))

        # Controlli Player Audio (Play, Stop, Apri Cartella)
        self.player_box = ctk.CTkFrame(action_bar, fg_color=CLR_CARD_BG, corner_radius=10)
        self.player_box.pack(side="left", padx=4)

        self.btn_play_audio = ctk.CTkButton(
            self.player_box,
            text="▶ Ascolta",
            width=90,
            height=46,
            fg_color="#166534",
            hover_color="#15803D",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled",
            command=self._toggle_play_audio,
            corner_radius=8,
        )
        self.btn_play_audio.pack(side="left", padx=6, pady=4)

        self.btn_open_folder = ctk.CTkButton(
            self.player_box,
            text="📁 Apri Cartella",
            width=110,
            height=46,
            fg_color="#1E293B",
            hover_color="#334155",
            text_color=CLR_TEXT_MAIN,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_temp_folder,
            corner_radius=8,
        )
        self.btn_open_folder.pack(side="left", padx=(0, 6), pady=4)

        # PULSANTE PRINCIPALE "⚡ GENERA AUDIO" (colore sobrio ed elegante)
        self.btn_generate_audio = ctk.CTkButton(
            action_bar,
            text="⚡ GENERA AUDIO",
            height=46,
            fg_color=CLR_BTN_AUDIO,
            hover_color=CLR_BTN_AUDIO_HOVER,
            text_color=CLR_BTN_AUDIO_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self._start_audio_generation_thread,
            corner_radius=10,
        )
        self.btn_generate_audio.pack(side="right", fill="x", expand=True, padx=(10, 0))

    # =========================================================================
    # TAB 2: VIDEO ENGINE (PLACEHOLDER FUTURISTICO)
    # =========================================================================

    def _build_tab_video_content(self) -> None:
        """Costruisce la scheda placeholder per la futura pipeline video."""
        video_layout = ctk.CTkFrame(self.tab_video, fg_color="transparent")
        video_layout.pack(fill="both", expand=True, padx=12, pady=12)

        # Card di Stato Pipeline
        status_card = ctk.CTkFrame(
            video_layout,
            fg_color=CLR_CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        status_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            status_card,
            text="// VIDEO ENGINE PIPELINE : IN STANDBY",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=CLR_ACCENT_CYAN,
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            status_card,
            text=(
                "I moduli di elaborazione MoviePy e PySceneDetect (video_cutter.py ed editor.py) "
                "saranno agganciati a questa dashboard nel prossimo sprint architetturale."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CLR_TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # Griglia Impostazioni Video Placeholder
        grid_frame = ctk.CTkFrame(video_layout, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        col_left = ctk.CTkFrame(
            grid_frame,
            fg_color=CLR_CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(
            col_left,
            text="INPUT MULTIMEDIALI",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        ctk.CTkButton(
            col_left,
            text="🎬 Seleziona Video Sorgente (workspace/input/)",
            height=40,
            fg_color="#1E293B",
            hover_color="#334155",
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=8)

        ctk.CTkButton(
            col_left,
            text="🎵 Seleziona Traccia Audio Narrata",
            height=40,
            fg_color="#1E293B",
            hover_color="#334155",
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=8)

        col_right = ctk.CTkFrame(
            grid_frame,
            fg_color=CLR_CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        col_right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        ctk.CTkLabel(
            col_right,
            text="PARAMETRI SHORTS & REELS",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=CLR_TEXT_MAIN,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            col_right,
            text="Durata Massima Clip: 60 sec",
            font=ctk.CTkFont(size=12),
            text_color=CLR_TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(4, 0))

        slider_v = ctk.CTkSlider(col_right, from_=15, to=180, progress_color=CLR_ACCENT_PURPLE)
        slider_v.set(60)
        slider_v.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            col_right,
            text="Formato Risoluzione:",
            font=ctk.CTkFont(size=12),
            text_color=CLR_TEXT_MUTED,
        ).pack(anchor="w", padx=16)

        ctk.CTkSegmentedButton(
            col_right,
            values=["9:16 Verticale", "1:1 Quadrato", "16:9"],
            selected_color=CLR_ACCENT_PURPLE,
        ).pack(fill="x", padx=16, pady=(4, 16))

        # Bottone Video Disabilitato
        ctk.CTkButton(
            video_layout,
            text="⚡ CREA SHORTS (STANDBY)",
            height=50,
            fg_color="#334155",
            text_color="#94A3B8",
            font=ctk.CTkFont(family="Impact", size=18),
            state="disabled",
            corner_radius=10,
        ).pack(fill="x", pady=(16, 0))

    # =========================================================================
    # COSTRUZIONE UI: FOOTER STATUS BAR
    # =========================================================================

    def _build_footer_status(self) -> None:
        """Costruisce la barra di stato inferiore."""
        footer_frame = ctk.CTkFrame(
            self,
            fg_color=CLR_CARD_BG,
            height=34,
            corner_radius=0,
            border_width=1,
            border_color=CLR_CARD_BORDER,
        )
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)

        self.status_bar_label = ctk.CTkLabel(
            footer_frame,
            text="Pronto per la generazione vocale.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=CLR_TEXT_MUTED,
        )
        self.status_bar_label.pack(side="left", padx=16)

        self.progress_bar = ctk.CTkProgressBar(
            footer_frame,
            width=160,
            height=8,
            progress_color=CLR_ACCENT_CYAN,
            fg_color="#1E293B",
            mode="indeterminate",
        )
        # Nascosta all'avvio

    # =========================================================================
    # LOGICA: GESTIONE MODELLI E STORIE
    # =========================================================================

    def refresh_stories_list(self) -> None:
        """Ricarica l'elenco delle storie non ancora elaborate da stories/."""
        stories = self.story_manager.get_unprocessed_stories()
        names = [s.name for s in stories]

        if names:
            self.story_selector.configure(values=names)
            self.story_selector.set(names[0])
            self._load_story_text(stories[0])
        else:
            self.story_selector.configure(values=["Nessuna storia in stories/"])
            self.story_selector.set("Nessuna storia in stories/")

    def refresh_models_list(self) -> None:
        """Ricarica l'elenco dei modelli ONNX disponibili da models/tts/."""
        models = self.tts_engine.list_available_models()
        model_names = [Path(m).name for m in models]

        if model_names:
            self.model_selector.configure(values=model_names)
            self.model_selector.set(model_names[0])
            self.engine_status_label.configure(
                text="● ENGINE ONLINE (VOICE READY)",
                text_color=CLR_SUCCESS,
            )
        else:
            self.model_selector.configure(values=["Nessun modello trovato (.onnx)"])
            self.model_selector.set("Nessun modello trovato (.onnx)")
            self.engine_status_label.configure(
                text="○ ENGINE WARNING (NO VOICE MODEL)",
                text_color=CLR_DANGER,
            )

    def _on_story_selected(self, choice: str) -> None:
        """Carica il testo quando l'utente seleziona un file dal menu."""
        stories = self.story_manager.get_unprocessed_stories()
        for s in stories:
            if s.name == choice:
                self._load_story_text(s)
                break

    def _load_story_text(self, file_path: Path) -> None:
        """Legge il file e popola l'editor di testo."""
        try:
            content = self.story_manager.read_story(file_path)
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", content)
            self._update_duration_estimate()
            self.status_bar_label.configure(
                text=f"Caricato: {file_path.name} ({len(content)} caratteri)",
                text_color=CLR_TEXT_MAIN,
            )
        except Exception as err:
            self._show_alert("Errore Lettura File", str(err), is_error=True)

    def _browse_and_load_file(self) -> None:
        """Apre un file dialog per selezionare un file .txt esterno."""
        path = filedialog.askopenfilename(
            title="Seleziona file storia .txt",
            filetypes=[("File di Testo", "*.txt"), ("Tutti i file", "*.*")],
        )
        if not path:
            return

        source = Path(path)
        dest = self.story_manager.stories_dir / source.name

        try:
            if source.resolve() != dest.resolve():
                shutil.copy2(str(source), str(dest))

            self.refresh_stories_list()
            self.story_selector.set(dest.name)
            self._load_story_text(dest)
        except Exception as err:
            self._show_alert("Errore Caricamento", str(err), is_error=True)

    def _on_speed_slider_changed(self, value: float) -> None:
        """Aggiorna il badge della velocità e ricalcola la stima della durata audio."""
        self.lbl_speed.configure(text=f"Velocità ({value:.2f}x):")
        self._update_duration_estimate()

    def _update_duration_estimate(self, event=None) -> None:
        """Calcola e aggiorna la durata audio stimata (140 WPM, modulata da Speed)."""
        text = self.text_editor.get("1.0", "end-1c")
        try:
            speed = float(self.slider_speed.get())
        except (AttributeError, ValueError):
            speed = 1.0

        seconds = estimate_audio_duration(text, wpm=150, speed=speed)
        formatted = format_duration(seconds)
        self.duration_estimate_label.configure(text=f"⏱️ Durata stimata: ~{formatted}")

    def _update_char_counter(self, event=None) -> None:
        """Alias di retrocompatibilità per il vecchio contatore caratteri."""
        self._update_duration_estimate(event)

    def _toggle_advanced_settings(self) -> None:
        """Mostra/nasconde il pannello dei parametri avanzati di sintesi."""
        if self.advanced_visible:
            self.advanced_frame.pack_forget()
            self.btn_toggle_advanced.configure(text="⚙️ Impostazioni Avanzate ▼")
            self.advanced_visible = False
        else:
            self.advanced_frame.pack(fill="x", pady=4, padx=2, before=self.btn_toggle_advanced.master)
            self.btn_toggle_advanced.configure(text="⚙️ Impostazioni Avanzate ▲")
            self.advanced_visible = True

    # =========================================================================
    # LOGICA: GENERAZIONE AUDIO ASINCRONA (THREADING)
    # =========================================================================

    def _start_audio_generation_thread(self) -> None:
        """Valida gli input e avvia la generazione TTS in un thread in background."""
        if self.is_generating:
            return

        text = self.text_editor.get("1.0", "end-1c").strip()
        if not text:
            self._show_alert(
                "Testo Mancante",
                "Inserisci o carica un testo prima di avviare la sintesi vocale.",
                is_error=True,
            )
            return

        selected_model = self.model_selector.get()
        available_models = self.tts_engine.list_available_models()
        model_path_str: Optional[str] = None

        for m in available_models:
            if Path(m).name == selected_model:
                model_path_str = m
                break

        if not model_path_str:
            self._show_alert(
                "Modello Vocale Assente",
                f"Nessun modello ONNX valido selezionato.\n\n{DOWNLOAD_INSTRUCTIONS}",
                is_error=True,
            )
            return

        # Prepara parametri
        speed = float(self.slider_speed.get())
        noise = float(self.slider_noise.get())
        noise_w = float(self.slider_noise_w.get())
        should_archive = bool(self.chk_archive.get())
        selected_story_name = self.story_selector.get()

        # Blocca controlli e avvia indicatore di progresso
        self.is_generating = True
        self.btn_generate_audio.configure(
            state="disabled",
            text="GENERAZIONE IN CORSO...",
            fg_color="#334155",
        )
        self.progress_bar.pack(side="right", padx=16)
        self.progress_bar.start()
        self.status_bar_label.configure(
            text="Sintesi vocale in corso tramite Piper TTS...",
            text_color=CLR_ACCENT_CYAN,
        )

        # Lancia thread separato per prevenire il freeze dell'interfaccia
        worker = threading.Thread(
            target=self._run_synthesis_worker,
            args=(text, model_path_str, speed, noise, noise_w, should_archive, selected_story_name),
            daemon=True,
        )
        worker.start()

    def _run_synthesis_worker(
        self,
        text: str,
        model_path: str,
        speed: float,
        noise: float,
        noise_w: float,
        should_archive: bool,
        story_name: str,
    ) -> None:
        """Worker eseguito nel thread secondario."""
        try:
            # Correzione logica velocità:
            # Per l'utente, 0.5x è metà velocità (quindi raddoppia la lunghezza audio: length_scale = 2.0)
            # e 2.0x è doppia velocità (quindi dimezza la lunghezza audio: length_scale = 0.5).
            length_scale = (1.0 / speed) if speed > 0 else 1.0

            config = PiperConfig(
                model_path=model_path,
                length_scale=length_scale,
                noise_scale=noise,
                noise_w=noise_w,
            )
            self.tts_engine.config = config

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = Path(story_name).stem if story_name and " " not in story_name else "voice"
            output_wav = self.temp_dir / f"{stem}_{timestamp}.wav"

            generated_path = self.tts_engine.synthesize(text, output_wav)
            self.last_generated_audio = Path(generated_path)

            # Archiviazione opzionale
            archived_info = ""
            if should_archive and story_name:
                stories = self.story_manager.get_unprocessed_stories()
                for s in stories:
                    if s.name == story_name:
                        archived_target = self.story_manager.mark_as_processed(s)
                        archived_info = f" | Archiviata in {archived_target.name}"
                        break

            # Comunica successo al thread principale
            self.after(0, self._on_generation_success, str(output_wav.name), archived_info)

        except Exception as err:
            logger.error("Errore sintesi: %s", err, exc_info=True)
            self.after(0, self._on_generation_error, str(err))

    def _on_generation_success(self, wav_name: str, archived_info: str) -> None:
        """Callback thread principale in caso di successo."""
        self._reset_generation_state()
        self.btn_play_audio.configure(state="normal")
        self.status_bar_label.configure(
            text=f"Audio generato: {wav_name}{archived_info}",
            text_color=CLR_SUCCESS,
        )
        self.refresh_stories_list()
        self._show_alert(
            "Generazione Completata",
            f"File audio creato con successo:\n{wav_name}\n\nPuoi ascoltarlo cliccando '▶ Ascolta'.",
        )

    def _on_generation_error(self, err_msg: str) -> None:
        """Callback thread principale in caso di errore."""
        self._reset_generation_state()
        self.status_bar_label.configure(
            text=f"Errore nella generazione audio.",
            text_color=CLR_DANGER,
        )
        self._show_alert("Errore Sintesi Vocale", err_msg, is_error=True)

    def _reset_generation_state(self) -> None:
        """Ripristina lo stato dei pulsanti dopo la generazione."""
        self.is_generating = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.btn_generate_audio.configure(
            state="normal",
            text="⚡ GENERA AUDIO",
            fg_color=CLR_BTN_AUDIO,
        )

    # =========================================================================
    # AUDIO PREVIEW & FILE UTILITY
    # =========================================================================

    def _toggle_play_audio(self) -> None:
        """Riproduce o interrompe l'audio tramite winsound in modo asincrono."""
        if not self.last_generated_audio or not self.last_generated_audio.exists():
            return

        if winsound is None:
            self._show_alert("Audio Player", "Riproduzione winsound disponibile solo su Windows.")
            return

        if not self.is_playing_audio:
            try:
                winsound.PlaySound(
                    str(self.last_generated_audio),
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
                self.is_playing_audio = True
                self.btn_play_audio.configure(text="⏹ Ferma", fg_color="#991B1B")
            except Exception as e:
                self._show_alert("Errore Riproduzione", str(e), is_error=True)
        else:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.is_playing_audio = False
            self.btn_play_audio.configure(text="▶ Ascolta", fg_color="#166534")

    def _open_temp_folder(self) -> None:
        """Apre la cartella di output temporanea in Esplora Risorse."""
        try:
            if sys.platform == "win32":
                os.startfile(str(self.temp_dir))
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(self.temp_dir)])
        except Exception as err:
            self._show_alert("Errore Apertura Cartella", str(err), is_error=True)

    def _show_alert(self, title: str, message: str, is_error: bool = False) -> None:
        """Mostra una finestra di alert stilizzata."""
        FuturisticDialog(self, title=title, message=message, is_error=is_error)


def create_gui(
    tts_engine: Optional[PiperEngine] = None,
    story_manager: Optional[StoryManager] = None,
) -> MainWindow:
    """Funzione factory compatibile per istanziare l'interfaccia CustomTkinter."""
    return MainWindow(tts_engine=tts_engine, story_manager=story_manager)
