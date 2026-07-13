"""The output contract. Every routing result must satisfy this — it is the single
source of truth for the response shape, used both to request structured output from
the LLM and to re-validate what comes back."""

from enum import Enum

from pydantic import BaseModel, Field

from router.config import CATEGORY_NAMES

# Build the category enum dynamically from taxonomy.yaml so it can never drift
# from the actual configured categories.
Category = Enum("Category", {name: name for name in CATEGORY_NAMES}, type=str)

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Sentiment(str, Enum):
    angry = "angry"
    neutral = "neutral"
    positive = "positive"


class RoutingResult(BaseModel):
    """Validated routing decision for a single ticket."""

    schema_version: str = "1.0"
    category: Category = Field(description="One of the categories defined in taxonomy.yaml")
    priority: Priority
    assigned_team: str = Field(description="Team responsible, derived from category")
    reasoning: str = Field(description="One sentence citing the decisive signal(s)")
    confidence: float = Field(ge=0.0, le=1.0, description="Model's confidence 0-1")
    needs_clarification: bool = False
    clarifying_question: str | None = None
    detected_language: str = "en"
    sentiment: Sentiment = Sentiment.neutral
    fallback_used: bool = False
