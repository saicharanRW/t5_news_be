import os
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Any
from langchain.output_parsers import PydanticOutputParser

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class ImageMetadata(BaseModel):
    src: Any  = Field(description="The main image src URL")
    data_src: Any  = Field(description="The data-src image URL")
    alt: Any  = Field(description="The alt text of the main image")

parser = PydanticOutputParser(pydantic_object=ImageMetadata)

def find_main_img(scraped_content):
    url = scraped_content['url']
    title = scraped_content['title']
    images = scraped_content['images']

    prompt = f"""
    You are an assistant that selects the most relevant image for a news article.
    
    News URL: {url}
    Title: {title}
    
    Images Metadata:
    """
    
    for img in images:
        img_src = f"""
        - Image:
            SRC: {img['url']}
            Data-src: {img['data_src']}
            Alt: {img['alt']}
            """
        prompt += img_src

    prompt += f"""
    Task: Based on the title and image metadata, return ONLY the most relevant image in JSON format with the following schema:
    {parser.get_format_instructions()}
    """

    response = model.generate_content(prompt)

    try:
        parsed_result = parser.parse(response.text)
        return parsed_result
    except Exception as e:
        print("Parsing failed. Raw output:\n", response.text)
        raise e