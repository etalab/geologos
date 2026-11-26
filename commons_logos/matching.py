"""Guess INSEE codes from logo file names."""

import os
import re
import unicodedata


# Words which may surround a commune name in a file title. Articles such as
# "le" or "la" are not listed: they belong to names like "Le Port".
NOISE_WORDS = frozenset("""
    logo logotype ville villede village commune mairie municipal officiel nouveau
    de d du des svg jpg png blason identite visuelle
    couleur couleurs bleu rouge noir blanc transparent detoure quadri rvb
    cmjn horizontal vertical texte web
""".split())
# Titles mentioning these are not about a single commune.
GROUP_WORDS = frozenset('metropole communaute agglomeration agglo cc cci'.split())


def normalize_key(text):
    """Normalize accents, punctuation, and spacing for matching."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("'", ' ').replace('’', ' ')
    text = re.sub(r'\bste\b', 'sainte', text)
    text = re.sub(r'\bst\b', 'saint', text)
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def is_noise(word):
    return word in NOISE_WORDS or bool(re.fullmatch(r'\d+(x\d+)?(px)?', word))


def match_insee_code(title, communes_index):
    """Guess the INSEE code of a commune from a logo file title.

    Only a whole name matches, once noise words are removed from both ends:
    searching a commune name anywhere in the title gives wrong codes
    ("Cergy Rouge" is not the commune of Rougé).
    """
    stem = os.path.splitext(title.split(':', 1)[-1])[0]
    # Split camel case / glued words: "LogoVilleAgen" -> "Logo Ville Agen".
    stem = re.sub(r'(?<=[a-zà-ÿ])(?=[A-Z])', ' ', stem)
    words = normalize_key(stem).split()
    if GROUP_WORDS.intersection(words):
        return None

    # Try the longest candidates first, only dropping noise at the ends.
    candidates = []
    start = 0
    while start < len(words):
        end = len(words)
        while end > start:
            candidates.append(' '.join(words[start:end]))
            if not (is_noise(words[end - 1]) or words[end - 1] in ('la', 'le')):
                break
            end -= 1
        if not (is_noise(words[start]) or words[start] in ('la', 'le')):
            break
        # "la ville de X": drop "la" only when it introduces a noise word.
        if words[start] in ('la', 'le') and not (
                start + 1 < len(words) and is_noise(words[start + 1])):
            break
        start += 1

    for candidate in sorted(candidates, key=len, reverse=True):
        if candidate in communes_index:
            return communes_index[candidate]
    return None
