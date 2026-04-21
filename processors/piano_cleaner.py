"""
Piano floor cleaner.

Usage:
    df_pure['piano_clean'] = clean_piano(df_pure['piano'])
    audit_piano(df_pure['piano'])                   # distribution overview
    audit_piano(df_pure['piano'], show_parsed=True) # debug token resolution

To extend to a new dataset: run audit_piano() first, then add any
unresolved values to WORD_TO_FLOOR and re-run the cell.
"""
import pandas as pd
import re
from typing import Optional


#    Vocabulary
# Maps every known token (lowercase) to a floor integer.
# Convention: 0 = ground, negative = basement, positive = above ground.
# Add new entries here whenever audit_piano() surfaces unknowns you want to rescue.

WORD_TO_FLOOR: dict[str, int] = {

    # Ground floor
    "t": 0, "terra": 0, "terreno": 0, "terr": 0, "terr.": 0,
    "pt": 0, "p.t": 0, "p.t.": 0, "p t": 0,
    "piano terra": 0, "piano terreno": 0,
    "0": 0, "00": 0, "p0": 0, "p00": 0, "p.0": 0,
    "rialzato": 0, "rialz.": 0, "rialz": 0,
    "terra rialz.": 0, "terra rialza": 0, "t rialzato": 0,
    "r": 0,       # rialzato abbreviation
    "attico": 0,  # treated as ground-equivalent when alone

    # Basement / below grade
    "s":   -1, "s1": -1, "s 1": -1, "s.1": -1, "s1.": -1,
    "ps":  -1, "ps1": -1, "p.s.1": -1, "psi": -1,
    "s2":  -2, "s 2": -2, "s.2": -2, "ps2": -2, "2st": -2, "st": -1,
    "s3":  -3, "s 3": -3, "s.3": -3,
    "s4":  -4, "s 4": -4, "s iv": -4,
    "-1":  -1, "-2": -2, "-3": -3,
    "seminterrato": -1, "sem": -1, "sem.": -1,
    "interrato": -1, "sottosuolo": -1,
    "si": -1, "s i": -1,
    "sottostrada": -1,
    "primo sottostrada": -1, "piano primo sottostrada": -1,
    "int": -1,    # interrato abbreviation

    # Upper floors — numeric
    "1": 1, "p1": 1, "p.1": 1, "p 1": 1, "1p": 1, "01": 1,
    "2": 2, "p2": 2, "p.2": 2, "p 2": 2, "2p": 2,
    "3": 3, "p3": 3, "p.3": 3, "p 3": 3, "3p": 3,
    "4": 4, "p4": 4, "p.4": 4, "p 4": 4,
    "5": 5, "p5": 5, "p 5": 5,
    "6": 6, "p6": 6,
    "7": 7, "p7": 7,
    "8": 8, "p8": 8,
    "9": 9, "p9": 9,

    # Upper floors — Italian words
    "primo": 1, "secondo": 2, "terzo": 3, "quarto": 4, "quinto": 5,
    "sesto": 6, "settimo": 7, "ottavo": 8, "nono": 9,
    "piano primo": 1, "piano secondo": 2, "piano terzo": 3,
    "piani primo": 1,
    "p. primo": 1, "p.primo": 1, "sottotetto": 5,

    # Upper floors — Roman numerals
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5,
    "vi": 6, "vii": 7, "viii": 8,

    # Typos
    "pimo": 1, "prim0": 1, "primo(rialz)": 1,
    "t3ezo": 3, "terrzo": 3, "iiiº": 3,
    "sezondo": 2, "sec": 2,
    "1st": 1, "1s": 1,
    "i°": 1, "pi": 1,
}

# Junk tokens — resolve to nothing
# Pure separators or semantically empty strings that should be silently dropped.
_JUNK: set[str] = {
    "-", "/", ".", "*", "---", "--",
    "na", "n/a", "globale", "cielo terra",
    "scala", "scala c", "b",
    "e",      # Italian "and" used between floor names
    "piano",  # bare "piano" with no number
    "pin",    # garbled prefix
}

# Patterns that mark a whole value as unrecoverable:
# pure numeric IDs (44958), strings of only punctuation/symbols.
_GARBAGE_RE = re.compile(r"^\d{4,}$|^[^a-z0-9]+$")

# Ordinal degree signs: 1° → 1, 2º → 2
_ORDINAL_RE = re.compile(r"(\d+)\s*[°º]")


# Normalization

def _preprocess(raw: str) -> str:
    s = raw.lower().strip()
    s = _ORDINAL_RE.sub(lambda m: m.group(1), s)   # strip ordinal °/º
    s = re.sub(r"[,;|+_\\]", " ", s)               # separators → space
    s = re.sub(r"(?<=\S)/(?=\S)", " ", s)          # T/1 → T 1
    s = re.sub(r"\s*-\s*", " ", s)                 # T-1 → T 1
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokenise(s: str) -> list[str]:
    return [t for t in s.split() if t]


def _resolve_token(token: str) -> Optional[int]:
    """Return a floor integer for one token, or None if unrecognised/junk."""
    if token in _JUNK:
        return None
    if token in WORD_TO_FLOOR:
        return WORD_TO_FLOOR[token]
    try:                        # handles arbitrary integers (high floors, depths)
        return int(token)
    except ValueError:
        return None


def _parse(raw: str) -> Optional[frozenset]:
    """
    Parse one raw value into a frozenset of floor integers.
    Returns None if nothing meaningful could be extracted.
    """
    pre = _preprocess(raw)
    if not pre or _GARBAGE_RE.match(pre):
        return None

    # Try the full preprocessed string first — catches multi-word vocab entries
    # like "piano terra" or "primo sottostrada" before splitting into tokens.
    if pre in WORD_TO_FLOOR:
        return frozenset([WORD_TO_FLOOR[pre]])

    floors = set()
    for tok in _tokenise(pre):
        v = _resolve_token(tok)
        if v is not None:
            floors.add(v)

    return frozenset(floors) if floors else None


# Classification

CATEGORIES = ["underground", "ground", "upper", "multi_floor", "unknown"]


def _classify(floors) -> str:
    if not floors:
        return "unknown"
    if len(floors) > 1:
        return "multi_floor"
    (f,) = floors
    if f < 0:
        return "underground"
    if f == 0:
        return "ground"
    return "upper"


def clean_piano(series: pd.Series) -> pd.Series:
    """
    Clean and categorise a raw 'piano' (floor) column.

    Returns a pd.Categorical Series with categories:
        underground | ground | upper | multi_floor | unknown

    Example
    -------
    df_pure['piano_clean'] = clean_piano(df_pure['piano'])
    """
    def _process(raw):
        if pd.isna(raw):
            return "unknown"
        return _classify(_parse(str(raw)))

    return series.map(_process).astype(
        pd.CategoricalDtype(categories=CATEGORIES, ordered=False)
    )


def audit_piano(
    series: pd.Series,
    top_n: int = 30,
    show_parsed: bool = False,
) -> None:
    """
    Print a classification breakdown and surface unresolved values.

    Parameters
    ----------
    series      : raw piano Series (before cleaning)
    top_n       : how many unknown values to list (default 30)
    show_parsed : if True, print every unique raw value with its resolved
                  floor set — useful for debugging unfamiliar datasets

    Typical workflow
    ----------------
    1.  audit_piano(df_pure['piano'])
    2.  Add any unknowns you want to WORD_TO_FLOOR
    3.  Re-run the cell and repeat until satisfied
    4.  df_pure['piano_clean'] = clean_piano(df_pure['piano'])
    """
    cleaned = clean_piano(series)
    total = len(series)

    print("=" * 60)
    print(f"  Piano column audit   (n={total:,})")
    print("=" * 60)
    counts = cleaned.value_counts(dropna=False)
    for cat in CATEGORIES:
        n = int(counts.get(cat, 0))
        bar = "█" * max(1, int(n / total * 40)) if n else ""
        print(f"  {cat:<15}  {n:>6,}   {bar}")

    unknowns = series[cleaned == "unknown"]
    if not unknowns.empty:
        print(f"\n  Top {top_n} unresolved values  "
              f"({len(unknowns):,} rows, "
              f"{len(unknowns)/total*100:.1f}% of total):")
        for val, cnt in unknowns.value_counts().head(top_n).items():
            print(f"    {cnt:>5}x  {repr(val)}")
    else:
        print("\n  No unresolved values.")

    if show_parsed:
        print("\n  Full token resolution (unique raw values):")
        for val in sorted(series.dropna().unique(), key=str):
            floors = _parse(str(val))
            cat = _classify(floors)
            print(f"    {str(val):<40}  floors={str(floors):<25}  [{cat}]")

    print("=" * 60)