# 🦸‍♂️ Historical Figures Chat & Explorer

A modern FastAPI + LangChain + Groq web app to chat about historical figures, with real-time LLM answers, images, and a live trace console! 🚀

---

## ✨ Features

- 💬 **Chat UI**: Ask about any hero, get detailed AI answers & images
- 🗃️ **Auto-enrich DB**: Missing/short descriptions are upgraded by Groq LLM
- 🟩 **Live Trace Console**: Neon-green on black, top-right, real-time backend steps
- 🐳 **Dockerized**: Easy to run anywhere
- 🔒 **.env Support**: Secure API key management

---

## 🏗️ Quickstart

1. **Clone & set up .env**
   ```
   git clone <your-repo-url>
   cd <project>
   echo "OPENAI_API_KEY=your-groq-key" > .env
   ```
2. **Run with Docker**
   ```
   docker-compose up --build
   ```
   Visit [http://localhost:8000/chat](http://localhost:8000/chat)

---

## 🗂️ Project Structure

```
├── app/
│   ├── main.py         # FastAPI app, endpoints, LLM logic
│   ├── models.py       # SQLAlchemy models
│   ├── database.py     # DB connection
│   ├── templates/      # chat.html, heroes.html
│   └── alembic/        # DB migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

---

## 🔌 API Endpoints

- `GET /chat` – Chat UI
- `GET /heroes` – Hero list UI
- `GET /figures` – All figures (JSON)
- `GET /hero_details?name=...` – LLM answer & image
- `GET /hero_trace?name=...` – Live backend trace (SSE)
- `POST /generate_descriptions` – Fill in missing hero info

---

## 🖥️ Frontend

- **Chat UI**: Modern, responsive, with image support
- **Trace Card**: Top-right, neon green on black, real-time
- **Hero List**: Card-based, all heroes in DB

---

## 🛠️ Troubleshooting

- ❗ **openai_api_key not found**: Check `.env` and Docker Compose `env_file`.
- 🗝️ **LLM not responding**: Check your Groq API key.
- 🗄️ **DB errors**: Delete `app/historical.db` and re-run migrations.
- 🔄 **Frontend issues**: Hard-refresh your browser.

---

## 📦 Dependencies

```
fastapi, uvicorn, sqlalchemy, alembic, jinja2, groq, langchain, langchain-community, openai, sse-starlette, python-dotenv
```

---

## 📝 License

MIT 