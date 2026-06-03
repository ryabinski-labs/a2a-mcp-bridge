"""A tiny bundled document corpus.

The research tools search and fetch from this local corpus instead of the live
internet, so the demo is deterministic, offline, and side-effect free. Swapping
in a real search API is a documented extension point — only the two functions in
``research_tools.py`` need to change.
"""

from __future__ import annotations

CORPUS: dict[str, dict[str, str]] = {
    "remote-work-productivity": {
        "title": "Remote work and team productivity: a 2025 field review",
        "body": (
            "Studies across distributed engineering teams report that remote work "
            "raises focused output for individual contributors by 8-13% while "
            "lengthening cross-team decision cycles. The strongest predictor of "
            "sustained productivity is asynchronous written communication paired "
            "with a small number of synchronous rituals. Burnout risk rises when "
            "meeting load is simply ported from the office to video calls. "
            "Companies named Acme Corp and Globex report the best retention when "
            "core collaboration hours are kept under three per day."
        ),
    },
    "async-communication": {
        "title": "Asynchronous communication patterns for distributed teams",
        "body": (
            "Asynchronous communication shifts coordination from interruption to "
            "documentation. Teams using decision records and written proposals "
            "cut meeting time by roughly 30%. The trade-off is higher up-front "
            "writing cost and slower escalation for genuinely urgent issues. "
            "Researchers Jane Doe and Carlos Ruiz recommend a tiered model: async "
            "by default, sync for conflict, live for crisis."
        ),
    },
    "meeting-overload": {
        "title": "Meeting overload: causes and measurable remedies",
        "body": (
            "Meeting overload correlates strongly with low autonomy and unclear "
            "ownership. Organizations that introduced no-meeting days and "
            "default-30-minute limits recovered an estimated 4-6 focus hours per "
            "engineer per week. The city of Helsinki piloted meeting-free Fridays "
            "across municipal IT with positive reported morale."
        ),
    },
    "hybrid-office-policy": {
        "title": "Hybrid office policies and their second-order effects",
        "body": (
            "Mandated in-office days improve ad-hoc mentorship but reduce reported "
            "deep-work satisfaction. The most durable hybrid policies tie office "
            "presence to a purpose (onboarding, planning) rather than a fixed "
            "quota. Microsoft and Atlassian have published differing conclusions, "
            "underscoring that context dominates."
        ),
    },
}


def search(query: str, limit: int = 3) -> list[dict[str, str]]:
    """Naive deterministic keyword scorer over the corpus."""
    terms = [t for t in _tokenize(query) if len(t) > 2]
    scored: list[tuple[int, str]] = []
    for doc_id, doc in CORPUS.items():
        haystack = _tokenize(doc["title"] + " " + doc["body"] + " " + doc_id)
        score = sum(haystack.count(term) for term in terms)
        # Always give every doc a tiny floor so an empty/odd query still returns
        # deterministic results rather than nothing.
        score = score * 10 + 1
        scored.append((score, doc_id))
    scored.sort(key=lambda x: (-x[0], x[1]))
    hits = []
    for score, doc_id in scored[:limit]:
        hits.append(
            {
                "doc_id": doc_id,
                "title": CORPUS[doc_id]["title"],
                "score": str(score),
            }
        )
    return hits


def fetch(doc_id: str) -> dict[str, str] | None:
    doc = CORPUS.get(doc_id)
    if doc is None:
        return None
    return {"doc_id": doc_id, "title": doc["title"], "body": doc["body"]}


def _tokenize(text: str) -> list[str]:
    return [w.strip(".,:;()").lower() for w in text.split()]
