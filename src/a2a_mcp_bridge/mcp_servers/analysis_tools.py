"""Analysis MCP server (stdio).

Exposes the *tools* the Analyst agent uses to turn raw findings into a
structured analysis. These are deterministic, dependency-free text utilities so
the demo behaves identically everywhere.
"""

from __future__ import annotations

import re
from collections import Counter

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("analysis-tools")

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")
_SENT_RE = re.compile(r"(?<=[.!?])\s+")
_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "but",
    "not",
    "you",
    "your",
    "their",
    "they",
    "them",
    "when",
    "while",
    "into",
    "than",
    "then",
    "over",
    "under",
    "more",
    "most",
    "some",
    "such",
    "each",
    "per",
    "across",
    "report",
    "reports",
    "reported",
}


@mcp.tool()
def summarize(text: str, max_sentences: int = 3) -> str:
    """Extractive summary: the highest-signal sentences from ``text``."""
    sentences = [s.strip() for s in _SENT_RE.split(text) if s.strip()]
    if len(sentences) <= max_sentences:
        return text.strip()
    freqs = _word_frequencies(text)
    scored = []
    for idx, sent in enumerate(sentences):
        words = [w.lower() for w in _WORD_RE.findall(sent)]
        score = sum(freqs.get(w, 0) for w in words) / (len(words) or 1)
        scored.append((score, idx, sent))
    top = sorted(scored, key=lambda x: -x[0])[:max_sentences]
    ordered = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return " ".join(ordered)


@mcp.tool()
def score_relevance(text: str, query: str) -> str:
    """Score 0-100 how relevant ``text`` is to ``query`` (deterministic)."""
    text_words = Counter(w.lower() for w in _WORD_RE.findall(text))
    query_terms = {w.lower() for w in _WORD_RE.findall(query) if w.lower() not in _STOPWORDS}
    if not query_terms:
        return "relevance: 0/100 (empty query)"
    matched = sum(1 for term in query_terms if text_words.get(term, 0) > 0)
    hit_mass = sum(text_words.get(term, 0) for term in query_terms)
    coverage = matched / len(query_terms)
    density = min(hit_mass / (sum(text_words.values()) or 1) * 8, 1.0)
    score = round((0.7 * coverage + 0.3 * density) * 100)
    return (
        f"relevance: {score}/100 "
        f"(matched {matched}/{len(query_terms)} query terms, {hit_mass} occurrences)"
    )


@mcp.tool()
def extract_entities(text: str, limit: int = 8) -> str:
    """Extract likely named entities (capitalized multi-word spans)."""
    candidates = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", text)
    counts: Counter[str] = Counter()
    for cand in candidates:
        # Drop single common sentence-initial words; keep multiword or repeated.
        if " " in cand or len(cand) > 3:
            counts[cand] += 1
    if not counts:
        return "entities: (none found)"
    top = [name for name, _ in counts.most_common(limit)]
    return "entities: " + ", ".join(top)


def _word_frequencies(text: str) -> dict[str, int]:
    """Frequency of content words (stopwords excluded), used to score sentences."""
    freqs: Counter[str] = Counter()
    for word in _WORD_RE.findall(text.lower()):
        if word not in _STOPWORDS and len(word) > 2:
            freqs[word] += 1
    return dict(freqs)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
