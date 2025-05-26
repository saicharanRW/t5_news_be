from pydantic import BaseModel

class KeywordRequest(BaseModel):
    category: str
    location: str