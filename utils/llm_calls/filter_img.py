import os
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Any, List
from langchain.output_parsers import PydanticOutputParser

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class ImageMetadata(BaseModel):
    img_url: Any  = Field(description="Image url which is relevent to the given News URL and Title")
    
class ImageMetadataList(BaseModel):
    images: List[ImageMetadata]


parser = PydanticOutputParser(pydantic_object=ImageMetadataList)

def filter_img(scraped_content):
    url = scraped_content['url']
    title = scraped_content['title']
    images = scraped_content['images']

    prompt = f"""
    You are an assistant that selects the most relevant image url for a news article.
    
    News URL: {url}
    Title: {title}
    
    Images Metadata:
    """
    
    for img in images:
        img_src = f"""
        - Images:
            IMAGE URL: {img}
        """
        prompt += img_src

    prompt += f"""
    Task: Based on the title and image url, filter out the unwanted image urls like logo, icons, advertisements, ete.. \n
    Keep only the image urls which is relavent to the News URL and Title, also remove the duplictes image urls
    {parser.get_format_instructions()}
    """

    response = model.generate_content(prompt)

    try:
        parsed_result = parser.parse(response.text)
        return parsed_result
    except Exception as e:
        print("Parsing failed. Raw output:\n", response.text)
        raise e