import re

STOPWORDS = set("""
a an the and or but if so to of in on at for with from by as is are was were be been being am do does did done
i i'm i'll i've i'd we we're we'll we've you you're they it it's that this these those there here what who whom whose
when where why how which not no yes yeah okay ok well just really actually still very too also going gonna gotta
my our your their his her its me us him them can could should would will shall may might must have has had
about into over than then now up out get got let lets let's one some any all more most much many like think
concern concerned worried worry biggest main risk sure maybe probably perhaps guess anyway today tomorrow
""".split())


def normalize(text: str) -> str:
    return text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def split_sentences(text: str) -> list[str]:
    text = normalize(text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def content_tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9+#.-]*", normalize(text).lower())
    return [w.strip(".-") for w in words if w.strip(".-") not in STOPWORDS and len(w) > 2]


def tokens_match(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) < 5 or len(b) < 5:
        return False
    n = min(len(a), len(b), 6)
    return a[:n] == b[:n]


def overlap(a: list[str], b: list[str]) -> int:
    return sum(1 for x in set(a) if any(tokens_match(x, y) for y in set(b)))


def fmt_ts(ms: int) -> str:
    s = max(0, ms) // 1000
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
