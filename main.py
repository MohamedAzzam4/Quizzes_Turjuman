from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import json_repair
from fastapi.middleware.cors import CORSMiddleware
import os
import openai

# تحميل متغيرات البيئة
load_dotenv()
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
llm = 'openai/gpt-4o-mini'

# إعداد موديل Gemini
#llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

#from dotenv import load_dotenv
# Load API key from environment variables
#load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(
    api_key= ROUTER_API_KEY,
    base_url= "https://router.requesty.ai/v1",
    default_headers= {"Authorization": f"Bearer {ROUTER_API_KEY}"}
)


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
The Correct Answer must be the char of the correct choice like A, B, C or D
like the following : "correct_answer": "B"

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
    "correct_answer": "B"
  }},
  ...
]

Rules:
- Return exactly 10 questions.
- All questions must relate to the following words: {word_list}
- All options must be plausible and only one correct.
- Only return a clean valid JSON array. No explanation or extra text.
- Never return a Number in the correct_answer.

Words: {word_list}

```json
"""

# محاولة تصحيح وتحويل النص إلى JSON
def parse_json(text):
    try:
        return json_repair.loads(text)
    except:
        return None

app = FastAPI()

origins = [
    "https://www.turjuman.online",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """Root endpoint returning basic API info."""
    return {"message": "Welcome ;) Quizes Generator API For Turjuman is running."}


# نقطة النهاية للـ API
@app.post("/generate-questions/")
async def generate_questions(request: QuizRequest):
    if len(request.words) != 5:
        raise HTTPException(status_code=400, detail="Exactly 5 words are required.")
    else:
        print('input is precise')

    prompt = build_prompt(request.words, request.srcLang)
    print('Builded Prompt')

    try:
        #response = llm.invoke(prompt)
        try:
            print("Sending request to the model...")
            response = client.chat.completions.create(
                model = llm,
                messages= [ {"role": "user", "content": prompt} ] 
            )
            print('the prompt was sent to the model')

            if not response.choices:
                raise Exception("No response choices found.")

            llm_response = response.choices[0].message.content
            
            
        except openai.OpenAIError as e:
            print(f"Model API error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        #response_text = response.content
        
        questions = parse_json(llm_response)

        if not questions:
            raise HTTPException(status_code=500, detail="Failed to parse response as JSON.")

        return questions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
