from pydantic import BaseModel

class KeywordRequest(BaseModel):
    category: str
    location: str
    
class GetNewsRequest(BaseModel):
    news_uuid: str