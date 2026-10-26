import re
import unicodedata


class TextCleaner:
    """Cleans, sanitizes, and normalizes raw text for robust chunking and retrieval."""

    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ""

        # 1. Normalize Unicode characters (e.g. compatibility characters)
        normalized = unicodedata.normalize("NFKC", text)

        # Normalize curly / smart quotes to standard ASCII quotes
        normalized = (
            normalized.replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )


        # 2. Standardize line endings (\r\n and \r -> \n)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Strip non-printable / control characters (except newline, tab)
        normalized = "".join(
            ch for ch in normalized if ch in ("\n", "\t") or unicodedata.category(ch)[0] != "C"
        )

        # 4. Collapse runs of horizontal spaces/tabs (preserve newlines)
        lines = []
        for line in normalized.split("\n"):
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(cleaned_line)

        # 5. Collapse excessive vertical blank lines (max 2 consecutive newlines)
        joined = "\n".join(lines)
        joined = re.sub(r"\n{3,}", "\n\n", joined)

        return joined.strip()
