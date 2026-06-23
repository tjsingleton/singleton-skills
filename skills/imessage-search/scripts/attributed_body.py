#!/usr/bin/env python3
"""Decode the iMessage ``attributedBody`` column to plain text.

On modern macOS (Ventura+), ``message.text`` is NULL for almost every row; the
body lives in the ``attributedBody`` BLOB as an ``NSAttributedString`` serialized
in Apple's "typedstream" (a.k.a. ``streamtyped``) binary format. A search that
only reads ``message.text`` therefore misses ~99% of messages.

Two decode tiers:

* **Tier 1 — pytypedstream** (``pip install pytypedstream``, import ``typedstream``):
  a proper structural deserializer. Most robust on multi-run / rich messages.
  Optional: if the package is not installed, we silently fall back to Tier 2.
* **Tier 2 — dependency-free heuristic**: scans the raw blob for the text run.
  Handles the UTF-16LE-BOM variant and the ``0x81`` 2-byte length prefix used for
  strings longer than 255 bytes.

Keeping Tier 2 means the skill works with the Python standard library alone; the
library is a pure-upgrade when present, never a hard requirement.
"""

from __future__ import annotations

import struct

# U+FFFC OBJECT REPLACEMENT CHARACTER marks each attachment position in the body.
OBJ_REPLACEMENT = "￼"


def _decode_with_library(blob: bytes) -> str | None:
    """Tier 1: pytypedstream. Returns None if the lib is absent or parsing fails."""
    try:
        from typedstream.stream import TypedStreamReader
    except Exception:
        return None
    try:
        for event in TypedStreamReader.from_data(blob):
            if isinstance(event, bytes):
                text = event.decode("utf-8", errors="replace")
                if text:
                    return text
    except Exception:
        return None
    return None


def _decode_heuristic(blob: bytes) -> str | None:
    """Tier 2: dependency-free byte scan.

    Layout after the ``NSString`` marker in a typedstream attributedBody:

        [..]"NSString"            8-byte class name
        [0x01 0x94 0x84 0x01 0x2b] 5-byte preamble (class version + UTF-8 tag)
        [length]                   1 byte, OR 0x81 + uint16-LE when > 255 bytes
        [UTF-8 text]               ``length`` bytes

    Some messages instead store a UTF-16LE string prefixed with a BOM; handle
    that first.
    """
    if not blob:
        return None

    # UTF-16LE BOM variant (messages whose text column is empty; fixed upstream
    # in imsg v0.6.0). The BOM can appear at the head of the run.
    bom = blob.find(b"\xff\xfe")
    if bom != -1:
        tail = blob[bom + 2:]
        # Trim trailing typedstream framing bytes that aren't valid UTF-16.
        if len(tail) >= 2:
            usable = tail[: len(tail) - (len(tail) % 2)]
            decoded = usable.decode("utf-16-le", errors="ignore").strip("\x00")
            if decoded.strip():
                return decoded

    marker = b"NSString"
    pos = blob.find(marker)
    if pos == -1:
        return None

    # Skip the 8-byte marker and the 5-byte preamble to land on the length byte.
    length_off = pos + len(marker) + 5
    if length_off >= len(blob):
        return None

    first = blob[length_off]
    if first == 0x81:
        if length_off + 3 > len(blob):
            return None
        str_len = struct.unpack_from("<H", blob, length_off + 1)[0]
        text_off = length_off + 3
    else:
        str_len = first
        text_off = length_off + 1

    text_end = min(text_off + str_len, len(blob))
    raw = blob[text_off:text_end]
    text = raw.decode("utf-8", errors="replace")
    return text or None


def decode_attributed_body(blob: bytes | memoryview | None) -> str | None:
    """Decode an attributedBody blob to plain text, or None if it can't be read.

    Tries the pytypedstream library first, then the dependency-free heuristic.
    """
    if blob is None:
        return None
    if isinstance(blob, memoryview):
        blob = bytes(blob)
    if not blob:
        return None
    return _decode_with_library(blob) or _decode_heuristic(blob)


def message_text(text: str | None, attributed_body: bytes | None) -> str:
    """Prefer the plain ``text`` column; fall back to decoding ``attributedBody``.

    Always returns a string (possibly empty) so callers can filter uniformly.
    """
    if text:
        return text
    decoded = decode_attributed_body(attributed_body)
    return decoded or ""


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    import sqlite3
    import sys
    from pathlib import Path

    db = sys.argv[1] if len(sys.argv) > 1 else str(
        Path.home() / "Library/Messages/chat.db"
    )
    conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT text, attributedBody FROM message "
        "WHERE attributedBody IS NOT NULL ORDER BY date DESC LIMIT 10"
    ).fetchall()
    for r in rows:
        print(repr(message_text(r["text"], r["attributedBody"])[:120]))
    conn.close()
