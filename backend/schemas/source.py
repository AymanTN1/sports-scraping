from pydantic import BaseModel, ConfigDict


class SourceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    language: str | None = None
    credibility_score: float
