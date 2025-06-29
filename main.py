# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import json_repair

def parse_json(text):
    try:
        return json_repair.loads(text)
    except Exception as e:
        print("Error in parse_json Function")
        print(f"An error occurred: {e}")
        print(f"Error type: {type(e)}")
        
# تحميل مفتاح API
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# إنشاء التطبيق
app = FastAPI()

# موديل جيمناي عبر Langchain
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

# نموذج الإدخال
class WordsInput(BaseModel):
    words: List[str]

# البرومبت الأساسي
def build_prompt(words: List[str]) -> str:
    word_list = ', '.join(f'"{w}"' for w in words)
    return f"""
You will receive 5 words in any language. Your task is to generate 10 multiple-choice questions (2 per word).
Use a variety of question types, such as:
- Definition of the word.
- Synonym or alternative in the same language.
- Translation of the word.
- Contextual usage.
- Part of speech.

Each question must follow this JSON format:
[
  {{
    "question": "1. Your question here",
    "options": [
      "A. Option one",
      "B. Option two",
      "C. Option three",
      "D. Option four"
    ],
    "correct_answer": "2"
  }},
  ...
]

Rules:
- Return exactly 10 questions.
- All questions must relate to the provided words: {word_list}
- All options must be plausible.
- Only return the valid JSON array. No explanations.

Now here are the 5 input words: {word_list} ```json
"""

# نقطة النهاية (API Endpoint)
@app.get("/")
async def read_root():
    """Root endpoint returning basic API info."""
    return {"message": "Welcome Generating Quizes API For Turjuman is running. use /docs to try it out", "version": "1.0.0"}




@app.post("/generate-questions/")
async def generate_questions(data: WordsInput):
    if len(data.words) != 5:
        raise HTTPException(status_code=400, detail="Exactly 5 words are required.")

    prompt = build_prompt(data.words)
    

    try:
        response = llm.invoke(prompt)
        # محاولة تحويل النص الناتج إلى JSON
        #import json
        #questions = json.loads(response)
        print('generated questions succesfully')
        questions = parse_json(response.content)
        if not questions:
            raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON.")
        
        return questions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
