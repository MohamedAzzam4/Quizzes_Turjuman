from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import json_repair

# تحميل متغيرات البيئة
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# إعداد FastAPI
app = FastAPI()

# إعداد موديل Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

# نموذج الإدخال
class QuizRequest(BaseModel):
    srcLang: str = Field(..., description="The language in which questions should be generated.")
    words: List[str] = Field(..., min_items=5, max_items=5, description="List of 5 words.")

# بناء البرومبت
def build_prompt(words: List[str], language: str) -> str:
    word_list = ', '.join(f'"{w}"' for w in words)
    return f"""
You will receive 5 words. Your task is to generate 10 multiple-choice quiz questions (2 per word).

All output must be written in **{language}**.

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
- All questions must relate to the following words: {word_list}
- All options must be plausible and only one correct.
- Only return a clean valid JSON array. No explanation or extra text.

Words: {word_list}
"""

# محاولة تصحيح وتحويل النص إلى JSON
def parse_json(text):
    try:
        return json_repair.loads(text)
    except:
        return None

# نقطة النهاية للـ API
@app.post("/generate-questions/")
async def generate_questions(request: QuizRequest):
    if len(request.words) != 5:
        raise HTTPException(status_code=400, detail="Exactly 5 words are required.")

    prompt = build_prompt(request.words, request.srcLang)

    try:
        response = llm.invoke(prompt)
        response_text = response.content
        questions = parse_json(response_text)

        if not questions:
            raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON.")

        return questions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
