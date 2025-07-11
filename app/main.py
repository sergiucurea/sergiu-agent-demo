from fastapi import FastAPI, Depends, Request, Query
from sqlalchemy.orm import Session
import models
import database
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from langchain_community.chat_models import ChatOpenAI
import json
from sse_starlette.sse import EventSourceResponse
import asyncio
import re
from dotenv import load_dotenv
from image_search_tool import ImageSearchTool

load_dotenv(dotenv_path="/app/.env")

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/figures")
def get_figures(db: Session = Depends(get_db)):
    return db.query(models.HistoricalFigure).all()

@app.get("/health")
def health():
    return {"status": "ok"}

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/heroes", response_class=HTMLResponse)
def show_heroes(request: Request):
    db = database.SessionLocal()
    heroes = db.query(models.HistoricalFigure).all()
    db.close()
    return templates.TemplateResponse("heroes.html", {"request": request, "heroes": heroes})

@app.post("/generate_descriptions")
def generate_descriptions():
    # Set up Groq LLM via OpenAI-compatible API
    llm = ChatOpenAI(
        model_name="llama3-70b-8192",
        temperature=0.7,
        max_tokens=512,
        openai_api_key=os.getenv("GROQ_API_KEY"),
        openai_api_base="https://api.groq.com/openai/v1"
    )
    db = database.SessionLocal()
    heroes = db.query(models.HistoricalFigure).all()
    updated = []
    for hero in heroes:
        if not hero.description or len(hero.description.split()) < 20:
            prompt = (
                f"Write a detailed, engaging, and historically accurate 5-10 sentence description "
                f"about {hero.name}. Focus on their life, achievements, and why they are remembered."
            )
            try:
                response = llm.invoke(prompt)
                hero.description = response.content
                db.add(hero)
                updated.append(hero.name)
            except Exception as e:
                print(f"Failed to generate description for {hero.name}: {e}")
    db.commit()
    db.close()
    return {"updated": updated}

def extract_json_from_response(text):
    match = re.search(r'\{[\s\S]*?\}', text)
    if match:
        return match.group(0)
    return None

@app.get("/hero_details")
def hero_details(name: str = Query(..., description="Name of the hero")):
    db = database.SessionLocal()
    hero = db.query(models.HistoricalFigure).filter(models.HistoricalFigure.name == name).first()
    llm = ChatOpenAI(
        model_name="llama3-70b-8192",
        temperature=0.7,
        max_tokens=512,
        openai_api_key=os.getenv("GROQ_API_KEY"),
        openai_api_base="https://api.groq.com/openai/v1"
    )
    image_tool = ImageSearchTool()

    # If hero exists but description is too short, update it
    if hero and (not hero.description or len(hero.description.split()) < 20):
        prompt = (
            f"Write a detailed, engaging, and historically accurate 5-10 sentence description "
            f"about {name}. Focus on their life, achievements, and why they are remembered."
        )
        try:
            response = llm.invoke(prompt)
            description = response.content
            # Use image search tool for the picture_url
            picture_url = image_tool.run({"query": name, "max_results": 1})
            if isinstance(picture_url, list):
                picture_url = picture_url[0] if picture_url else ""
            hero.description = description
            hero.picture_url = picture_url
            db.add(hero)
            db.commit()
            db.close()
            return {"answer": description, "picture_url": picture_url, "source": "groq+tool", "hero": name}
        except Exception as e:
            db.close()
            return {"error": f"Failed to generate description for {name}: {e}"}

    if hero:
        db.close()
        return {"answer": hero.description, "picture_url": hero.picture_url, "source": "db", "hero": hero.name}

    # If not found, use Groq LLM to generate description and tool for image
    prompt = (
        f"Write a detailed, engaging, and historically accurate 5-10 sentence description "
        f"about {name}. Focus on their life, achievements, and why they are remembered."
    )
    try:
        response = llm.invoke(prompt)
        description = response.content
        picture_url = image_tool.run({"query": name, "max_results": 1})
        if isinstance(picture_url, list):
            picture_url = picture_url[0] if picture_url else ""
        new_hero = models.HistoricalFigure(name=name, description=description, picture_url=picture_url)
        db.add(new_hero)
        db.commit()
        db.close()
        return {"answer": description, "picture_url": picture_url, "source": "groq+tool", "hero": name}
    except Exception as e:
        db.close()
        return {"error": f"Failed to generate description for {name}: {e}"}

@app.get("/hero_trace")
async def hero_trace(name: str = Query(..., description="Name of the hero")):
    async def event_generator():
        trace = []
        db = database.SessionLocal()
        yield f"Looking up '{name}' in the database."
        hero = db.query(models.HistoricalFigure).filter(models.HistoricalFigure.name == name).first()
        llm = ChatOpenAI(
            model_name="llama3-70b-8192",
            temperature=0.7,
            max_tokens=512,
            openai_api_key=os.getenv("GROQ_API_KEY"),
            openai_api_base="https://api.groq.com/openai/v1"
        )
        image_tool = ImageSearchTool()
        await asyncio.sleep(0.2)
        if hero and (not hero.description or len(hero.description.split()) < 20):
            yield "Found hero in DB, but description is too short. Calling Groq to upgrade description."
            prompt = (
                f"Write a detailed, engaging, and historically accurate 5-10 sentence description "
                f"about {name}. Focus on their life, achievements, and why they are remembered."
            )
            try:
                yield "Calling Groq LLM..."
                response = await asyncio.get_event_loop().run_in_executor(None, llm.invoke, prompt)
                await asyncio.sleep(0.2)
                description = response.content
                yield "Searching for image using image search tool..."
                picture_url = await asyncio.get_event_loop().run_in_executor(None, image_tool.run, {"query": name, "max_results": 1})
                if isinstance(picture_url, list):
                    picture_url = picture_url[0] if picture_url else ""
                hero.description = description
                hero.picture_url = picture_url
                db.add(hero)
                db.commit()
                db.close()
                yield "Updated hero in DB with new description and picture_url."
                yield f"FINAL_ANSWER::" + json.dumps({"answer": description, "picture_url": picture_url, "source": "groq+tool", "hero": name})
                return
            except Exception as e:
                db.close()
                yield f"Error: {e}"
                yield f"FINAL_ANSWER::" + json.dumps({"error": f"Failed to generate description for {name}: {e}"})
                return
        if hero:
            db.close()
            yield "Found hero in DB with sufficient description."
            yield f"FINAL_ANSWER::" + json.dumps({"answer": hero.description, "picture_url": hero.picture_url, "source": "db", "hero": hero.name})
            return
        yield "Hero not found in DB. Generating description and searching for image."
        prompt = (
            f"Write a detailed, engaging, and historically accurate 5-10 sentence description "
            f"about {name}. Focus on their life, achievements, and why they are remembered."
        )
        try:
            yield "Calling Groq LLM..."
            response = await asyncio.get_event_loop().run_in_executor(None, llm.invoke, prompt)
            await asyncio.sleep(0.2)
            description = response.content
            yield "Searching for image using image search tool..."
            picture_url = await asyncio.get_event_loop().run_in_executor(None, image_tool.run, {"query": name, "max_results": 1})
            if isinstance(picture_url, list):
                picture_url = picture_url[0] if picture_url else ""
            new_hero = models.HistoricalFigure(name=name, description=description, picture_url=picture_url)
            db.add(new_hero)
            db.commit()
            db.close()
            yield "Added new hero to DB."
            yield f"FINAL_ANSWER::" + json.dumps({"answer": description, "picture_url": picture_url, "source": "groq+tool", "hero": name})
            return
        except Exception as e:
            db.close()
            yield f"Error: {e}"
            yield f"FINAL_ANSWER::" + json.dumps({"error": f"Failed to generate description for {name}: {e}"})
            return
    return EventSourceResponse(event_generator())

@app.get("/chat", response_class=HTMLResponse)
def chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})