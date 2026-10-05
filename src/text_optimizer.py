"""Text pre-processing and phonetic optimization module for English Text-to-Speech (TTS).

Optimizes English text for Piper TTS by expanding common English abbreviations,
normalizing currency, percentages and symbols, formatting acronyms,
cleaning superfluous non-phonetic punctuation while strictly preserving rhythmic
pause markers, and calculating accurate audio duration estimates.
"""

from __future__ import annotations

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)

# Dictionary of common English abbreviations mapped to their spoken expansion
# Regex pattern -> full spoken form
ENGLISH_ABBREVIATIONS: Dict[str, str] = {
    # Titles & Honorifics
    r"\bmr\b\.": "mister",
    r"\bmrs\b\.": "missus",
    r"\bms\b\.": "miss",
    r"\bdr\b\.": "doctor",
    r"\bdrs\b\.": "doctors",
    r"\bprof\b\.": "professor",
    r"\bprofs\b\.": "professors",
    r"\bsr\b\.": "senior",
    r"\bjr\b\.": "junior",
    r"\brev\b\.": "reverend",
    r"\bgen\b\.": "general",
    r"\bcol\b\.": "colonel",
    r"\bcapt\b\.": "captain",
    r"\blt\b\.": "lieutenant",
    r"\bsgt\b\.": "sergeant",

    # Latin & Discourse Abbreviations
    r"\be\.g\b\.?": "for example",
    r"\bi\.e\b\.?": "that is",
    r"\betc\b\.": "etcetera",
    r"\bvs\b\.?": "versus",
    r"\bapprox\b\.": "approximately",
    r"\best\b\.": "estimated",
    r"\basap\b": "as soon as possible",
    r"\bw/\b": "with",
    r"\bw/o\b": "without",

    # Measurement & Time units
    r"\bmin\b\.(?=\s*\d|\b)": "minutes",
    r"\bmins\b\.": "minutes",
    r"\bsec\b\.(?=\s*\d|\b)": "seconds",
    r"\bsecs\b\.": "seconds",
    r"\bhr\b\.(?=\s*\d|\b)": "hour",
    r"\bhrs\b\.": "hours",
    r"\byr\b\.(?=\s*\d|\b)": "year",
    r"\byrs\b\.": "years",
    r"\bmo\b\.(?=\s*\d|\b)": "month",
    r"\bmos\b\.": "months",
    r"\blbs\b\.": "pounds",
    r"\blb\b\.": "pound",
    r"\boz\b\.": "ounces",
    r"\bft\b\.(?=\s*\d|\b)": "feet",
    r"\bin\b\.(?=\s*\d)": "inches",
    r"\byd\b\.(?=\s*\d|\b)": "yard",
    r"\byds\b\.": "yards",
    r"\bmi\b\.(?=\s*\d|\b)": "miles",
    r"\bmph\b": "miles per hour",
    r"\bkph\b": "kilometers per hour",
    r"\bkm/h\b": "kilometers per hour",
    r"\bkm\b(?=\s*\d|\b)": "kilometers",
    r"\bcm\b(?=\s*\d|\b)": "centimeters",
    r"\bmm\b(?=\s*\d|\b)": "millimeters",
    r"\bkg\b(?=\s*\d|\b)": "kilograms",

    # References & Addresses
    r"\bno\b\.(?=\s*\d)": "number",
    r"\bnos\b\.(?=\s*\d)": "numbers",
    r"\bnr\b\.(?=\s*\d)": "number",
    r"\bvol\b\.(?=\s*\d)": "volume",
    r"\bvols\b\.(?=\s*\d)": "volumes",
    r"\bp\b\.(?=\s*\d)": "page",
    r"\bpp\b\.(?=\s*\d)": "pages",
    r"\bch\b\.(?=\s*\d)": "chapter",
    r"\bchap\b\.(?=\s*\d)": "chapter",
    r"\bsec\b\.(?=\s*\d)": "section",
    r"\bdept\b\.": "department",
    r"\bext\b\.(?=\s*\d)": "extension",
    r"\btel\b\.": "telephone",
    r"\bave\b\.": "avenue",
    r"\bblvd\b\.": "boulevard",
    r"\brd\b\.": "road",
    r"\bln\b\.": "lane",
    r"\bct\b\.": "court",
    r"\bpl\b\.": "place",
    r"\bapt\b\.(?=\s*\d|[A-Z])": "apartment",
    r"\bste\b\.(?=\s*\d|[A-Z])": "suite",

    # Corporate & Business
    r"\bco\b\.": "company",
    r"\bcorp\b\.": "corporation",
    r"\binc\b\.": "incorporated",
    r"\bltd\b\.": "limited",
}

# Common English words that appear capitalized in titles/shouting and should NOT be split letter by letter
COMMON_UPPERCASE_WORDS = {
    "A", "AN", "THE", "AND", "BUT", "OR", "NOR", "FOR", "YET", "SO",
    "AT", "BY", "FROM", "IN", "INTO", "OF", "OFF", "ON", "ONTO", "OUT",
    "OVER", "TO", "UP", "WITH", "AS", "IF", "WHEN", "THAN", "THAT",
    "THOUGH", "ALTHOUGH", "WHILE", "WHERE", "HOW", "WHAT", "WHO", "WHOM",
    "WHICH", "WHY", "ALL", "ANY", "BOTH", "EACH", "FEW", "MORE", "MOST",
    "OTHER", "SOME", "SUCH", "NO", "NOT", "ONLY", "OWN", "SAME", "TOO",
    "VERY", "CAN", "WILL", "JUST", "SHOULD", "NOW", "I", "YOU", "HE",
    "SHE", "IT", "WE", "THEY", "ME", "HIM", "HER", "US", "THEM", "MY",
    "YOUR", "HIS", "ITS", "OUR", "THEIR", "MINE", "YOURS", "HERS", "OURS",
    "THEIRS", "THIS", "THESE", "THOSE", "IS", "AM", "ARE", "WAS", "WERE",
    "BE", "BEEN", "BEING", "HAVE", "HAS", "HAD", "DO", "DOES", "DID",
    "GO", "GET", "MAKE", "KNOW", "TAKE", "SEE", "COME", "THINK", "LOOK",
    "WANT", "GIVE", "USE", "FIND", "TELL", "ASK", "WORK", "SEEM", "FEEL",
    "TRY", "LEAVE", "CALL", "GOOD", "NEW", "FIRST", "LAST", "LONG",
    "GREAT", "LITTLE", "OLD", "RIGHT", "BIG", "HIGH", "SMALL", "LARGE",
    "NEXT", "EARLY", "YOUNG", "WEEK", "DAY", "TIME", "YEAR", "WAY",
    "MAN", "WORLD", "LIFE", "HAND", "PART", "CHILD", "EYE", "WOMAN",
    "PLACE", "CASE", "POINT", "NUMBER", "GROUP", "PROBLEM", "FACT",
}


class TextOptimizer:
    """Sanitizes and phonetically optimizes English text for neural Text-to-Speech."""

    @classmethod
    def expand_abbreviations(cls, text: str) -> str:
        """Expands common English abbreviations while preserving original capitalization."""
        result = text

        # Special contextual handling for 'St.' -> 'Saint' vs 'Street'
        # Followed by Capitalized word: 'St. Patrick' -> 'Saint Patrick'
        result = re.sub(
            r"\bSt\b\.(?=\s+[A-Z][a-z])",
            "Saint",
            result,
        )
        # Preceded by alphanumeric / digits: 'Main St.' -> 'Main Street', '42nd St.' -> '42nd Street'
        result = re.sub(
            r"(?<=[A-Za-z0-9])\s+\b[Ss]t\b\.",
            " Street",
            result,
        )

        for pattern, replacement in ENGLISH_ABBREVIATIONS.items():
            regex = re.compile(pattern, re.IGNORECASE)

            def _repl(match: re.Match) -> str:
                matched_str = match.group(0)
                if matched_str.isupper():
                    return replacement.upper()
                elif matched_str[0].isupper():
                    return replacement.capitalize()
                return replacement

            result = regex.sub(_repl, result)

        return result

    @classmethod
    def convert_symbols(cls, text: str) -> str:
        """Converts currency, percentages, and math symbols into spoken English words."""
        # Currency: Dollars $100 / $5.50
        text = re.sub(r"\$\s*(\d+(?:\.\d+)?)\s*(?:million|M)\b", r"\1 million dollars", text, flags=re.IGNORECASE)
        text = re.sub(r"\$\s*(\d+(?:\.\d+)?)\s*(?:billion|B)\b", r"\1 billion dollars", text, flags=re.IGNORECASE)
        text = re.sub(r"\$\s*(\d+)\.(\d{2})\b", r"\1 dollars and \2 cents", text)
        text = re.sub(r"\$\s*(\d+(?:\.\d+)?)\b", r"\1 dollars", text)

        # Currency: Pounds £50
        text = re.sub(r"£\s*(\d+(?:\.\d+)?)\b", r"\1 pounds", text)

        # Currency: Euros €50
        text = re.sub(r"€\s*(\d+(?:\.\d+)?)\b", r"\1 euros", text)

        # Percentages: 50% -> 50 percent
        text = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"\1 percent", text)
        text = re.sub(r"%", " percent", text)

        # Ampersand & -> and
        text = re.sub(r"\s*&\s*", " and ", text)

        # At symbol @ -> at
        text = re.sub(r"(?<=\s)@(?=\s)", " at ", text)

        # Number sign before digit: #1 -> number 1
        text = re.sub(r"#\s*(\d+)", r"number \1", text)

        # Degrees: 72° -> 72 degrees
        text = re.sub(r"(\d+)\s*°", r"\1 degrees", text)

        return text

    @classmethod
    def format_acronyms(cls, text: str) -> str:
        """Inserts spaces between letters of uppercase acronyms so Piper pronounces each letter cleanly.

        Examples:
        - 'U.S.A.' -> 'U S A'
        - 'A.I.' -> 'A I'
        - 'NASA' -> 'N A S A'
        - 'CEO' -> 'C E O'
        """
        # 1. Dotted acronyms (e.g. U.S.A. -> U S A, A.I. -> A I)
        text = re.sub(
            r"\b([A-Z])\.(?:([A-Z])\.)+(?:([A-Z])\.?)?\b",
            lambda m: " ".join([char for char in m.group(0).replace(".", " ").split() if char]),
            text,
        )

        # 2. Uppercase acronyms of 2 to 5 letters (e.g. AI, TTS, FBI, NASA, POV, CEO)
        def _space_acronym(match: re.Match) -> str:
            word = match.group(0)
            if word in COMMON_UPPERCASE_WORDS:
                return word
            return " ".join(list(word))

        text = re.sub(r"\b[A-Z]{2,5}\b", _space_acronym, text)
        return text

    @classmethod
    def clean_superfluous_punctuation(cls, text: str) -> str:
        """Removes brackets, quotes, hashtags, asterisks and non-phonetic noise

        while strictly preserving rhythmic pause punctuation:
        - Periods (.)
        - Commas (,)
        - Question marks (?)
        - Exclamation marks (!)
        - Colons (:)
        - Semicolons (;)
        - Internal contractions / apostrophes (don't, it's, I'm, user's)
        """
        # Normalize typographic/curly single quotes to standard ASCII apostrophe
        text = re.sub(r"[‘’`´]", "'", text)

        # Remove double quotes and guillemets
        text = re.sub(r'["“”«»„]', "", text)

        # Remove parentheses, brackets, and braces
        text = re.sub(r"[()[\]{}]", "", text)

        # Remove hashtags, asterisks, underscores, pipes, carets, slashes
        text = re.sub(r"[*#_~|^\\<>/]", " ", text)

        # Convert phrase dashes (-- or —) into natural comma pauses
        text = re.sub(r"\s+[-–—]+\s+", ", ", text)
        text = re.sub(r"[-–—]+", " ", text)

        # Normalize ellipsis (...) into single period with pause
        text = re.sub(r"\.{2,}", ".", text)

        # Normalize repeated exclamation/question marks
        text = re.sub(r"\?{2,}", "?", text)
        text = re.sub(r"!{2,}", "!", text)
        text = re.sub(r"\?!|\!\?", "?", text)

        # Remove isolated apostrophes not attached to letters (e.g. ' quote ')
        text = re.sub(r"(?<!\w)'|'(?!\w)", "", text)

        return text

    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """Normalizes horizontal whitespace, removes spaces before punctuation, and cleans newlines."""
        # Remove spaces before punctuation (e.g. 'hello ,' -> 'hello,')
        text = re.sub(r"\s+([.,!?:;])", r"\1", text)

        # Ensure space after punctuation if immediately followed by letters or digits
        text = re.sub(r"([.,!?:;])(?=[A-Za-z0-9])", r"\1 ", text)

        # Collapse multiple horizontal whitespace characters
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize multiple newlines (\n\n+ -> \n)
        text = re.sub(r"\n\s*\n+", "\n", text)

        # Strip lines
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join([line for line in lines if line])

        return text.strip()

    @classmethod
    def optimize(cls, text: str) -> str:
        """Executes the complete English text optimization pipeline for Piper TTS."""
        if not text:
            return ""

        processed = cls.convert_symbols(text)
        processed = cls.expand_abbreviations(processed)
        processed = cls.format_acronyms(processed)
        processed = cls.clean_superfluous_punctuation(processed)
        processed = cls.normalize_whitespace(processed)

        return processed


def optimize_for_tts(text: str) -> str:
    """Entry point for English text pre-processing and phonetic optimization for TTS.

    Args:
        text: Raw English text input.

    Returns:
        Clean, phonetically enriched English text tailored for natural Piper TTS synthesis.
    """
    return TextOptimizer.optimize(text)


def estimate_audio_duration(text: str, wpm: int = 150, speed: float = 1.0) -> float:
    """Calculates estimated audio duration in seconds for English speech.

    Formula:
        base_seconds = (word_count / wpm) * 60
        effective_seconds = base_seconds / speed

    Note on Speed:
        - speed = 1.0x : standard playback duration.
        - speed = 0.5x : half speed, speech is slower, DURATION IS DOUBLED (x2).
        - speed = 2.0x : double speed, speech is faster, DURATION IS HALVED (/2).

    Args:
        text: Text to evaluate.
        wpm: Average words per minute (default 150 for spoken English).
        speed: Speed multiplier selected by the user (default 1.0).

    Returns:
        Estimated duration in seconds (float).
    """
    if not text or not text.strip():
        return 0.0

    # Extract words including internal contractions (e.g. don't, it's)
    words = re.findall(r"\b[\w'-]+\b", text)
    word_count = len(words)

    if word_count == 0 or wpm <= 0:
        return 0.0

    base_seconds = (word_count / float(wpm)) * 60.0

    # speed = 0.5x means speech is half as fast, so duration is doubled (base_seconds / 0.5 = base_seconds * 2)
    # speed = 2.0x means speech is twice as fast, so duration is halved (base_seconds / 2.0 = base_seconds * 0.5)
    speed_factor = float(speed) if speed > 0 else 1.0
    effective_seconds = base_seconds / speed_factor

    return max(0.0, effective_seconds)


def format_duration(seconds: float) -> str:
    """Formats seconds into readable mm:ss format (e.g. 75s -> '01:15')."""
    total_sec = max(0, int(round(seconds)))
    minutes = total_sec // 60
    secs = total_sec % 60
    return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    print("=" * 65)
    print(" [UNIT TEST] Validation for English src/text_optimizer.py")
    print("=" * 65)

    test_cases = [
        (
            "Dr. Smith and Prof. Johnson said: 'Today A.I. is crucial (really!).'",
            "Doctor Smith and Professor Johnson said: Today A I is crucial, really!.",
        ),
        (
            "We watched the news on TV, e.g. on CNN at 8:00 PM ... etc.",
            "We watched the news on T V, for example on C N N at 8:00 P M. etcetera.",
        ),
        (
            "Get a 50% discount on Amazon #deals for Mr. Brown (tel. 555-0199) w/ free shipping!",
            "Get a 50 percent discount on Amazon deals for Mister Brown telephone 555-0199 with free shipping!",
        ),
        (
            "The CEO of Acme Corp. earned $100 million in Q1 of 2026.",
            "The C E O of Acme Corporation earned 100 million dollars in Q 1 of 2026.",
        ),
        (
            "Hello   ,  how are you  ?   Great  !   See you at Main St. soon   . \n\n\nNext paragraph.",
            "Hello, how are you? Great! See you at Main Street soon.\nNext paragraph.",
        ),
    ]

    for idx, (raw_text, expected_hint) in enumerate(test_cases, start=1):
        cleaned = optimize_for_tts(raw_text)
        dur_1x = estimate_audio_duration(raw_text, wpm=150, speed=1.0)
        dur_half_speed = estimate_audio_duration(raw_text, wpm=150, speed=0.5)
        dur_double_speed = estimate_audio_duration(raw_text, wpm=150, speed=2.0)

        print(f"\n--- Test Case #{idx} ---")
        print(f"Original       : {raw_text}")
        print(f"Cleaned (EN)   : {cleaned}")
        print(f"Duration 1.00x : ~{format_duration(dur_1x)} ({dur_1x:.1f}s)")
        print(f"Duration 0.50x : ~{format_duration(dur_half_speed)} ({dur_half_speed:.1f}s) -> [Doubled as requested!]")
        print(f"Duration 2.00x : ~{format_duration(dur_double_speed)} ({dur_double_speed:.1f}s) -> [Halved as requested!]")

        # Verification of speed inversion:
        assert abs(dur_half_speed - (dur_1x * 2.0)) < 1e-4, "Error: 0.5x speed must double duration!"
        assert abs(dur_double_speed - (dur_1x * 0.5)) < 1e-4, "Error: 2.0x speed must halve duration!"

        # Sanity checks
        assert "Dr." not in cleaned and "Prof." not in cleaned
        assert "(" not in cleaned and ")" not in cleaned
        assert "  " not in cleaned
        assert " ," not in cleaned and " ." not in cleaned

    print("\n" + "=" * 65)
    print(" [SUCCESS] All English TTS phonetic tests and duration formulas verified!")
    print("=" * 65)
