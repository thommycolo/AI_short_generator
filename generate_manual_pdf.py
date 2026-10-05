"""Script generatore del Manuale Utente ufficiale in formato PDF per AI_short_gen.

Costruisce un documento PDF multi-pagina (10 pagine) completo, professionale e
ad alta risoluzione secondo lo standard ISO 32000 (PDF 1.4), senza dipendere da
librerie esterne.
Aggiornato per pipeline in lingua INGLESE e correzione scala velocità TTS.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class PDFDocument:
    """Motore PDF leggero, affidabile e conforme agli standard per generare manuali tecnici."""

    def __init__(self, title: str = "Manuale Utente AI_short_gen", author: str = "AI_short_gen Studio") -> None:
        self.title = title
        self.author = author
        self.pages: list[str] = []
        self.page_width = 595.28  # A4 pt
        self.page_height = 841.89 # A4 pt

    def add_page(self, stream_content: str) -> None:
        """Aggiunge una nuova pagina con il relativo content stream."""
        self.pages.append(stream_content)

    @staticmethod
    def escape_text(text: str) -> str:
        """Converte il testo in formato compatibile PDF con encoding WinAnsi per caratteri speciali."""
        replacements = {
            "\\": "\\\\",
            "(": "\\(",
            ")": "\\)",
            "à": "\\340",
            "è": "\\350",
            "é": "\\351",
            "ì": "\\354",
            "ò": "\\362",
            "ù": "\\371",
            "À": "\\300",
            "È": "\\310",
            "É": "\\311",
            "Ì": "\\314",
            "Ò": "\\322",
            "Ù": "\\331",
            "°": "\\260",
            "•": "\\225",
            "–": "\\226",
            "—": "\\227",
            "“": "\\223",
            "”": "\\224",
            "‘": "\\221",
            "’": "\\222",
            "«": "\\253",
            "»": "\\273",
        }
        res = []
        for ch in text:
            if ch in replacements:
                res.append(replacements[ch])
            elif ord(ch) < 128:
                res.append(ch)
            else:
                res.append("?")
        return "".join(res)

    def compile(self) -> bytes:
        """Compila l'intero documento in un flusso di byte PDF 1.4 valido con tabella XRef."""
        num_pages = len(self.pages)
        objects: list[bytes] = []

        # Oggetto 1: Catalog
        catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
        objects.append(catalog)

        # Oggetto 2: Pages tree
        font_res_id = 3 + 2 * num_pages
        kids = " ".join([f"{3 + 2 * i} 0 R" for i in range(num_pages)])
        pages_obj = f"<< /Type /Pages /Kids [ {kids} ] /Count {num_pages} >>".encode("latin1")
        objects.append(pages_obj)

        for i, page_stream in enumerate(self.pages):
            content_id = 4 + 2 * i
            page_obj = (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [ 0 0 {self.page_width:.2f} {self.page_height:.2f} ] "
                f"/Resources {font_res_id} 0 R "
                f"/Contents {content_id} 0 R >>"
            ).encode("latin1")
            objects.append(page_obj)

            stream_bytes = page_stream.encode("latin1")
            stream_obj = (
                f"<< /Length {len(stream_bytes)} >>\n"
                f"stream\n"
            ).encode("latin1") + stream_bytes + b"\nendstream"
            objects.append(stream_obj)

        # Font resources object
        fonts_dict = (
            b"<<\n"
            b"  /Font <<\n"
            b"    /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\n"
            b"    /F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\n"
            b"    /F3 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>\n"
            b"    /F4 << /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>\n"
            b"    /F5 << /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold /Encoding /WinAnsiEncoding >>\n"
            b"  >>\n"
            b"  /ProcSet [ /PDF /Text ]\n"
            b">>"
        )
        objects.append(fonts_dict)

        out = bytearray()
        out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = [0]
        for i, obj_data in enumerate(objects, start=1):
            offsets.append(len(out))
            out.extend(f"{i} 0 obj\n".encode("latin1"))
            out.extend(obj_data)
            out.extend(b"\nendobj\n")

        xref_offset = len(out)
        total_objects = len(offsets)
        out.extend(f"xref\n0 {total_objects}\n".encode("latin1"))
        out.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            out.extend(f"{off:010d} 00000 n \n".encode("latin1"))

        out.extend(
            (
                f"trailer\n<< /Size {total_objects} /Root 1 0 R "
                f"/Info << /Title ({self.escape_text(self.title)}) /Author ({self.escape_text(self.author)}) >> >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode("latin1")
        )

        return bytes(out)


class PageBuilder:
    """Costruttore fluido di comandi grafici e testuali per una singola pagina PDF."""

    def __init__(self, page_num: int, total_pages: int = 10, is_cover: bool = False) -> None:
        self.page_num = page_num
        self.total_pages = total_pages
        self.is_cover = is_cover
        self.commands: list[str] = []
        self.width = 595.28
        self.height = 841.89

        if not is_cover:
            self._draw_running_header()
            self._draw_running_footer()

    def _draw_running_header(self) -> None:
        self.set_stroke_color(0.80, 0.84, 0.88)
        self.set_line_width(0.75)
        self.line(45, 804, 550, 804)
        self.text(45, 812, "AI_SHORT_GEN  //  MANUALE UTENTE UFFICIALE", font="/F2", size=8.5, color=(0.15, 0.39, 0.92))
        self.text(360, 812, "ENGLISH TTS & SPEED CONTROL v1.1", font="/F1", size=8.0, color=(0.40, 0.45, 0.52))

    def _draw_running_footer(self) -> None:
        self.set_stroke_color(0.80, 0.84, 0.88)
        self.set_line_width(0.75)
        self.line(45, 42, 550, 42)
        self.text(45, 30, "Documentazione Ufficiale - Versione 1.1 (English Voice Pipeline & Fixed Speed)", font="/F1", size=8.0, color=(0.45, 0.50, 0.58))
        page_str = f"Pagina {self.page_num} di {self.total_pages}"
        self.text(490, 30, page_str, font="/F2", size=8.0, color=(0.15, 0.39, 0.92))

    def set_fill_color(self, r: float, g: float, b: float) -> None:
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def set_stroke_color(self, r: float, g: float, b: float) -> None:
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def set_line_width(self, width: float) -> None:
        self.commands.append(f"{width:.2f} w")

    def rect(self, x: float, y: float, w: float, h: float, fill: bool = True, stroke: bool = False) -> None:
        self.commands.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re")
        if fill and stroke:
            self.commands.append("B")
        elif fill:
            self.commands.append("f")
        elif stroke:
            self.commands.append("S")

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.commands.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(self, x: float, y: float, txt: str, font: str = "/F1", size: float = 10.0, color: tuple[float, float, float] = (0.05, 0.08, 0.14)) -> None:
        esc = PDFDocument.escape_text(txt)
        r, g, b = color
        self.commands.append("BT")
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
        self.commands.append(f"{font} {size:.1f} Tf")
        self.commands.append(f"1 0 0 1 {x:.2f} {y:.2f} Tm")
        self.commands.append(f"({esc}) Tj")
        self.commands.append("ET")

    def heading(self, y: float, num_text: str, title_text: str) -> float:
        self.set_fill_color(0.145, 0.388, 0.922)
        self.rect(45, y - 4, 32, 20, fill=True)
        self.text(50, y + 2, num_text, font="/F2", size=11, color=(1, 1, 1))
        self.text(85, y + 2, title_text, font="/F2", size=13.5, color=(0.06, 0.09, 0.16))
        self.set_stroke_color(0.85, 0.88, 0.92)
        self.set_line_width(1.0)
        self.line(45, y - 10, 550, y - 10)
        return y - 28

    def subheading(self, y: float, subtitle_text: str) -> float:
        self.set_fill_color(0.545, 0.361, 0.965)
        self.rect(45, y - 2, 4, 14, fill=True)
        self.text(55, y, subtitle_text, font="/F2", size=10.5, color=(0.06, 0.09, 0.16))
        return y - 16

    def paragraph(self, y: float, lines: list[str], font: str = "/F1", size: float = 9.5, line_height: float = 13.0, color: tuple[float, float, float] = (0.20, 0.25, 0.32), x: float = 45) -> float:
        curr_y = y
        for l in lines:
            self.text(x, curr_y, l, font=font, size=size, color=color)
            curr_y -= line_height
        return curr_y - 4

    def bullet(self, y: float, title: str, desc: str = "", x: float = 50, col_w: float = 0) -> float:
        self.set_fill_color(0.145, 0.388, 0.922)
        self.rect(x, y + 2, 4, 4, fill=True)
        if desc:
            if col_w > 0:
                self.text(x + 12, y, title, font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
                self.text(x + 12 + col_w, y, desc, font="/F1", size=9.5, color=(0.25, 0.30, 0.38))
            else:
                title_str = f"{title}: "
                title_len = len(title_str) * 5.4
                self.text(x + 12, y, title_str, font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
                self.text(x + 12 + title_len, y, desc, font="/F1", size=9.5, color=(0.25, 0.30, 0.38))
        else:
            self.text(x + 12, y, title, font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
        return y - 14

    def bullet_block(self, y: float, title: str, desc: str, x: float = 50) -> float:
        self.set_fill_color(0.145, 0.388, 0.922)
        self.rect(x, y + 2, 4, 4, fill=True)
        self.text(x + 12, y, title, font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
        self.text(x + 12, y - 12, desc, font="/F1", size=8.5, color=(0.25, 0.30, 0.38))
        return y - 26


    def callout(self, y: float, title: str, text_lines: list[str], box_type: str = "info", height: float = 52.0) -> float:
        box_y = y - height + 10
        if box_type == "info":
            bg_clr = (0.937, 0.965, 1.000)
            border_clr = (0.145, 0.388, 0.922)
            title_clr = (0.118, 0.314, 0.745)
            badge = "[INFO & AGGIORNAMENTO]"
        elif box_type == "warning":
            bg_clr = (1.000, 0.984, 0.922)
            border_clr = (0.851, 0.529, 0.098)
            title_clr = (0.706, 0.400, 0.050)
            badge = "[ATTENZIONE]"
        elif box_type == "success":
            bg_clr = (0.925, 0.992, 0.961)
            border_clr = (0.063, 0.725, 0.506)
            title_clr = (0.035, 0.545, 0.380)
            badge = "[CONFIGURAZIONE VALIDATA]"
        else:
            bg_clr = (0.059, 0.090, 0.165)
            border_clr = (0.180, 0.240, 0.340)
            title_clr = (0.000, 0.941, 1.000)
            badge = "[TERMINALE / POWERSHELL]"

        self.set_fill_color(*bg_clr)
        self.rect(45, box_y, 505, height, fill=True)
        self.set_fill_color(*border_clr)
        self.rect(45, box_y, 4, height, fill=True)
        self.set_stroke_color(*border_clr)
        self.set_line_width(0.5)
        self.rect(45, box_y, 505, height, fill=False, stroke=True)

        self.text(58, box_y + height - 14, f"{badge}  {title}", font="/F2", size=9.5, color=title_clr)
        curr_y = box_y + height - 26
        for line in text_lines:
            txt_color = (0.95, 0.98, 1.0) if box_type == "code" else (0.22, 0.28, 0.36)
            txt_font = "/F4" if box_type == "code" else "/F1"
            self.text(58, curr_y, line, font=txt_font, size=8.5, color=txt_color)
            curr_y -= 11.5

        return box_y - 10

    def code_box(self, y: float, lines: list[str], height: float = 46.0) -> float:
        box_y = y - height + 8
        self.set_fill_color(0.059, 0.090, 0.165)
        self.rect(45, box_y, 505, height, fill=True)
        self.set_stroke_color(0.18, 0.24, 0.35)
        self.set_line_width(0.75)
        self.rect(45, box_y, 505, height, fill=False, stroke=True)
        self.set_fill_color(0.12, 0.16, 0.24)
        self.rect(45, box_y + height - 12, 505, 12, fill=True)
        self.text(55, box_y + height - 9, "TERMINALE POWERSHELL / BASH", font="/F5", size=7.0, color=(0.60, 0.65, 0.75))
        curr_y = box_y + height - 24
        for l in lines:
            self.text(55, curr_y, l, font="/F4", size=8.5, color=(0.20, 0.90, 0.60))
            curr_y -= 11.5
        return box_y - 10

    def render(self) -> str:
        return "\n".join(self.commands)


def build_manual_pdf() -> bytes:
    """Costruisce l'intero manuale aggiornato in 10 pagine complete."""
    doc = PDFDocument(
        title="Manuale Utente Completo - AI_short_gen Studio (English TTS)",
        author="Thomas / AI_short_gen Developer Team",
    )

    # =========================================================================
    # PAGINA 1: COPERTINA E FRONTESPIZIO
    # =========================================================================
    p1 = PageBuilder(1, is_cover=True)
    p1.set_fill_color(0.043, 0.055, 0.078)
    p1.rect(0, 520, 595.28, 321.89, fill=True)
    p1.set_fill_color(0.145, 0.388, 0.922)
    p1.rect(0, 514, 595.28, 6, fill=True)

    p1.set_fill_color(0.118, 0.106, 0.294)
    p1.rect(48, 770, 270, 22, fill=True)
    p1.set_stroke_color(0.545, 0.361, 0.965)
    p1.set_line_width(1.0)
    p1.rect(48, 770, 270, 22, fill=False, stroke=True)
    p1.text(56, 776, "DOCUMENTAZIONE UFFICIALE // ENGLISH TTS v1.1", font="/F5", size=9.0, color=(0.00, 0.94, 1.00))

    p1.text(48, 715, "AI_SHORT_GEN STUDIO", font="/F2", size=32.0, color=(1.00, 1.00, 1.00))
    p1.text(48, 680, "ENGLISH NEURAL VOICE & VIDEO SHORTS AUTOMATION", font="/F2", size=14.0, color=(0.00, 0.94, 1.00))
    p1.text(48, 646, "Manuale Utente: Pipeline Inglese & Controllo Velocita' Intuitivo", font="/F2", size=16.0, color=(0.95, 0.96, 0.98))
    p1.text(48, 626, "Guida completa alla sintesi vocale in lingua inglese con Piper TTS e pre-processing NLP.", font="/F1", size=10.5, color=(0.75, 0.80, 0.88))
    p1.text(48, 608, "Include la nuova correzione della scala di velocita' (0.5x raddoppia la lunghezza, 2.0x dimezza).", font="/F3", size=9.5, color=(0.60, 0.65, 0.75))

    p1.set_fill_color(0.95, 0.97, 1.00)
    p1.rect(48, 370, 500, 120, fill=True)
    p1.set_stroke_color(0.80, 0.85, 0.92)
    p1.set_line_width(1.0)
    p1.rect(48, 370, 500, 120, fill=False, stroke=True)

    p1.text(62, 472, "SCHEDA DI CONFIGURAZIONE AGGIORNATA", font="/F2", size=11.0, color=(0.145, 0.388, 0.922))
    p1.set_stroke_color(0.145, 0.388, 0.922)
    p1.set_line_width(1.5)
    p1.line(62, 466, 280, 466)

    p1.text(62, 446, "Lingua Primaria:", font="/F2", size=9.5, color=(0.10, 0.15, 0.22))
    p1.text(160, 446, "Inglese (English US / UK) con ottimizzatore NLP dedicato", font="/F1", size=9.5, color=(0.25, 0.30, 0.38))
    p1.text(62, 428, "Motore TTS:", font="/F2", size=9.5, color=(0.10, 0.15, 0.22))
    p1.text(160, 428, "Piper TTS Neurale (Modelli ONNX English: Lessac, Amy, Ryan, Alan)", font="/F1", size=9.5, color=(0.25, 0.30, 0.38))
    p1.text(62, 410, "Controllo Velocita':", font="/F2", size=9.5, color=(0.10, 0.15, 0.22))
    p1.text(160, 410, "Scala intuitiva corretta (0.50x allunga x2, 2.00x velocizza /2)", font="/F2", size=9.5, color=(0.04, 0.55, 0.35))
    p1.text(62, 392, "Stima Durata Audio:", font="/F2", size=9.5, color=(0.10, 0.15, 0.22))
    p1.text(160, 392, "Dinamica in tempo reale a 150 WPM (Words Per Minute inglesi)", font="/F1", size=9.5, color=(0.25, 0.30, 0.38))
    p1.text(62, 374, "Design & UX:", font="/F2", size=9.5, color=(0.10, 0.15, 0.22))
    p1.text(160, 374, "Pulsante Genera Audio in Blu Studio Sobrio (#2563EB) con dark mode", font="/F1", size=9.5, color=(0.25, 0.30, 0.38))

    p1.text(48, 340, "SOMMARIO DEI CONTENUTI", font="/F2", size=12.0, color=(0.06, 0.09, 0.16))
    p1.set_stroke_color(0.85, 0.88, 0.92)
    p1.line(48, 332, 548, 332)

    toc = [
        ("Capitolo 1", "Architettura di Sistema e Struttura Cartelle di Lavoro", "Pag. 2"),
        ("Capitolo 2", "Requisiti, Setup e Download dei Modelli Vocali Inglesi (Piper ONNX)", "Pag. 3"),
        ("Capitolo 3", "Interfaccia Cybernetic Studio & Flusso Operativo delle Storie", "Pag. 4"),
        ("Capitolo 4", "Audio Studio: Ottimizzazione Testo Inglese & Durata Dinamica (150 WPM)", "Pag. 5"),
        ("Capitolo 4 (cont.)", "Audio Studio: Correzione Scala Velocita' (0.5x = Doppia Durata, 2.0x = Meta')", "Pag. 6"),
        ("Capitolo 4 (cont.)", "Audio Studio: Generazione Asincrona (Pulsante Blu Sobrio) e Player Audio", "Pag. 7"),
        ("Capitolo 5", "Video Engine: Parametri Shorts (9:16, 1:1, 16:9) e Roadmap Video", "Pag. 8"),
        ("Capitolo 6", "Packaging e Compilazione Eseguibile Standalone (.exe) con PyInstaller", "Pag. 9"),
        ("Capitolo 7", "Guida Rapida, Risoluzione Errori (FAQ) e Checklist per Content Creator", "Pag. 10"),
    ]
    y_toc = 316
    for cap, desc, page in toc:
        p1.text(52, y_toc, cap, font="/F2", size=9.0, color=(0.145, 0.388, 0.922))
        p1.text(145, y_toc, desc, font="/F1", size=9.0, color=(0.20, 0.25, 0.32))
        p1.text(505, y_toc, page, font="/F2", size=9.0, color=(0.45, 0.50, 0.58))
        y_toc -= 17.5

    p1.callout(
        y_toc - 6,
        "Novita' di questa Versione 1.1",
        [
            "1. Pipeline NLP interamente tarata sull'inglese (abbreviazioni Mr./Dr., valute $, acronimi).",
            "2. Risolto il comportamento invertito della barra di velocita': ora 0.50x raddoppia la lunghezza",
            "   mentre 2.00x dimezza la durata, esattamente come atteso."
        ],
        box_type="info",
        height=52.0
    )
    doc.add_page(p1.render())

    # =========================================================================
    # PAGINA 2: CAPITOLO 1 - ARCHITETTURA E CARTELLE
    # =========================================================================
    p2 = PageBuilder(2)
    y2 = p2.heading(770, "1", "ARCHITETTURA DI SISTEMA E STRUTTURA CARTELLE")
    y2 = p2.subheading(y2, "1.1 Scopo del Progetto & Target Internazionale")
    y2 = p2.paragraph(y2, [
        "AI_short_gen e' progettato per i content creator che producono video corti (YouTube Shorts, TikTok, Reels)",
        "in lingua inglese. La suite integra un modulo avanzato di Natural Language Processing (NLP) che converte",
        "copioni grezzi in parlato naturale, eliminando intoppi di pronuncia e calcolando la durata esatta al secondo."
    ])
    y2 = p2.subheading(y2, "1.2 Struttura delle Directory Operative")
    folders = [
        ("models/tts/", "Directory in cui posizionare i modelli ONNX in lingua inglese (.onnx e .onnx.json)."),
        ("stories/", "Cartella per i file di testo (.txt) dei copioni in inglese non ancora elaborati."),
        ("stories/archive/", "Archivio automatico post-generazione per non perdere mai lo storico."),
        ("workspace/input/", "Filmati di sfondo (gameplay 4K, video stock, clip dinamiche)."),
        ("workspace/output/", "Cartella finale in cui risiederanno i mini-video finiti."),
        ("workspace/temp/", "Deposito temporaneo dei file audio .wav narrati generati dal motore vocale."),
    ]
    for fld, dsc in folders:
        y2 = p2.bullet(y2, fld, dsc, x=50, col_w=125)

    y2 -= 6
    y2 = p2.subheading(y2, "1.3 Clean Architecture & Modulo text_optimizer.py")
    y2 = p2.paragraph(y2, [
        "Il backend si articola in componenti modulari a responsabilita' singola:",
        "- src/text_optimizer.py : Cuore NLP per l'espansione delle abbreviazioni inglesi e stima WPM.",
        "- src/tts_engine.py : Motore di inferenza neurale Piper con gestione automatica di length_scale.",
        "- src/story_manager.py : Gestione atomica sicura dei file con timestamp anti-sovrascrittura."
    ])
    y2 = p2.callout(
        y2,
        "Privacy e Sicurezza dei Tuoi Script",
        [
            "Ogni elaborazione di testo e voce avviene rigorosamente in locale sulla tua macchina.",
            "Nessun copione o audio viene mai caricato su server cloud: zero leak, zero costi API."
        ],
        box_type="success",
        height=42.0
    )
    doc.add_page(p2.render())

    # =========================================================================
    # PAGINA 3: CAPITOLO 2 - MODELLI VOCALI INGLESI
    # =========================================================================
    p3 = PageBuilder(3)
    y3 = p3.heading(770, "2", "MODELLI VOCALI INGLESI & SETUP AMBIENTE")
    y3 = p3.subheading(y3, "2.1 Requisiti di Sistema")
    y3 = p3.paragraph(y3, [
        "- Piattaforma: Windows 10 o Windows 11 (64-bit).",
        "- Interprete: Python 3.10+ (se avviato da sorgente) oppure .exe standalone.",
        "- Memoria: 8 GB RAM (l'inferenza neurale ONNX richiede meno di 500 MB di RAM)."
    ])
    y3 = p3.subheading(y3, "2.2 Dove Scaricare i Migliori Modelli Vocali Inglesi")
    y3 = p3.paragraph(y3, [
        "I modelli Piper sono open source e gratuiti. Sono ospitati su HuggingFace nel repository ufficiale:",
        "HuggingFace Repository: https://huggingface.co/rhasspy/piper-voices",
        "Per la lingua inglese, naviga nella sezione: tree/main/en/en_US/  oppure  tree/main/en/en_GB/"
    ])

    en_voices = [
        ("en_US-lessac-medium", "Voce femminile americana limpida e professionale (news e tutorial)."),
        ("en_US-amy-medium", "Voce femminile calda ed espressiva per narrazione e storytelling."),
        ("en_US-ryan-medium", "Voce maschile americana energica per tech, gaming e video virali."),
        ("en_GB-alan-low", "Voce maschile britannica elegante per saggi storici e documentari."),
    ]
    for vn, vd in en_voices:
        y3 = p3.bullet(y3, vn, vd, x=50, col_w=140)

    y3 -= 6
    y3 = p3.callout(
        y3,
        "Ricorda la Regola dei Due File (.onnx + .onnx.json)",
        [
            "Per ogni voce vocale inglese, scarica sempre la coppia di file:",
            "  1) nome_modello.onnx         (pesi della rete neurale)",
            "  2) nome_modello.onnx.json    (configurazione dei fonemi)",
            "Posizionali in models/tts/. Se manca il file .json, Piper non potra' sintetizzare l'audio."
        ],
        box_type="warning",
        height=54.0
    )
    doc.add_page(p3.render())

    # =========================================================================
    # PAGINA 4: CAPITOLO 3 - INTERFACCIA E INDICATORI
    # =========================================================================
    p4 = PageBuilder(4)
    y4 = p4.heading(770, "3", "INTERFACCIA DESKTOP & FEEDBACK DI STATO")
    y4 = p4.subheading(y4, "3.1 Struttura della Finestra Desktop")
    y4 = p4.paragraph(y4, [
        "L'interfaccia adotta un'estetica Dark Cybernetic Studio pensata per sessioni di montaggio prolungate:",
        "- Top Bar : Mostra il badge STANDALONE v1.1, il titolo dello studio e l'indicatore diagnostico dell'engine.",
        "- Schede : Navigazione rapida tra 'AUDIO & STORY STUDIO' e 'VIDEO ENGINE'.",
        "- Footer : Barra di avanzamento asincrona e notifica testuale di stato per ogni operazione."
    ])
    y4 = p4.subheading(y4, "3.2 Gli Indicatori Dinamici di Stato")
    y4 = p4.bullet(y4, "[ONLINE] ENGINE READY", "Luce verde: modelli vocali ONNX rilevati in models/tts/. Pronto all'uso.", x=50, col_w=150)
    y4 = p4.bullet(y4, "[AVVISO] NO VOICE MODEL", "Luce rossa: nessun file .onnx in models/tts/. In attesa di modelli.", x=50, col_w=150)
    y4 -= 6
    y4 = p4.subheading(y4, "3.3 Nuovo Aspetto del Pulsante di Generazione")
    y4 = p4.paragraph(y4, [
        "Il pulsante principale 'GENERA AUDIO' e' stato rinnovato con una colorazione sobria ed elegante:",
        "- Colore Primario: Blu Studio Professionale (#2563EB) con hover scuro (#1D4ED8).",
        "- Testo: Bianco nitido (#FFFFFF) con font Segoe UI Bold (14 pt).",
        "- Risultato: Il precedente ciano neon (#00F0FF), giudicato troppo appariscente, e' stato eliminato",
        "  a favore di una tonalita' discreta ed ergonomica che riduce l'affaticamento visivo."
    ])
    y4 = p4.callout(
        y4,
        "Architettura Non-Bloccante (Background Worker)",
        [
            "La sintesi vocale gira su un thread secondario dedicato.",
            "L'interfaccia rimane sempre reattiva: puoi scorrere il testo, visionare i parametri",
            "e non vedrai mai la finestra bloccarsi con la scritta 'Non risponde'."
        ],
        box_type="info",
        height=48.0
    )
    doc.add_page(p4.render())

    # =========================================================================
    # PAGINA 5: CAPITOLO 4 (PARTE 1) - OTTIMIZZATORE INGLESE & DURATA
    # =========================================================================
    p5 = PageBuilder(5)
    y5 = p5.heading(770, "4", "AUDIO STUDIO: OTTIMIZZATORE INGLESE & DURATA (P.1)")
    y5 = p5.subheading(y5, "4.1 La Nuova Pipeline di Pre-Processing per la Lingua Inglese")
    y5 = p5.paragraph(y5, [
        "I modelli TTS spesso inciampano su abbreviazioni, simboli o formattazioni non standard.",
        "Il nuovo modulo src/text_optimizer.py esegue automaticamente le seguenti trasformazioni prima della sintesi:"
    ])
    en_rules = [
        ("Espansione Abbreviazioni", "Mr. -> Mister, Dr. -> Doctor, Prof. -> Professor, e.g. -> for example, etc. -> etcetera."),
        ("Gestione Indirizzi e Titoli", "St. Patrick -> Saint Patrick; Main St. -> Main Street (distinzione semantica automatica)."),
        ("Conversione Valute e Simboli", "$100 -> 100 dollars, $5.50 -> 5 dollars and 50 cents, 50% -> 50 percent, & -> and."),
        ("Spaziatura Acronimi", "A.I. -> A I, TTS -> T T S, NASA -> N A S A, CEO -> C E O, POV -> P O V (fonetica naturale)."),
        ("Pulizia Punteggiatura", "Rimuove parentesi (), virgolette \"\", asterischi *, hashtag # mantenendo il ritmo (. , ? ! : ;)."),
        ("Preservazione Contrazioni", "Mantiene intatte le contrazioni inglesi naturali (don't, it's, I'm, we'll, user's)."),
    ]
    for r_title, r_desc in en_rules:
        y5 = p5.bullet(y5, r_title, r_desc, x=50, col_w=150)

    y5 -= 6
    y5 = p5.subheading(y5, "4.2 Stima Dinamica della Durata Audio (150 WPM)")
    y5 = p5.paragraph(y5, [
        "In alto a destra nell'editor, il contatore caratteri e' stato sostituito con la Stima della Durata Audio:",
        "                            Durata stimata: ~01:15",
        "Il calcolo adotta la velocita' media di narrazione per la lingua inglese: 150 Parole Al Minuto (WPM):",
        "                            secondi_base = (numero_parole / 150) * 60",
        "La stima si aggiorna in tempo reale mentre digiti, incolli testo o modifichi la velocita' dello slider."
    ])
    y5 = p5.callout(
        y5,
        "Benchmark Vocale per Shorts & Reels in Inglese",
        [
            "- 50 parole inglesi  -> circa 20 secondi (ideale per ganci ultra-rapidi)",
            "- 100 parole inglesi -> circa 40 secondi (lunghezza ottimale per TikTok)",
            "- 140 parole inglesi -> circa 56 secondi (perfetto limite massimo per YouTube Shorts da 60s)"
        ],
        box_type="info",
        height=48.0
    )
    doc.add_page(p5.render())

    # =========================================================================
    # PAGINA 6: CAPITOLO 4 (PARTE 2) - CORREZIONE VELOCITÀ INTUITIVA
    # =========================================================================
    p6 = PageBuilder(6)
    y6 = p6.heading(770, "4", "CORREZIONE SCALA VELOCITA' INTUITIVA (P.2)")
    y6 = p6.subheading(y6, "4.1 La Correzione della Barra di Velocita'")
    y6 = p6.paragraph(y6, [
        "Nelle versioni precedenti, il parametro Piper TTS length_scale veniva applicato direttamente,",
        "provocando un comportamento al contrario: impostare 0.5x velocizzava al doppio anziche' rallentare.",
        "Il sistema e' stato completamente corretto per rispettare la percezione naturale dell'utente:"
    ])

    speed_cases = [
        ("Velocita' 1.00x (Standard Naturale)", "Riproduzione a velocita' standard naturale. (length_scale = 1.0)"),
        ("Velocita' 0.50x (Slow / Meta' Velocita')", "Il parlato rallenta al 50%: la durata audio RADDOPPIA (x2). (length_scale = 2.0)"),
        ("Velocita' 2.00x (Fast / Doppia Velocita')", "Il parlato accelera al doppio: la durata audio SI DIMEZZA (/2). (length_scale = 0.5)"),
        ("Velocita' 1.25x (Dinamica per Shorts)", "Il parlato e' 25% piu' rapido: ritmo serrato ideale per TikTok e Reels. (length_scale = 0.8)"),
    ]
    for sc_t, sc_d in speed_cases:
        y6 = p6.bullet_block(y6, sc_t, sc_d, x=50)

    y6 -= 4
    y6 = p6.subheading(y6, "4.2 Formula Tecnica di Conversione")
    y6 = p6.paragraph(y6, [
        "Il backend esegue l'inversione esatta richiesta dal motore neurale Piper:",
        "                            length_scale = 1.0 / speed",
        "E la stima della durata nella GUI applica la stessa formula coerente:",
        "                            durata_effettiva = durata_base / speed",
        "Di conseguenza, muovendo lo slider a 0.50x vedrai la durata stimata raddoppiare all'istante!"
    ])

    y6 = p6.subheading(y6, "4.3 Altri Parametri Avanzati")
    y6 = p6.paragraph(y6, [
        "- Espressivita' (noise_scale, default 0.67): Varianza tonale della voce (0.50 per news, 0.75 per drama).",
        "- Durata Fonemi (noise_w, default 0.80): Naturalezza nella transizione tra consonanti e vocali.",
        "- Archiviazione Automatica: Sposta il copione .txt in stories/archive/ al termine della sintesi."
    ])

    y6 = p6.callout(
        y6,
        "Allineamento Perfetto tra GUI e Sintesi",
        [
            "Sia la stima visualizzata a schermo sia l'audio WAV generato su disco riflettono fedelmente",
            "la velocita' selezionata. Con 0.50x l'audio generato sara' esattamente due volte piu' lungo!"
        ],
        box_type="success",
        height=44.0
    )
    doc.add_page(p6.render())

    # =========================================================================
    # PAGINA 7: CAPITOLO 4 (PARTE 3) - GENERAZIONE E PLAYER
    # =========================================================================
    p7 = PageBuilder(7)
    y7 = p7.heading(770, "4", "GENERAZIONE AUDIO, MONITORAGGIO E PLAYER (P.3)")
    y7 = p7.subheading(y7, "4.1 Flusso di Sintesi con il Nuovo Pulsante Blu")
    y7 = p7.paragraph(y7, [
        "Quando il copione in inglese e' pronto, fai clic sul pulsante blu:",
        "                            [>] GENERA AUDIO  (Colore Blu Studio #2563EB)",
        "Il flusso automatico esegue:",
        "1. Validazione del testo: impedisce generazioni a vuoto con editor vuoto.",
        "2. Ottimizzazione NLP inglese: ripulisce abbreviazioni, simboli e punteggiatura.",
        "3. Calcolo parametri: applica length_scale = 1.0 / speed ed avvia il thread di inferenza.",
        "4. Durante la lavorazione: il pulsante mostra 'GENERAZIONE IN CORSO...' e si disabilita.",
        "5. Al termine: il pulsante torna al colore blu sobrio ed emette l'avviso di successo."
    ])

    y7 = p7.subheading(y7, "4.2 Strumenti di Ascolto e Gestione File")
    y7 = p7.bullet(y7, "Pulsante '[>] Ascolta'", "Riproduce il file WAV sintetizzato. Cliccando diventa '[X] Ferma'.", x=50, col_w=150)
    y7 = p7.bullet(y7, "Pulsante '[DIR] Apri Cartella'", "Apre Esplora Risorse puntando direttamente a 'workspace/temp/'.", x=50, col_w=150)
    y7 -= 8


    y7 = p7.callout(
        y7,
        "Denominazione File di Output",
        [
            "I file generati seguono lo schema: workspace/temp/[nome_storia]_[timestamp].wav",
            "Esempio pratico: workspace/temp/english_script_20261005_183015.wav",
            "Nessuna sovrascrittura accidentale tra diverse prove di voce o velocita'."
        ],
        box_type="info",
        height=48.0
    )
    doc.add_page(p7.render())

    # =========================================================================
    # PAGINA 8: CAPITOLO 5 - VIDEO ENGINE
    # =========================================================================
    p8 = PageBuilder(8)
    y8 = p8.heading(770, "5", "VIDEO ENGINE: PIPELINE PER SHORTS & REELS")
    y8 = p8.subheading(y8, "5.1 La Scheda 'VIDEO ENGINE'")
    y8 = p8.paragraph(y8, [
        "La seconda scheda dell'applicazione e' dedicata all'assemblaggio dei mini-video verticali:",
        "- Input Video: seleziona filmati lunghi posizionati in workspace/input/.",
        "- Input Audio: seleziona la traccia WAV narrata in inglese creata nella Scheda 1.",
        "- Slider Durata Massima: impostabile da 15s a 180s (standard consigliato 55-60s per Shorts)."
    ])
    y8 = p8.subheading(y8, "5.2 Formati Risoluzione Disponibili")
    y8 = p8.bullet(y8, "9:16 Verticale (1080x1920)", "Formato per YouTube Shorts, Instagram Reels e TikTok.", x=50, col_w=170)
    y8 = p8.bullet(y8, "1:1 Quadrato (1080x1080)", "Formato per post feed tradizionali di Instagram e LinkedIn.", x=50, col_w=170)
    y8 = p8.bullet(y8, "16:9 Orizzontale (1920x1080)", "Formato widescreen per YouTube classico e desktop.", x=50, col_w=170)
    y8 -= 6

    y8 = p8.subheading(y8, "5.3 Moduli Backend PySceneDetect & MoviePy")
    y8 = p8.paragraph(y8, [
        "- src/video_cutter.py : Rileva i cambi di inquadratura e ritaglia automaticamente le clip piu' dinamiche.",
        "- src/editor.py : Sincronizza i tagli video con la voce narrata ed esporta in workspace/output/."
    ])
    y8 = p8.callout(
        y8,
        "Predisposizione Architetturale",
        [
            "La dashboard video memorizza i tuoi parametri preferiti pronti per l'esecuzione della pipeline.",
            "Puoi usare subito le tracce audio WAV con Premiere, DaVinci Resolve o CapCut."
        ],
        box_type="info",
        height=44.0
    )
    doc.add_page(p8.render())

    # =========================================================================
    # PAGINA 9: CAPITOLO 6 - PACKAGING STANDALONE (.EXE)
    # =========================================================================
    p9 = PageBuilder(9)
    y9 = p9.heading(770, "6", "PACKAGING STANDALONE (.EXE) CON PYINSTALLER")
    y9 = p9.subheading(y9, "6.1 Compilazione Semplice Senza Python")
    y9 = p9.paragraph(y9, [
        "Puoi compilare AI_short_gen in un eseguibile Windows autonomo che non richiede l'installazione di Python",
        "ne' delle dipendenze sul PC finale. L'utente dovra' solo fare doppio clic su AI_short_gen.exe."
    ])
    y9 = p9.code_box(y9, [
        "# Modalita' Cartella Distribuibile (Consigliata per avvio istantaneo):",
        "python build_exe.py",
        "",
        "# Modalita' Singolo File .exe compresso:",
        "python build_exe.py --onefile"
    ], height=76.0)

    y9 = p9.subheading(y9, "6.2 Predisposizione Automatica dell'Ambiente")
    y9 = p9.paragraph(y9, [
        "Lo script build_exe.py automatizza l'inclusione di CustomTkinter, crea la cartella dist/AI_short_gen/",
        "e vi genera accanto tutte le directory operative (models/tts/, stories/, workspace/)."
    ])
    y9 = p9.callout(
        y9,
        "Condivisione con Collaboratori",
        [
            "Ti basta comprimere la cartella dist/AI_short_gen/ in un archivio .ZIP e condividerla:",
            "funzionera' immediatamente su qualsiasi computer con Windows 10 o Windows 11 a 64-bit."
        ],
        box_type="success",
        height=44.0
    )
    doc.add_page(p9.render())

    # =========================================================================
    # PAGINA 10: CAPITOLO 7 - FAQ & BEST PRACTICES
    # =========================================================================
    p10 = PageBuilder(10)
    y10 = p10.heading(770, "7", "FAQ, RISOLUZIONE PROBLEMI & BEST PRACTICES")
    y10 = p10.subheading(y10, "7.1 Risoluzione delle Casistiche Frequenti")
    faqs = [
        ("Come faccio a usare voci in inglese?", [
            "Scarica i file .onnx e .onnx.json da HuggingFace (en/en_US/) e salvali in models/tts/.",
            "Premi il pulsante circolare [Ricarica] accanto al selettore per caricare la voce inglese."
        ]),
        ("La barra di velocita' allunga o accorcia il parlato?", [
            "Con la nuova correzione: 0.50x parla piu' lentamente e RADDOPPIA la durata audio;",
            "2.00x parla al doppio della velocita' e DIMEZZA la durata complessiva."
        ]),
        ("Perche' il contatore mostra 'Durata stimata' invece dei caratteri?", [
            "La durata in tempo reale (calcolata su 150 WPM) e' molto piu' utile per creare Shorts di 60s",
            "rispetto a un semplice numero di caratteri grezzi."
        ]),
        ("Come gestisce l'ottimizzatore le abbreviazioni in inglese?", [
            "Espande automaticamente 'Dr.' in 'Doctor', 'Mr.' in 'Mister', '$100' in '100 dollars',",
            "'e.g.' in 'for example', garantendo una lettura fluida senza pause errate sui punti."
        ]),
    ]
    for q_t, q_lines in faqs:
        y10 = p10.bullet(y10, q_t, "", x=48)
        y10 = p10.paragraph(y10, q_lines, size=8.5, line_height=11.5, x=60)
        y10 -= 2

    y10 = p10.subheading(y10, "7.2 Checklist Giornaliera per la Produzione di Shorts")
    steps = [
        ("Passo 1: Inserisci il Copione Inglese", "Scrivi o carica il file .txt in lingua inglese nell'editor."),
        ("Passo 2: Controlla la Durata", "Verifica che 'Durata stimata' sia inferiore a 00:58 per YouTube Shorts."),
        ("Passo 3: Calibra la Velocita'", "Imposta 1.10x o 1.25x per ritmo energico, oppure 0.85x per narrazioni rilassanti."),
        ("Passo 4: Premi Genera Audio", "Clicca sul pulsante blu ed attendi la notifica di completamento."),
        ("Passo 5: Ascolta l'Anteprima", "Premi [>] Ascolta e poi [DIR] Apri Cartella per prelevare il file .wav."),
    ]
    for st_n, st_d in steps:
        y10 = p10.bullet_block(y10, st_n, st_d, x=48)

    y10 -= 2
    y10 = p10.callout(
        y10,
        "Tutto Pronto per Creare Contenuti Internazionali",
        [
            "La combinazione tra pre-processing inglese, voci neurali Piper e controllo intuitivo della velocita'",
            "ti permette di produrre narrazioni vocali professionali in pochi clic."
        ],
        box_type="info",
        height=42.0
    )
    doc.add_page(p10.render())


    return doc.compile()


def main() -> None:
    """Funzione principale: compila il manuale PDF e lo salva nei percorsi corretti."""
    print("=" * 65)
    print(" [GENERATORE PDF] Compilazione Manuale Utente AI_short_gen (English Edition)...")
    print("=" * 65)

    pdf_bytes = build_manual_pdf()

    project_root = Path(__file__).resolve().parent
    output_pdf_path = project_root / "MANUALE_UTENTE_AI_SHORT_GEN.pdf"

    output_pdf_path.write_bytes(pdf_bytes)
    print(f"[OK] File PDF generato con successo:")
    print(f"    Percorso: {output_pdf_path}")
    print(f"    Dimensione: {len(pdf_bytes) / 1024:.2f} KB (10 Pagine complete)")
    print("=" * 65)

    alt_workspace = Path(r"C:\Users\thomm\Desktop\AI shorts gen")
    if alt_workspace.exists():
        alt_pdf = alt_workspace / "MANUALE_UTENTE_AI_SHORT_GEN.pdf"
        alt_pdf.write_bytes(pdf_bytes)
        print(f"[OK] Copia sincronizzata in: {alt_pdf}")


if __name__ == "__main__":
    main()
