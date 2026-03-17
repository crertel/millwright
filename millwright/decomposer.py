"""Query decomposition: Claude-based and mock implementations."""

from abc import ABC, abstractmethod


class Decomposer(ABC):
    @abstractmethod
    def decompose(self, query: str) -> list[str]:
        """Break a query into atomic subqueries."""
        ...


class MockDecomposer(Decomposer):
    """Deterministic decomposer that splits on common conjunctions and punctuation."""

    def decompose(self, query: str) -> list[str]:
        # Split on " and ", " then ", commas, semicolons
        parts = [query]
        for sep in [" and then ", " and ", " then ", ";", ","]:
            new_parts = []
            for p in parts:
                new_parts.extend(p.split(sep))
            parts = new_parts

        result = [p.strip() for p in parts if p.strip()]
        return result if result else [query]


class ClaudeDecomposer(Decomposer):
    """Uses Claude to decompose queries into atomic subqueries."""

    def __init__(self, api_key: str | None = None):
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)

    def decompose(self, query: str) -> list[str]:
        response = self._client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": (
                    "Decompose this tool-use query into atomic subqueries. "
                    "Return one subquery per line, nothing else.\n\n"
                    f"Query: {query}"
                ),
            }],
        )
        text = response.content[0].text
        parts = [line.strip() for line in text.strip().split("\n") if line.strip()]
        return parts if parts else [query]
