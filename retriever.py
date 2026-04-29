from dataclasses import dataclass
from pathlib import Path
import re


STOP_WORDS = {
    "i", "have", "has", "a", "an", "the", "and", "or", "to", "for", "of", "in",
    "on", "my", "with", "is", "are", "today", "need", "needs", "he", "she",
    "it", "they", "them", "his", "her", "their", "this", "that", "also"
}

KEYWORD_BONUSES = {
    "medicine": 4,
    "medication": 4,
    "pill": 4,
    "pills": 4,
    "dose": 4,
    "dosage": 4,
    "feeding": 3,
    "feed": 3,
    "water": 3,
    "walking": 3,
    "walk": 3,
    "litter": 3,
    "grooming": 3,
    "groom": 3,
    "emergency": 5,
    "seizure": 5,
    "vomiting": 5,
    "blood": 5,
    "breathing": 5,
}


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    heading: str
    text: str
    score: int

    def preview(self, max_lines: int = 8) -> str:
        """
        Return a readable preview for terminal/debug output.

        This preserves markdown line breaks and bullet formatting.
        It only limits the number of displayed lines.
        """
        lines = [line.rstrip() for line in self.text.strip().splitlines()]

        visible_lines = lines[:max_lines]

        if len(lines) > max_lines:
            visible_lines.append("...")

        return "\n".join(visible_lines)


def normalize_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {word for word in words if word not in STOP_WORDS and len(word) > 2}


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """
    Split a markdown document into sections based on level-2 headings.

    Example:
        ## Feeding
        text...

    becomes:
        ("Feeding", "text...")
    """
    sections: list[tuple[str, str]] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_heading, body))
                current_lines = []

            current_heading = stripped.replace("## ", "", 1).strip()

        elif not stripped.startswith("# "):
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_heading, body))

    return sections


def load_knowledge_chunks(folder: str = "knowledge") -> list[RetrievedChunk]:
    knowledge_path = Path(folder)

    if not knowledge_path.exists():
        return []

    chunks: list[RetrievedChunk] = []

    for path in sorted(knowledge_path.glob("*.md")):
        file_text = path.read_text(encoding="utf-8")
        sections = split_markdown_sections(file_text)

        for heading, body in sections:
            chunks.append(
                RetrievedChunk(
                    source=path.name,
                    heading=heading,
                    text=body,
                    score=0,
                )
            )

    return chunks


def score_chunk(query: str, chunk: RetrievedChunk) -> int:
    query_words = normalize_words(query)
    chunk_words = normalize_words(f"{chunk.heading} {chunk.text}")

    overlap_score = len(query_words.intersection(chunk_words))

    lowered_query = query.lower()
    lowered_chunk = f"{chunk.heading} {chunk.text}".lower()

    keyword_bonus = 0
    for keyword, bonus in KEYWORD_BONUSES.items():
        if keyword in lowered_query and keyword in lowered_chunk:
            keyword_bonus += bonus

    return overlap_score + keyword_bonus


def retrieve_context(
    query: str,
    top_k: int = 3,
    folder: str = "knowledge",
    min_score: int = 1,
) -> list[RetrievedChunk]:
    """
    Retrieve the most relevant knowledge chunks for a user query.

    This is a simple keyword-based retriever. It is intentionally deterministic,
    easy to test, and does not require an external vector database.
    """
    if not query.strip():
        return []

    chunks = load_knowledge_chunks(folder)
    scored_chunks: list[RetrievedChunk] = []

    for chunk in chunks:
        final_score = score_chunk(query, chunk)

        if final_score >= min_score:
            scored_chunks.append(
                RetrievedChunk(
                    source=chunk.source,
                    heading=chunk.heading,
                    text=chunk.text,
                    score=final_score,
                )
            )

    scored_chunks.sort(key=lambda chunk: chunk.score, reverse=True)
    return scored_chunks[:top_k]


def format_retrieval_results(results: list[RetrievedChunk], max_lines_per_chunk: int = 8) -> str:
    if not results:
        return "No relevant knowledge chunks found."

    output_blocks = []

    for index, result in enumerate(results, start=1):
        block = (
            f"[{index}] {result.source} — {result.heading}\n"
            f"Score: {result.score}\n"
            f"{result.preview(max_lines=max_lines_per_chunk)}"
        )
        output_blocks.append(block)

    return "\n\n" + ("\n" + "-" * 60 + "\n").join(output_blocks)


if __name__ == "__main__":
    test_query = "My dog needs medicine, feeding, and walking today."
    results = retrieve_context(test_query)

    print(f"Query: {test_query}")
    print(format_retrieval_results(results))