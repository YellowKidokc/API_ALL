"""Deterministic text statistics for station 42 (pure Python; same numbers every run).

Names match config/metric_catalog.json (the approved statistics matrix). Each metric carries
method = python | python-heuristic | library:<name>, so every number says how it was made.
Optional libraries are used when installed (textstat for Dale-Chall / Spache, vaderSentiment for
VADER, spaCy for syntax); otherwise those metrics are simply absent, never guessed.
"""
from __future__ import annotations

import bz2
import gzip
import lzma
import math
import re
import statistics
from collections import Counter, defaultdict
from typing import Any

from .text import Paragraph, Sentence

STOP = set("""a about above after again against all am an and any are as at be because been before being below between both but by
can could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if
in into is it its itself just me more most my myself no nor not now of off on once only or other our ours ourselves out over own same
she should so some such than that the their theirs them themselves then there these they this those through to too under until up very
was we were what when where which while who whom why will with would you your yours yourself yourselves also may might must shall upon
unto thee thou thy ye""".split())
PRONOUNS = set("i me my mine myself we us our ours ourselves you your yours yourself yourselves he him his himself she her hers herself it its itself they them their theirs themselves".split())
PREPS = set("about above across after against along among around at before behind below beneath beside between beyond by down during except for from in inside into like near of off on onto out outside over past since through throughout to toward towards under underneath until unto up upon with within without".split())
CONJ = set("and but or nor for yet so because although though while whereas if unless since whether".split())
DETS = set("the a an this that these those each every either neither some any no all both half several many much few little".split())
SUBORD = set("because although though while whereas if unless since whether that which who whom whose when where after before until once".split())
CONNECTIVES = {
    "Causal connectives": ["because", "therefore", "thus", "hence", "consequently", "so that", "as a result", "since", "for this reason"],
    "Adversative connectives": ["but", "however", "yet", "although", "though", "nevertheless", "nonetheless", "whereas", "on the other hand", "instead"],
    "Temporal connectives": ["then", "after", "before", "when", "while", "meanwhile", "finally", "first", "next", "later", "until"],
    "Additive connectives": ["and", "also", "moreover", "furthermore", "in addition", "besides", "likewise", "similarly"],
    "Conditional connectives": ["if", "unless", "provided that", "in case", "otherwise", "whether"],
}
HEDGES = ["may", "might", "could", "perhaps", "possibly", "probably", "likely", "suggest", "suggests", "appear", "appears", "seem", "seems",
          "somewhat", "arguably", "tend to", "tends to", "in part", "approximately", "roughly", "i think", "we think", "plausibly"]
BOOSTERS = ["clearly", "obviously", "certainly", "definitely", "undoubtedly", "indeed", "in fact", "of course", "must", "demonstrate",
            "demonstrates", "show", "shows", "prove", "proves", "without doubt", "surely"]
ATTITUDE = ["unfortunately", "remarkably", "surprisingly", "importantly", "interestingly", "hopefully", "astonishingly", "sadly",
            "fortunately", "crucially", "beautifully"]
ENGAGEMENT = ["you", "your", "consider", "note", "notice", "imagine", "see", "let us", "let's", "recall", "suppose"]
SELF = ["i", "me", "my", "mine", "we", "our", "us"]
ABSOLUTES = ["always", "never", "proves", "proven", "prove", "every", "all", "none", "nothing", "everything", "certainly", "undeniably", "must"]
POSITIVE = set("""good great love joy peace hope grace true truth beautiful kind wonderful glad happy blessed faithful strong life light
gift free freedom mercy trust wise wisdom delight rejoice praise holy healing heal whole restore restored best better beloved""".split())
NEGATIVE = set("""bad evil hate fear death dead sin wrong false lie lies pain suffer suffering sorrow sad anger angry wrath chaos broken
destroy destruction curse cursed darkness dark lost doubt despair guilt shame fail failure weak worse worst cruel""".split())
OT = ["genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua", "judges", "ruth", "samuel", "kings", "chronicles", "ezra",
      "nehemiah", "esther", "job", "psalm", "psalms", "proverbs", "ecclesiastes", "song of songs", "isaiah", "jeremiah", "lamentations",
      "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah", "haggai", "zechariah", "malachi",
      "gen", "exod", "lev", "deut", "isa", "jer", "ezek", "dan", "ps", "prov"]
NT = ["matthew", "mark", "luke", "john", "acts", "romans", "corinthians", "galatians", "ephesians", "philippians", "colossians",
      "thessalonians", "timothy", "titus", "philemon", "hebrews", "james", "peter", "jude", "revelation",
      "matt", "mk", "lk", "jn", "rom", "cor", "gal", "eph", "phil", "col", "thess", "tim", "heb", "jas", "pet", "rev"]


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", text)


def syllables(word: str) -> int:
    w = word.lower().strip("'’-")
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def _per_k(count: int, n_words: int) -> float:
    return round(count / max(1, n_words) * 1000, 2)


def _count_phrases(low: str, phrases: list[str]) -> int:
    return sum(len(re.findall(r"(?<![\w'])" + re.escape(p) + r"(?![\w'])", low)) for p in phrases)


def _mtld(tokens: list[str], threshold: float = 0.72) -> float | None:
    def one_pass(seq):
        factors, types, count = 0.0, set(), 0
        for t in seq:
            count += 1
            types.add(t)
            if len(types) / count <= threshold:
                factors += 1
                types, count = set(), 0
        if count:
            ttr = len(types) / count
            factors += (1 - ttr) / (1 - threshold) if ttr < 1 else 0
        return len(seq) / factors if factors else None
    if len(tokens) < 50:
        return None
    a, b = one_pass(tokens), one_pass(list(reversed(tokens)))
    return round((a + b) / 2, 2) if a and b else None


def _mattr(tokens: list[str], window: int = 50) -> float | None:
    if len(tokens) < window:
        return None
    counts = Counter(tokens[:window])
    total = len(counts)
    vals = [total / window]
    for i in range(window, len(tokens)):
        out, inn = tokens[i - window], tokens[i]
        counts[out] -= 1
        if counts[out] == 0:
            total -= 1
            del counts[out]
        if counts[inn] == 0:
            total += 1
        counts[inn] += 1
        vals.append(total / window)
    return round(sum(vals) / len(vals), 4)


def _hdd(tokens: list[str], sample: int = 42) -> float | None:
    n = len(tokens)
    if n < sample:
        return None
    total = 0.0
    for c in Counter(tokens).values():
        # probability the word is absent from a random sample of `sample` tokens (hypergeometric)
        p0 = math.exp(math.lgamma(n - c + 1) + math.lgamma(n - sample + 1) - math.lgamma(n - c - sample + 1) - math.lgamma(n + 1)) if n - c >= sample else 0.0
        total += (1 - p0) / sample
    return round(total, 4)


def _linfit(xs: list[float], ys: list[float]) -> tuple[float, float] | None:
    if len(xs) < 3:
        return None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if not sxx:
        return None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (my + slope * (x - mx))) ** 2 for x, y in zip(xs, ys))
    return slope, (1 - ss_res / ss_tot) if ss_tot else 1.0


def _entropy(counter: Counter) -> float:
    total = sum(counter.values())
    return -sum(c / total * math.log2(c / total) for c in counter.values()) if total else 0.0


def _cos(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b.get(k, 0) for k in a)
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def distribution(values: list[float]) -> dict[str, Any]:
    """The distribution set for any per-sentence series (STATISTICS_WALL_V1)."""
    if not values:
        return {}
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    sd = statistics.pstdev(values) if n > 1 else 0.0
    q1, q3 = s[int(n * .25)], s[min(n - 1, int(n * .75))]
    skew = sum((x - mean) ** 3 for x in values) / n / sd ** 3 if sd else 0.0
    kurt = sum((x - mean) ** 4 for x in values) / n / sd ** 4 - 3 if sd else 0.0
    total = sum(abs(x) for x in values)
    gini = sum(abs(a - b) for a in values for b in values) / (2 * n * n * (total / n)) if total and n <= 3000 else None
    lag = (sum((values[i] - mean) * (values[i + 1] - mean) for i in range(n - 1)) / (n * sd * sd)) if sd and n > 2 else None
    return {"mean": round(mean, 3), "median": statistics.median(values), "sd": round(sd, 3), "min": s[0], "max": s[-1],
            "iqr": q3 - q1, "skew": round(skew, 3), "kurtosis": round(kurt, 3), "gini": round(gini, 3) if gini is not None else None,
            "burstiness": round((sd - mean) / (sd + mean), 3) if (sd + mean) else None, "autocorr_lag1": round(lag, 3) if lag is not None else None,
            "argmax": values.index(max(values)), "argmin": values.index(min(values))}


def compute(text: str, paragraphs: list[Paragraph], sentences: list[Sentence], raw: str = "") -> tuple[list[dict], dict]:
    """Return (metrics, extras). extras holds series used by the charts (lengths, zipf points, ...)."""
    out: list[dict] = []

    def add(family: str, name: str, value, method: str = "python", **kw):
        if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
            return
        out.append({"family": family, "name": name, "value": round(float(value), 4), "method": method, **kw})

    words = _words(text)
    low_words = [w.lower().strip("'’") for w in words]
    n_words = len(words)
    n_sent = max(1, len(sentences))
    sent_words = [_words(s.text) for s in sentences]
    lengths = [len(w) for w in sent_words]
    syl = [syllables(w) for w in words]
    n_syl = sum(syl)
    poly = sum(1 for s in syl if s >= 3)
    chars = sum(len(w) for w in words)
    long_words = sum(1 for w in words if len(w) >= 7)
    low = text.lower()
    content = [w for w in low_words if w not in STOP and len(w) > 2]

    # Text and size
    add("text", "Word count", n_words)
    add("text", "Sentences", len(sentences))
    add("text", "Paragraphs", len(paragraphs))
    add("text", "Mean words per sentence", n_words / n_sent)
    add("text", "Longest sentence", max(lengths) if lengths else 0)
    add("text", "Type-token ratio", len(set(low_words)) / max(1, n_words))
    add("text", "Stopword ratio", sum(1 for w in low_words if w in STOP) / max(1, n_words))
    add("text", "Questions", sum(1 for s in sentences if s.text.rstrip().endswith("?")))
    add("text", "Quotations", len(re.findall(r"[\"“][^\"”]{3,}[\"”]", text)))
    add("text", "Parentheticals", len(re.findall(r"\([^)]{2,}\)", text)))
    add("text", "Reading time", n_words / 238, unit="min")
    add("text", "Speaking time", n_words / 150, unit="min")

    # Readability
    wps, spw = n_words / n_sent, n_syl / max(1, n_words)
    add("read", "Flesch reading ease", 206.835 - 1.015 * wps - 84.6 * spw)
    fk = 0.39 * wps + 11.8 * spw - 15.59
    add("read", "Flesch–Kincaid grade", fk)
    fog = 0.4 * (wps + 100 * poly / max(1, n_words))
    add("read", "Gunning fog", fog)
    smog = 1.043 * math.sqrt(poly * 30 / n_sent) + 3.1291 if len(sentences) >= 3 else None
    add("read", "SMOG", smog)
    L, S = chars / max(1, n_words) * 100, n_sent / max(1, n_words) * 100
    cli = 0.0588 * L - 0.296 * S - 15.8
    add("read", "Coleman–Liau", cli)
    ari = 4.71 * chars / max(1, n_words) + 0.5 * wps - 21.43
    add("read", "ARI", ari)
    add("read", "LIX", wps + 100 * long_words / max(1, n_words))
    add("read", "RIX", long_words / n_sent)
    sample = words[:100]
    easy = sum(1 for w in sample if syllables(w) < 3)
    hard = len(sample) - easy
    sents_in_sample = max(1, sum(1 for s in sentences[:max(1, int(len(sentences) * 100 / max(1, n_words)))]))
    lw = (easy + 3 * hard) / sents_in_sample
    add("read", "Linsear Write", lw / 2 if lw > 20 else (lw - 2) / 2, "python-heuristic")
    mono150 = sum(1 for w in words[:150] if syllables(w) == 1) * (150 / max(1, min(150, n_words)))
    add("read", "FORCAST", 20 - mono150 / 10)
    add("read", "McAlpine EFLAW", (n_words + sum(1 for w in words if len(w) <= 3)) / n_sent)
    try:
        import textstat  # type: ignore
        add("read", "Dale–Chall", textstat.dale_chall_readability_score(text), f"library:textstat {getattr(textstat, '__version__', '')}")
        add("read", "Spache", textstat.spache_readability(text), f"library:textstat {getattr(textstat, '__version__', '')}")
    except Exception:
        pass
    grades = [g for g in (fk, fog, smog, cli, ari) if g is not None]
    add("read", "Consensus grade", statistics.median(grades) if grades else None)

    # Vocabulary richness
    toks = low_words
    counts = Counter(toks)
    V, N = len(counts), max(1, len(toks))
    freq_of_freq = Counter(counts.values())
    add("lex", "MTLD", _mtld(toks))
    add("lex", "MATTR (w=50)", _mattr(toks))
    add("lex", "HD-D", _hdd(toks))
    m2 = sum(i * i * v for i, v in freq_of_freq.items())
    add("lex", "Yule's K", 1e4 * (m2 - N) / (N * N) if N > 1 else None)
    add("lex", "Simpson's D", sum(v * (v - 1) for v in counts.values()) / (N * (N - 1)) if N > 1 else None)
    v1 = freq_of_freq.get(1, 0)
    add("lex", "Honoré's R", 100 * math.log(N) / (1 - v1 / V) if V and v1 != V else None)
    add("lex", "Brunet's W", N ** (V ** -0.165) if V else None)
    add("lex", "Herdan's C", math.log(V) / math.log(N) if N > 1 and V > 1 else None)
    add("lex", "Maas a²", (math.log(N) - math.log(V)) / math.log(N) ** 2 if N > 1 and V > 1 else None)
    add("lex", "Hapax ratio", v1 / max(1, V))
    add("lex", "Dis legomena ratio", freq_of_freq.get(2, 0) / max(1, V))
    ranked = sorted(counts.values(), reverse=True)
    zipf_pts = [(i + 1, f) for i, f in enumerate(ranked)]
    fit = _linfit([math.log10(r) for r, _ in zipf_pts], [math.log10(f) for _, f in zipf_pts])
    if fit:
        add("lex", "Zipf slope", fit[0])
        add("lex", "Zipf R²", fit[1])
    seen, heaps_x, heaps_y = set(), [], []
    for i, t in enumerate(toks, 1):
        seen.add(t)
        if i % 25 == 0:
            heaps_x.append(math.log(i))
            heaps_y.append(math.log(len(seen)))
    hfit = _linfit(heaps_x, heaps_y)
    add("lex", "Heaps β", hfit[0] if hfit else None)

    # Sentence structure (heuristics without spaCy)
    add("syn", "Clauses per sentence", sum(1 + len(re.findall(r",\s*(?:" + "|".join(SUBORD) + r")\b|;", s.text.lower())) for s in sentences) / n_sent, "python-heuristic")
    add("syn", "Subordination index", sum(1 for w in low_words if w in SUBORD) / n_sent, "python-heuristic")
    passive = sum(len(re.findall(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b", s.text.lower())) > 0 for s in sentences)
    add("syn", "Passive voice ratio", passive / n_sent, "python-heuristic")
    add("syn", "Nominalization ratio", sum(1 for w in low_words if re.search(r"(tion|ment|ness|ity|ance|ence|ism)s?$", w) and len(w) > 6) / max(1, n_words), "python-heuristic")
    add("syn", "Pronoun share", sum(1 for w in low_words if w in PRONOUNS) / max(1, n_words))
    add("syn", "Lexical density", len(content) / max(1, n_words))
    add("syn", "Mean word length", chars / max(1, n_words))
    add("syn", "Long-word share", long_words / max(1, n_words))
    try:
        import spacy  # type: ignore
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:300000])
        pos = Counter(t.pos_ for t in doc if t.is_alpha)
        total = max(1, sum(pos.values()))
        method = f"library:spacy {spacy.__version__}"
        for name, tag in (("Noun share", "NOUN"), ("Verb share", "VERB"), ("Adjective share", "ADJ"), ("Adverb share", "ADV")):
            add("syn", name, pos.get(tag, 0) / total, method)
        dists = [abs(t.i - t.head.i) for t in doc if t.dep_ != "ROOT" and t.is_alpha]
        add("syn", "Mean dependency distance", sum(dists) / max(1, len(dists)), method)

        def depth(tok):
            d = 0
            while tok.head is not tok and d < 60:
                tok, d = tok.head, d + 1
            return d
        add("syn", "Parse-tree depth", sum(max((depth(t) for t in s), default=0) for s in doc.sents) / max(1, len(list(doc.sents))), method)
    except Exception:
        pass

    # Cohesion
    bags = [Counter(w.lower() for w in ws if w.lower() not in STOP and len(w) > 2) for ws in sent_words]
    nouns = [set(b) for b in bags]
    if len(bags) > 1:
        overlaps = [1 if nouns[i] & nouns[i + 1] else 0 for i in range(len(nouns) - 1)]
        add("coh", "Noun overlap, adjacent", sum(overlaps) / len(overlaps), "python-heuristic")
        arg = [len(nouns[i] & nouns[i + 1]) / max(1, len(nouns[i] | nouns[i + 1])) for i in range(len(nouns) - 1)]
        add("coh", "Argument overlap", sum(arg) / len(arg), "python-heuristic")
        sims = [_cos(bags[i], bags[i + 1]) for i in range(len(bags) - 1)]
        add("coh", "Sentence similarity mean", sum(sims) / len(sims))
        add("coh", "Sentence similarity SD", statistics.pstdev(sims))
    pbags = [Counter(w.lower() for w in _words(p.text) if w.lower() not in STOP and len(w) > 2) for p in paragraphs]
    if len(pbags) > 1:
        psims = [_cos(pbags[i], pbags[i + 1]) for i in range(len(pbags) - 1)]
        add("coh", "Paragraph similarity", sum(psims) / len(psims))
        head = sum(pbags[: max(1, len(pbags) // 5)], Counter())
        tail = sum(pbags[-max(1, len(pbags) // 5):], Counter())
        add("coh", "Topic drift start→end", 1 - _cos(head, tail))
    for name, phrases in CONNECTIVES.items():
        add("coh", name, _per_k(_count_phrases(low, phrases), n_words), unit="/1k")
    seen_terms, given, new = set(), 0, 0
    for b in bags:
        for t in b:
            if t in seen_terms:
                given += 1
            else:
                new += 1
                seen_terms.add(t)
    add("coh", "Given/new ratio", given / max(1, new))

    # Information theory
    uni = Counter(toks)
    bi = Counter(zip(toks, toks[1:]))
    h1, h2 = _entropy(uni), _entropy(bi)
    add("info", "Unigram entropy", h1, unit="bits")
    add("info", "Bigram entropy", h2, unit="bits")
    add("info", "Conditional entropy", h2 - h1, unit="bits")
    add("info", "Redundancy", 1 - h1 / math.log2(V) if V > 1 else None)
    raw_bytes = text.encode("utf-8")
    if raw_bytes:
        add("info", "gzip ratio", len(gzip.compress(raw_bytes)) / len(raw_bytes))
        add("info", "bz2 ratio", len(bz2.compress(raw_bytes)) / len(raw_bytes))
        add("info", "lzma ratio", len(lzma.compress(raw_bytes)) / len(raw_bytes))
    # surprisal under an add-one bigram model of the paper itself (in-sample; stated in the method)
    surprisals, info_per_sentence = [], []
    for ws in sent_words:
        ws = [w.lower() for w in ws]
        bits = 0.0
        for a, b in zip(["<s>"] + ws, ws):
            p = (bi.get((a, b), 0) + 1) / (uni.get(a, 0) + V) if a != "<s>" else (uni.get(b, 0) + 1) / (N + V)
            s_bits = -math.log2(p)
            surprisals.append(s_bits)
            bits += s_bits
        info_per_sentence.append(bits)
    if surprisals:
        method = "python (add-one bigram model fitted to this paper; in-sample)"
        add("info", "Surprisal mean", sum(surprisals) / len(surprisals), method, unit="bits")
        add("info", "Surprisal SD", statistics.pstdev(surprisals), method, unit="bits")
        add("info", "Perplexity", 2 ** (sum(surprisals) / len(surprisals)), method)
        add("info", "Information per sentence", sum(info_per_sentence) / len(info_per_sentence), method, unit="bits")
    key = [w for w, _ in Counter(content).most_common(20)]
    sent_sets = [set(w.lower() for w in ws) for ws in sent_words]
    mis = []
    for i, a in enumerate(key):
        for b in key[i + 1:]:
            pa = sum(1 for s in sent_sets if a in s) / n_sent
            pb = sum(1 for s in sent_sets if b in s) / n_sent
            pab = sum(1 for s in sent_sets if a in s and b in s) / n_sent
            if pab and pa and pb:
                mis.append(math.log2(pab / (pa * pb)))
    add("info", "Key-term mutual info", sum(mis) / len(mis) if mis else None, unit="bits")

    # Stance (Hyland metadiscourse)
    hedges, boosters = _count_phrases(low, HEDGES), _count_phrases(low, BOOSTERS)
    add("stance", "Hedges", _per_k(hedges, n_words), unit="/1k")
    add("stance", "Boosters", _per_k(boosters, n_words), unit="/1k")
    add("stance", "Attitude markers", _per_k(_count_phrases(low, ATTITUDE), n_words), unit="/1k")
    add("stance", "Self-mentions", _per_k(_count_phrases(low, SELF), n_words), unit="/1k")
    add("stance", "Engagement markers", _per_k(_count_phrases(low, ENGAGEMENT), n_words), unit="/1k")
    add("stance", "Hedge:booster ratio", hedges / boosters if boosters else None)
    absolutes = _count_phrases(low, ABSOLUTES)
    add("stance", "Absolutes (always/never/proves)", _per_k(absolutes, n_words), unit="/1k")
    add("stance", "Certainty index", (boosters + absolutes) / max(1, boosters + absolutes + hedges))

    # Emotion and tone
    tone = []
    for ws in sent_words:
        lw_ = [w.lower() for w in ws]
        pos, neg = sum(w in POSITIVE for w in lw_), sum(w in NEGATIVE for w in lw_)
        tone.append((pos - neg) / max(1, pos + neg) if pos + neg else 0.0)
    add("emo", "Positive share", sum(1 for w in low_words if w in POSITIVE) / max(1, n_words), "python (small built-in lexicon)")
    add("emo", "Negative share", sum(1 for w in low_words if w in NEGATIVE) / max(1, n_words), "python (small built-in lexicon)")
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
        va = SentimentIntensityAnalyzer()
        comp = [va.polarity_scores(s.text)["compound"] for s in sentences]
        add("emo", "VADER compound", sum(comp) / len(comp), "library:vaderSentiment")
        tone = comp
    except Exception:
        pass

    # Citations and sources
    refs_block = re.split(r"\n#+\s*(?:references|bibliography|works cited|sources)\s*\n", raw or text, flags=re.I)
    refs = [ln for ln in refs_block[1].splitlines() if ln.strip()] if len(refs_block) > 1 else []
    add("cite", "References", len(refs))
    add("cite", "References per 1k words", _per_k(len(refs), n_words))
    dois = re.findall(r"\b10\.\d{4,9}/\S+", raw or text)
    add("cite", "DOI coverage", len({d for d in dois}) / len(refs) if refs else None)
    years = [int(y) for y in re.findall(r"\((1[6-9]\d\d|20[0-4]\d)\)|\b(?:1[6-9]\d\d|20[0-4]\d)\b(?=[a-z]?[.,;)])", " ".join(refs)) if y]
    if years:
        add("cite", "Median reference year", statistics.median(years))
        latest = max(years)
        add("cite", "Price index (last 5 yrs)", sum(1 for y in years if y >= latest - 5) / len(years))
    urls = len(re.findall(r"https?://", " ".join(refs)))
    add("cite", "Web share", urls / len(refs) if refs else None, "python-heuristic")
    scripture = re.findall(r"\b((?:[1-3]\s)?[A-Z][a-z]+)\.?\s+(\d{1,3}):(\d{1,3})", raw or text)
    ot = sum(1 for b, _, _ in scripture if b.lower().lstrip("123 ") in OT)
    nt = sum(1 for b, _, _ in scripture if b.lower().lstrip("123 ") in NT)
    add("cite", "Scripture references", ot + nt)
    add("cite", "OT:NT ratio", ot / nt if nt else None)

    # Math and formal proof
    eqs = re.findall(r"\$\$.+?\$\$|\$[^$\n]+\$|^\s*[\w\\()χ∫∇]+\s*=\s*.+$", raw or text, flags=re.S | re.M)
    add("math", "Equations", len(eqs), "python-heuristic")
    symbols = set(re.findall(r"\\[a-zA-Z]+|[α-ωΑ-Ωχ∇∫∑∂]", " ".join(eqs)))
    add("math", "Unique symbols", len(symbols), "python-heuristic")
    add("math", "Kill conditions stated", len(re.findall(r"kill condition|would be falsified|falsif(?:ied|y|iable) (?:if|by)", low)), "python-heuristic")
    add("math", "Testable predictions", len(re.findall(r"\bpredict(?:s|ion|ions|ed)?\b", low)), "python-heuristic")
    add("math", "Lean theorems linked", len(re.findall(r"\btheorem\s+\w+|\.lean\b", raw or text)), "python-heuristic")
    add("math", "Lean sorry count", len(re.findall(r"\bsorry\b", raw or text)), "python-heuristic")

    # Concept graph (co-occurrence of the top 60 content terms within sentences)
    top = [w for w, _ in Counter(content).most_common(60)]
    idx = {w: i for i, w in enumerate(top)}
    adj: dict[int, set[int]] = defaultdict(set)
    for s in sent_sets:
        present = [idx[w] for w in s if w in idx]
        for a in present:
            for b in present:
                if a != b:
                    adj[a].add(b)
    nodes = [i for i in range(len(top)) if adj.get(i)]
    edges = sum(len(v) for v in adj.values()) // 2
    if nodes:
        add("graph", "Concept nodes", len(nodes))
        add("graph", "Edges", edges)
        add("graph", "Density", 2 * edges / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0)
        cc = []
        for v in nodes:
            nb = list(adj[v])
            if len(nb) > 1:
                links = sum(1 for i, a in enumerate(nb) for b in nb[i + 1:] if b in adj[a])
                cc.append(2 * links / (len(nb) * (len(nb) - 1)))
        add("graph", "Clustering coefficient", sum(cc) / len(cc) if cc else 0)
        comps, seen_nodes, diam = 0, set(), 0
        for v in nodes:
            if v in seen_nodes:
                continue
            comps += 1
            stack = [v]
            while stack:
                x = stack.pop()
                if x not in seen_nodes:
                    seen_nodes.add(x)
                    stack.extend(adj[x] - seen_nodes)
        for v in nodes[:40]:
            dist, frontier = {v: 0}, [v]
            while frontier:
                nxt = []
                for x in frontier:
                    for y in adj[x]:
                        if y not in dist:
                            dist[y] = dist[x] + 1
                            nxt.append(y)
                frontier = nxt
            diam = max(diam, max(dist.values()))
        add("graph", "Connected components", comps)
        add("graph", "Diameter", diam)
        degrees = sorted(((len(adj[v]), top[v]) for v in nodes), reverse=True)
        add("graph", "Hub concepts", sum(1 for d, _ in degrees if d >= max(3, degrees[0][0] * 0.6)))
        pr = {v: 1 / len(nodes) for v in nodes}
        for _ in range(30):
            pr = {v: 0.15 / len(nodes) + 0.85 * sum(pr[u] / len(adj[u]) for u in adj[v]) for v in nodes}
        add("graph", "PageRank of thesis term", pr[idx[top[0]]] if top and idx[top[0]] in pr else None)

    # Obsidian
    src = raw or text
    add("obs", "Wikilinks out", len(re.findall(r"(?<!!)\[\[[^\]]+\]\]", src)))
    add("obs", "Embeds", len(re.findall(r"!\[\[[^\]]+\]\]", src)))
    add("obs", "Block references", len(re.findall(r"\^[\w-]{3,}\b|\[\[[^\]]*#\^", src)))
    fm = re.match(r"---\n(.*?)\n---", src, re.S)
    tags = set(re.findall(r"(?<![\w#])#([A-Za-z][\w/-]+)", src))
    if fm:
        tags |= set(re.findall(r"^\s*-\s*([\w/-]+)\s*$", fm.group(1), re.M)) if "tags:" in fm.group(1) else set()
    add("obs", "Tags", len(tags))
    wanted = ["title", "tags", "series", "status", "date", "aliases", "author"]
    add("obs", "Frontmatter completeness", sum(1 for k in wanted if fm and re.search(rf"^{k}\s*:", fm.group(1), re.M)) / len(wanted))
    heads = re.findall(r"^(#{1,6})\s", src, re.M)
    add("obs", "Heading depth", max((len(h) for h in heads), default=0))
    add("obs", "Callouts", len(re.findall(r"^>\s*\[!\w+\]", src, re.M)))

    extras = {"sentence_lengths": lengths, "zipf": zipf_pts[:2000], "tone": tone,
              "distributions": {"sentence_length": distribution(lengths), "tone": distribution(tone),
                                "information_per_sentence": distribution(info_per_sentence)}}
    return out, extras


def percentile(value: float, population: list[float]) -> float | None:
    """Rank percentile of value in population (0-100); None when fewer than 2 values."""
    if len(population) < 2:
        return None
    below = sum(1 for x in population if x < value)
    equal = sum(1 for x in population if x == value)
    return round(100 * (below + 0.5 * equal) / len(population), 1)
