# receipt_parser.py
# Heuristic line-based parser for OCR'd receipt text (see AndroidOcr.kt's
# y-grouped "rows" output). Pure functions, no DB/session dependencies, so
# this can be unit-tested in isolation from the rest of the app.
#
# Expected single-item line format (after OCR):
#   <product number> <description> <price:.2f> <A|B>
# e.g. "12345 Milch 3,5% 1,99 A"
#
# Expected multi-item line format (a "count x unit price" line immediately
# followed by a single-item line for the same product):
#   <count> x <unit price:.2f>
#   <product number> <description> <price:.2f> <A|B>
# e.g. "3 x 1,99"
#      "12345 Milch 3,5% 5,97 A"
#
# Faded/worn receipts sometimes get letters/digits misread by OCR (e.g. "B"
# misread as "8") and the price's decimal separator misread as something
# other than ',' or '.' (e.g. a plain space). These heuristics -- which
# letters are valid, which characters should be corrected to which letter,
# and which characters count as a decimal separator -- are user-adjustable
# (see ReceiptParsingRules / the app's Settings page) rather than hardcoded,
# since different receipts/printers/OCR runs can misbehave differently.
#
# Some bottle/deposit items add an extra "Pfand" (deposit) line identified by
# a fixed product number (provided by the caller, since it's store-specific
# and not reliably distinguishable by description alone):
#   <pfand product number> <description> <price:.2f> <letter>
# e.g. "80000291 Einweg Pfand 0,25 C"
# This line ALWAYS comes after the product it belongs to, never before.
# Either the product, the Pfand line, both, or neither may have their own
# "<count> x <unit price>" multiplier header -- e.g. buying one 6-pack (no
# header on the product line) still needs a header on the deposit line for
# the 6 individual bottle deposits ("6 x 0,25" then the Pfand item line).
# Whichever combination occurs, the Pfand line's price is collapsed into the
# product it follows: added to that item's price, and kept separately as
# "pfand_price" for display (e.g. as a "+price PF" annotation).

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

# Defaults used when the caller doesn't provide customized rules.
DEFAULT_VALID_LETTERS: List[str] = ["A", "B", "C", "D", "E"]
DEFAULT_LETTER_CORRECTIONS: Dict[str, str] = {"8": "B"}
DEFAULT_DECIMAL_SEPARATOR_CHARS: List[str] = [",", ".", " "]

# Fuzzy product-number merge heuristic defaults (see
# find_fuzzy_merge_candidates): how many digits must match exactly, which
# digit pairs are considered common OCR misreads of each other, and the
# expected length of a product number (used to tolerate one missed digit).
DEFAULT_MIN_MATCHING_DIGITS: int = 3
DEFAULT_CONFUSABLE_DIGIT_PAIRS: List[List[str]] = [
    ["3", "8"], ["5", "6"], ["1", "7"], ["0", "8"],
]
DEFAULT_EXPECTED_ID_LENGTH: Optional[int] = 6

# Allowed absolute rounding error when checking count * unit_price == price.
_PRICE_TOLERANCE = 0.01


def get_default_parsing_settings() -> Dict[str, Any]:
    """Returns the built-in default parsing rules, e.g. for a Settings page
    to prefill before the user has customized anything.
    """
    return {
        "valid_letters": list(DEFAULT_VALID_LETTERS),
        "letter_corrections": dict(DEFAULT_LETTER_CORRECTIONS),
        "decimal_separator_chars": list(DEFAULT_DECIMAL_SEPARATOR_CHARS),
        "min_matching_digits": DEFAULT_MIN_MATCHING_DIGITS,
        "confusable_digit_pairs": [list(pair) for pair in DEFAULT_CONFUSABLE_DIGIT_PAIRS],
        "expected_id_length": DEFAULT_EXPECTED_ID_LENGTH,
    }


class ReceiptParsingRules:
    """Bundles the user-configurable OCR-heuristic rules used while parsing
    a receipt:
      - valid_letters: which single-character VAT categories are expected
        at the end of an item line (e.g. ['A', 'B'], or ['A', 'B', 'C', 'D']
        for stores with more categories).
      - letter_corrections: characters OCR sometimes misreads in place of a
        valid letter, mapped to the letter they should be corrected to
        (e.g. {'8': 'B'} for a faded 'B', or {'4': 'A'} if 'A' gets misread
        as '4').
      - decimal_separator_chars: characters that can appear as a price's
        decimal separator, including OCR misreads (e.g. [',', '.', ' ']
        when a comma sometimes gets misread as a plain space).
      - pfand_product_number: the store-specific product number identifying
        a "Pfand" (bottle deposit) line, if known.
    """

    def __init__(
        self,
        valid_letters: Optional[List[str]] = None,
        letter_corrections: Optional[Dict[str, str]] = None,
        decimal_separator_chars: Optional[List[str]] = None,
        pfand_product_number: Optional[str] = None,
    ):
        self.valid_letters = [
            c.upper() for c in (valid_letters or DEFAULT_VALID_LETTERS) if c
        ]
        self.letter_corrections = {
            k: v.upper()
            for k, v in (letter_corrections or DEFAULT_LETTER_CORRECTIONS).items()
            if k and v
        }
        self.decimal_separator_chars = [
            c for c in (decimal_separator_chars or DEFAULT_DECIMAL_SEPARATOR_CHARS) if c
        ] or list(DEFAULT_DECIMAL_SEPARATOR_CHARS)
        self.pfand_product_number = pfand_product_number or None

        self._price_pattern = self._build_price_pattern()
        self.item_re = self._build_item_re()
        self.multiplier_re = self._build_multiplier_re()

    def _decimal_separator_char_class(self) -> str:
        return "".join(re.escape(c) for c in self.decimal_separator_chars)

    def _build_price_pattern(self) -> str:
        return rf"\d{{1,4}}[{self._decimal_separator_char_class()}]\d{{2}}"

    def _letter_char_class(self) -> str:
        chars = set()
        for letter in self.valid_letters:
            chars.add(letter.upper())
            chars.add(letter.lower())
        chars.update(self.letter_corrections)
        return "".join(re.escape(c) for c in sorted(chars))

    def _build_item_re(self) -> re.Pattern:
        # Product number, description, price, trailing valid/misread letter.
        # Description is matched lazily so the price/letter anchored at the
        # end are preferred over any numbers embedded in the text.
        return re.compile(
            rf"^\s*(?P<product_number>\d+)\s+(?P<description>.+?)\s+"
            rf"(?P<price>{self._price_pattern})\s*(?P<letter>[{self._letter_char_class()}])\s*$"
        )

    def _build_multiplier_re(self) -> re.Pattern:
        # "<count> x <unit price>" line preceding a multi-item purchase's item line.
        return re.compile(
            rf"^\s*(?P<count>\d+)\s*[xX]\s*(?P<unit_price>{self._price_pattern})\s*$"
        )

    def parse_price(self, raw: str) -> float:
        normalized = re.sub(f"[{self._decimal_separator_char_class()}]", ".", raw)
        return round(float(normalized), 2)

    def normalize_letter(self, raw: str) -> str:
        """Corrects a misread character (e.g. '8') to its intended letter
        (e.g. 'B'), or just upper-cases an already-valid letter.
        """
        if raw in self.letter_corrections:
            return self.letter_corrections[raw]
        upper = raw.upper()
        if upper in self.letter_corrections:
            return self.letter_corrections[upper]
        return upper

    def match_pfand_line(self, text: str) -> Optional[Dict[str, Any]]:
        """Matches text against the configured Pfand product number
        specifically (not the generic item pattern, since the deposit
        line's letter/category may differ). Returns {"description",
        "price"} or None.
        """
        if not self.pfand_product_number:
            return None
        pattern = re.compile(
            rf"^\s*{re.escape(self.pfand_product_number)}\s+(?P<description>.+?)\s+"
            rf"(?P<price>{self._price_pattern})\s*[A-Za-z0-9]*\s*$"
        )
        match = pattern.match(text)
        if not match:
            return None
        return {
            "description": match.group("description").strip(),
            "price": self.parse_price(match.group("price")),
        }


def _try_match_trailing_pfand(
    lines: List[str], start: int, rules: "ReceiptParsingRules"
) -> Optional[Dict[str, Any]]:
    """Looks for a Pfand deposit sequence beginning at `start` (always AFTER
    the product it belongs to): either a bare Pfand line, or a multiplier
    header for the deposit quantity immediately followed by a Pfand line.
    Returns {"price", "line_numbers"} or None if no Pfand sequence is there.
    """
    if not rules.pfand_product_number or start >= len(lines):
        return None

    bare_match = rules.match_pfand_line((lines[start] or "").strip())
    if bare_match is not None:
        return {"price": bare_match["price"], "line_numbers": [start]}

    multiplier_match = rules.multiplier_re.match((lines[start] or "").strip())
    if multiplier_match and start + 1 < len(lines):
        pfand_match = rules.match_pfand_line((lines[start + 1] or "").strip())
        if pfand_match is not None:
            return {"price": pfand_match["price"], "line_numbers": [start, start + 1]}

    return None


def _attach_trailing_pfand(
    group: Dict[str, Any], lines: List[str], rules: "ReceiptParsingRules"
) -> None:
    """Looks immediately after `group`'s consumed lines for a Pfand deposit
    sequence and, if found, merges it into `group` in place: adds to price,
    records pfand_price, and extends line_numbers (and text, if present).
    """
    next_index = group["line_numbers"][-1] + 1
    pfand_info = _try_match_trailing_pfand(lines, next_index, rules)
    if pfand_info is None:
        return

    group["price"] = round(group["price"] + pfand_info["price"], 2)
    group["pfand_price"] = pfand_info["price"]
    group["line_numbers"] = group["line_numbers"] + pfand_info["line_numbers"]
    if "text" in group:
        pfand_lines = [lines[n] for n in pfand_info["line_numbers"]]
        group["text"] = "\n".join([group["text"], *pfand_lines])


def _try_match_multiplier_group(
    lines: List[str], i: int, rules: "ReceiptParsingRules"
) -> Optional[Dict[str, Any]]:
    """Attempts to match lines[i] as a "count x unit_price" line followed by
    lines[i + 1] as its item line. Returns the resulting group (with
    "verified" indicating whether count * unit_price == price), or None if
    lines[i] isn't a multiplier line or isn't followed by a matching item.
    """
    if i + 1 >= len(lines):
        return None

    multiplier_match = rules.multiplier_re.match((lines[i] or "").strip())
    if not multiplier_match:
        return None

    item_match = rules.item_re.match((lines[i + 1] or "").strip())
    if not item_match:
        return None

    count = int(multiplier_match.group("count"))
    unit_price = rules.parse_price(multiplier_match.group("unit_price"))
    price = rules.parse_price(item_match.group("price"))
    expected = round(count * unit_price, 2)
    verified = abs(expected - price) <= _PRICE_TOLERANCE

    group: Dict[str, Any] = {
        "count": count,
        "product_number": item_match.group("product_number"),
        "description": item_match.group("description").strip(),
        "price": price,
        "letter": rules.normalize_letter(item_match.group("letter")),
        "line_numbers": [i, i + 1],
        "verified": verified,
    }

    if not verified:
        group["text"] = f"{lines[i]}\n{lines[i + 1]}"
        group["reason"] = (
            f"{count} x {unit_price:.2f} = {expected:.2f}, "
            f"but line price is {price:.2f}"
        )

    return group


def aggregate_items(
    items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Collapses items with the same product_number into a single entry,
    summing count and price across all their occurrences.

    This is a separate, explicit step from parse_receipt_lines: callers are
    expected to let the user clean up (edit/delete/merge/re-parse) the raw
    per-line items first, then call this once they're done.

    Matching is done by product_number only (not description): OCR'd
    descriptions for the same product can differ slightly between
    occurrences (e.g. truncation, misreads), but the product number is a
    much more reliable identifier.
    """
    aggregated: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []

    for item in items:
        product_number = item["product_number"]
        if product_number not in aggregated:
            aggregated[product_number] = {
                "count": 0,
                "product_number": product_number,
                "description": item["description"],
                "price": 0.0,
                "pfand_price": 0.0,
                "letter": item["letter"],
                "line_numbers": [],
                "verified": True,
            }
            order.append(product_number)

        entry = aggregated[product_number]
        entry["count"] += item["count"]
        entry["price"] = round(entry["price"] + item["price"], 2)
        entry["pfand_price"] = round(
            entry["pfand_price"] + item.get("pfand_price", 0.0), 2
        )
        entry["line_numbers"].extend(item["line_numbers"])

    result = []
    for product_number in order:
        entry = aggregated[product_number]
        entry["line_numbers"] = sorted(set(entry["line_numbers"]))
        if abs(entry["pfand_price"]) < _PRICE_TOLERANCE:
            del entry["pfand_price"]
        result.append(entry)
    return result


def _build_confusable_lookup(pairs: List[List[str]]) -> Dict[str, set]:
    lookup: Dict[str, set] = {}
    for pair in pairs:
        chars = [c for c in pair if c]
        for c in chars:
            lookup.setdefault(c, set()).update(x for x in chars if x != c)
    return lookup


def _compare_digit_strings(
    a: str, b: str, confusable_lookup: Dict[str, set]
) -> Optional[int]:
    """Compares two equal-length digit strings position by position.
    Returns the count of EXACT matches if every mismatched position is a
    "confusable" pair (per confusable_lookup), or None if any mismatch is
    not confusable (i.e. a genuine difference, not just an OCR misread).
    """
    if len(a) != len(b):
        return None
    exact = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            exact += 1
        elif cb not in confusable_lookup.get(ca, set()):
            return None
    return exact


def _fuzzy_digits_match(
    a: str,
    b: str,
    min_matching_digits: int,
    confusable_lookup: Dict[str, set],
    expected_id_length: Optional[int],
) -> bool:
    """True if product numbers `a` and `b` look like the same code with one
    or more digits misread by OCR (see find_fuzzy_merge_candidates).
    """
    if a == b:
        return False  # identical codes are already grouped by aggregate_items

    candidates = []
    if len(a) == len(b):
        candidates.append((a, b))
    elif expected_id_length and abs(len(a) - len(b)) == 1:
        longer, shorter = (a, b) if len(a) > len(b) else (b, a)
        # A digit could have been missed at either the start or the end.
        candidates.append((longer[1:], shorter))
        candidates.append((longer[:-1], shorter))

    for x, y in candidates:
        exact = _compare_digit_strings(x, y, confusable_lookup)
        if exact is not None and exact >= min_matching_digits:
            return True
    return False


class _UnionFind:
    """Minimal union-find (disjoint set) helper for clustering indices."""

    def __init__(self, size: int):
        self._parent = list(range(size))

    def find(self, i: int) -> int:
        while self._parent[i] != i:
            self._parent[i] = self._parent[self._parent[i]]
            i = self._parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        root_i, root_j = self.find(i), self.find(j)
        if root_i != root_j:
            self._parent[root_i] = root_j


def _price_per_package(item: Dict[str, Any]) -> Optional[float]:
    count = item.get("count") or 0
    if count <= 0:
        return None
    return round(item["price"] / count, 2)


def _cluster_fuzzy_matching_items(
    items: List[Dict[str, Any]],
    threshold: int,
    confusable_lookup: Dict[str, set],
    expected_id_length: Optional[int],
) -> _UnionFind:
    prices = [_price_per_package(item) for item in items]
    union_find = _UnionFind(len(items))

    for i in range(len(items)):
        if prices[i] is None:
            continue
        for j in range(i + 1, len(items)):
            if prices[j] is None or prices[i] != prices[j]:
                continue
            if _fuzzy_digits_match(
                items[i]["product_number"],
                items[j]["product_number"],
                threshold,
                confusable_lookup,
                expected_id_length,
            ):
                union_find.union(i, j)

    return union_find


def find_fuzzy_merge_candidates(
    items: List[Dict[str, Any]],
    min_matching_digits: Optional[int] = None,
    confusable_digit_pairs: Optional[List[List[str]]] = None,
    expected_id_length: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Given items already aggregated by exact product_number (see
    aggregate_items), finds clusters of DIFFERENT product_numbers that are
    likely the same product with a misread digit, for the user to confirm
    or reject before merging.

    Two items are only considered a fuzzy match if their price-per-package
    is identical (price parsing is reliable even when the product number
    isn't) AND their product numbers satisfy the digit heuristic:
      - enough digits match exactly (>= min_matching_digits), and every
        remaining mismatched digit is a "commonly misread" pair (e.g.
        3<->8, 5<->6) -- any other mismatch rules the pair out entirely.
      - if the numbers' lengths differ by exactly one and
        expected_id_length is set, the shorter one is compared against the
        longer one with either its first or last digit dropped (a likely
        missed leading/trailing digit), using the same rule above.

    Returns a list of clusters: [{"items": [<aggregated item>, ...]}, ...],
    each with 2+ items suspected to be the same product. Items with no
    fuzzy match to anything else are omitted entirely. Callers are expected
    to let the user pick which items in each cluster to actually merge
    (e.g. via checkboxes), then call merge_items() on the confirmed subset.
    """
    threshold = (
        min_matching_digits
        if min_matching_digits is not None
        else DEFAULT_MIN_MATCHING_DIGITS
    )
    pairs = (
        confusable_digit_pairs
        if confusable_digit_pairs is not None
        else DEFAULT_CONFUSABLE_DIGIT_PAIRS
    )
    confusable_lookup = _build_confusable_lookup(pairs)

    union_find = _cluster_fuzzy_matching_items(
        items, threshold, confusable_lookup, expected_id_length
    )

    clusters: Dict[int, List[int]] = {}
    for i in range(len(items)):
        clusters.setdefault(union_find.find(i), []).append(i)

    return [
        {"items": [items[i] for i in indices]}
        for indices in clusters.values()
        if len(indices) > 1
    ]


def merge_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merges a user-confirmed set of (already-aggregated) items believed to
    be the same product (see find_fuzzy_merge_candidates) into a single
    entry: sums count/price/pfand_price, unions line_numbers, and keeps the
    first item's product_number/description/letter as representative.
    """
    if not items:
        raise ValueError("Invalid input: items must be a non-empty list")

    merged: Dict[str, Any] = {
        "count": 0,
        "product_number": items[0]["product_number"],
        "description": items[0]["description"],
        "price": 0.0,
        "pfand_price": 0.0,
        "letter": items[0]["letter"],
        "line_numbers": [],
        "verified": True,
    }
    for item in items:
        merged["count"] += item["count"]
        merged["price"] = round(merged["price"] + item["price"], 2)
        merged["pfand_price"] = round(
            merged["pfand_price"] + item.get("pfand_price", 0.0), 2
        )
        merged["line_numbers"].extend(item["line_numbers"])

    merged["line_numbers"] = sorted(set(merged["line_numbers"]))
    if abs(merged["pfand_price"]) < _PRICE_TOLERANCE:
        del merged["pfand_price"]
    return merged


# Default minimum word-match ratio for suggest_ingredient_matches: a
# description word and an ingredient-name word are considered a confident
# match if they're at least this similar (see _word_match_ratio).
DEFAULT_MIN_WORD_MATCH_RATIO: float = 0.8

_WORD_SPLIT_RE = re.compile(r"[^\w]+", re.UNICODE)


def _tokenize_words(text: str) -> List[str]:
    return [w for w in _WORD_SPLIT_RE.split(text.lower()) if w]


def _word_match_ratio(word_a: str, word_b: str) -> float:
    """Best-case similarity between two words, robust to length
    differences: if the shorter word is contained (exactly, or nearly so)
    anywhere within the longer one, this returns close to 1.0 regardless of
    how much longer the other word is -- e.g. "zwiebel" vs "röstzwiebel".
    """
    if not word_a or not word_b:
        return 0.0
    if word_a == word_b:
        return 1.0

    shorter, longer = (word_a, word_b) if len(word_a) <= len(word_b) else (word_b, word_a)

    best_containment = 0.0
    for start in range(len(longer) - len(shorter) + 1):
        window = longer[start:start + len(shorter)]
        ratio = SequenceMatcher(None, shorter, window).ratio()
        if ratio > best_containment:
            best_containment = ratio
        if best_containment >= 1.0:
            break

    # Also consider the words as a whole, for similar-length typos where
    # neither word is really "contained" in the other.
    whole_ratio = SequenceMatcher(None, word_a, word_b).ratio()
    return max(best_containment, whole_ratio)


def _best_description_match_ratio(description: str, ingredient_name: str) -> float:
    """Highest word-vs-word match ratio between a description and an
    ingredient name. Only one confidently-matching word pair is needed --
    e.g. "Röstzwiebel Chips 200g" vs ingredient "Zwiebel" matches on
    "Röstzwiebel"/"Zwiebel" alone.
    """
    description_words = _tokenize_words(description)
    ingredient_words = _tokenize_words(ingredient_name)
    best = 0.0
    for description_word in description_words:
        for ingredient_word in ingredient_words:
            ratio = _word_match_ratio(description_word, ingredient_word)
            if ratio > best:
                best = ratio
    return best


def _find_best_ingredient_match(
    description: str,
    ingredients: List[Dict[str, Any]],
    threshold: float,
) -> Dict[str, Any]:
    """Finds the best-matching ingredient for a single description. Returns
    {"ingredient_id", "ingredient_name", "best_ratio", "tie_candidates"} for
    debug visibility as well as the actual suggestion.
    """
    best_ratio = 0.0
    best_overall = -1.0
    best_ingredient_id: Optional[int] = None
    best_ingredient_name = None
    tie_candidates: List[str] = []

    for ingredient in ingredients:
        name = ingredient.get("name") or ""
        ratio = _best_description_match_ratio(description, name)
        if ratio < threshold:
            continue

        if ratio > best_ratio:
            tie_candidates = [name]
        elif ratio == best_ratio:
            tie_candidates.append(name)

        overall = SequenceMatcher(None, description.lower(), name.lower()).ratio()
        if ratio > best_ratio or (ratio == best_ratio and overall > best_overall):
            best_ratio = ratio
            best_overall = overall
            best_ingredient_id = ingredient.get("ingredient_id")
            best_ingredient_name = name

    return {
        "ingredient_id": best_ingredient_id,
        "ingredient_name": best_ingredient_name,
        "best_ratio": best_ratio,
        "tie_candidates": tie_candidates,
    }


def suggest_ingredient_matches(
    items: List[Dict[str, Any]],
    ingredients: List[Dict[str, Any]],
    min_word_match_ratio: Optional[float] = None,
) -> Dict[str, Any]:
    """Suggests, for each item, the app Ingredient (by ingredient_id) whose
    name best fuzzy-matches the item's description, to prefill the manual
    ingredient-matching step (the user still reviews/confirms every
    suggestion, so this only needs to be a good guess, not perfect).

    A description and an ingredient name match if ANY single word from one
    is a confident match (>= min_word_match_ratio) for any single word from
    the other -- multi-word descriptions/names don't all need to match, and
    a word is considered a confident match either because the two words are
    similar as a whole (e.g. minor OCR typos) or because one word is
    contained (exactly, or nearly so) within the other, e.g. ingredient
    "Zwiebel" inside product description "Röstzwiebel" (and vice versa).

    Returns {"suggestions": {"<item index>": ingredient_id_or_null, ...}}.
    If two or more ingredients tie on their best word-match ratio for the
    same item (e.g. several "Lachgummi ..." variants all containing the
    word "Lachgummi"), the one whose full name is overall most similar to
    the description is preferred -- a suggestion is still made rather than
    giving up, since the user reviews/confirms it anyway.
    """
    threshold = (
        min_word_match_ratio
        if min_word_match_ratio is not None
        else DEFAULT_MIN_WORD_MATCH_RATIO
    )
    print(
        f"DEBUG: suggest_ingredient_matches called with {len(items)} item(s), "
        f"{len(ingredients)} ingredient(s), threshold={threshold}"
    )

    suggestions: Dict[str, Optional[int]] = {}
    for index, item in enumerate(items):
        description = item.get("description") or ""
        match = _find_best_ingredient_match(description, ingredients, threshold)
        suggestions[str(index)] = match["ingredient_id"]
        print(
            f"DEBUG: suggest_ingredient_matches item[{index}] description={description!r} "
            f"-> best_ratio={match['best_ratio']:.2f} candidates={match['tie_candidates']!r} "
            f"chosen={match['ingredient_name']!r} (ingredient_id={match['ingredient_id']})"
        )

    return {"suggestions": suggestions}


def parse_receipt_lines(
    lines: List[str],
    pfand_product_number: Optional[str] = None,
    valid_letters: Optional[List[str]] = None,
    letter_corrections: Optional[Dict[str, str]] = None,
    decimal_separator_chars: Optional[List[str]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Parse OCR'd receipt row text into structured purchase line items.

    Each recognized line (or multiplier header + line, or product + Pfand
    sequence) becomes its own entry in "items" -- items are NOT collapsed by
    product_number here. Call aggregate_items() as a separate, explicit step
    once the caller/user has finished cleaning up the raw per-line results
    (editing, deleting, merging, re-parsing).

    Args:
        lines: One string per detected row (index in this list is used as
            the "line number" for traceability back to the original OCR
            output, e.g. when displaying which raw lines a group came from).
        pfand_product_number: The store-specific product number used for
            "Pfand" (bottle deposit) lines, if known. When provided, a Pfand
            sequence immediately following a product (a bare Pfand line, or
            a multiplier header + Pfand line) is collapsed into that
            product: its price is added to the item's price, and kept
            separately as "pfand_price". Left as None/empty, Pfand lines are
            treated like any other unrecognized line.
        valid_letters: Which single-character VAT categories are expected at
            the end of an item line. Defaults to DEFAULT_VALID_LETTERS.
        letter_corrections: Characters OCR sometimes misreads in place of a
            valid letter, mapped to the letter to correct them to. Defaults
            to DEFAULT_LETTER_CORRECTIONS (e.g. {"8": "B"}).
        decimal_separator_chars: Characters that can appear as a price's
            decimal separator, including OCR misreads. Defaults to
            DEFAULT_DECIMAL_SEPARATOR_CHARS (e.g. [",", ".", " "]).

    Returns:
        {
            "items": [ { count, product_number, description, price, letter,
                         line_numbers, verified: True, pfand_price? }, ... ],
            "unmatched": [ { line_numbers, text, reason,
                              # present only for a detected-but-unverified
                              # multiplier+item pair:
                              count, product_number, description, price, letter,
                              verified: False }, ... ],
        }
    """
    if lines is None or not isinstance(lines, list):
        raise ValueError("Invalid input: lines must be a list of strings")

    rules = ReceiptParsingRules(
        valid_letters=valid_letters,
        letter_corrections=letter_corrections,
        decimal_separator_chars=decimal_separator_chars,
        pfand_product_number=pfand_product_number,
    )

    items: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []

    i = 0
    n = len(lines)
    while i < n:
        text = (lines[i] or "").strip()
        if not text:
            i += 1
            continue

        multiplier_group = _try_match_multiplier_group(lines, i, rules)
        if multiplier_group is not None:
            _attach_trailing_pfand(multiplier_group, lines, rules)
            (items if multiplier_group["verified"] else unmatched).append(multiplier_group)
            i = multiplier_group["line_numbers"][-1] + 1
            continue

        item_match = rules.item_re.match(text)
        if item_match:
            group = {
                "count": 1,
                "product_number": item_match.group("product_number"),
                "description": item_match.group("description").strip(),
                "price": rules.parse_price(item_match.group("price")),
                "letter": rules.normalize_letter(item_match.group("letter")),
                "line_numbers": [i],
                "verified": True,
            }
            _attach_trailing_pfand(group, lines, rules)
            items.append(group)
            i = group["line_numbers"][-1] + 1
            continue

        unmatched.append({
            "line_numbers": [i],
            "text": lines[i],
            "reason": "Line did not match the expected item pattern",
        })
        i += 1

    return {
        "items": items,
        "unmatched": unmatched,
    }

