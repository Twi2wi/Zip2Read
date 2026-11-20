# mod
import re
from dataclasses import dataclass, field

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}#{1,6}\s+\S")
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
LINK_RE = re.compile(r"(?<!\!)\[(?:\\.|[^\[\]\\])*\]\((?:\\.|[^()\\]|\([^()]*\))*\)")
IMAGE_RE = re.compile(r"!\[(?:\\.|[^\[\]\\])*\]\((?:\\.|[^()\\]|\([^()]*\))*\)")
WORD_RE = re.compile(r"\S+")


@dataclass
class MdScan:
    lines: list[str]
    inside: list[bool]
    blocks: list[tuple[int, int]]


@dataclass
class MdStats:
    path: str
    lines: int = 0
    words: int = 0
    chars: int = 0
    code: int = 0
    headings: int = 0
    links: int = 0
    images: int = 0


@dataclass
class Hit:
    line: int
    start: int
    end: int
    snippet: str


@dataclass
class FileHits:
    path: str
    hits: list[Hit] = field(default_factory=list)


def scan(text: str) -> MdScan:
    lines = text.splitlines()
    inside = [False] * len(lines)
    blocks: list[tuple[int, int]] = []
    marker = ""
    size = 0
    start = -1
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if marker:
            inside[i] = True
            if m:
                ch = m.group(1)[0]
                n = len(m.group(1))
                if ch == marker and n >= size and not m.group(2).strip():
                    blocks.append((start, i))
                    marker = ""
                    size = 0
                    start = -1
            continue
        if m:
            ch = m.group(1)[0]
            if ch == "`" and "`" in m.group(2):
                continue
            inside[i] = True
            marker = ch
            size = len(m.group(1))
            start = i
    if marker:
        blocks.append((start, len(lines) - 1))
    return MdScan(lines, inside, blocks)


def analyze(path: str, text: str) -> MdStats:
    sc = scan(text)
    headings = links = images = 0
    for i, line in enumerate(sc.lines):
        if sc.inside[i]:
            continue
        if HEADING_RE.match(line):
            headings += 1
        clean = INLINE_CODE_RE.sub("", line)
        links += len(LINK_RE.findall(clean))
        images += len(IMAGE_RE.findall(clean))
    return MdStats(
        path, len(sc.lines), len(WORD_RE.findall(text)), len(text),
        len(sc.blocks), headings, links, images
    )


def extract(text: str, kind: str) -> list[str]:
    sc = scan(text)
    if kind == "code":
        return ["\n".join(sc.lines[a:b + 1]) for a, b in sc.blocks]
    out: list[str] = []
    for i, line in enumerate(sc.lines):
        if sc.inside[i]:
            continue
        if kind == "headings":
            if HEADING_RE.match(line):
                out.append(line)
            continue
        clean = INLINE_CODE_RE.sub("", line)
        if kind == "links":
            out.extend(LINK_RE.findall(clean))
        elif kind == "images":
            out.extend(IMAGE_RE.findall(clean))
    return out