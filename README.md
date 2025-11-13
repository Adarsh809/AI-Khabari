# AI Khabri – Intelligent News Summarization System

AI Khabri is an end-to-end news intelligence platform that fetches real-time news from the web and generates concise summaries using Large Language Models.
It combines a FastAPI backend, Streamlit frontend, and Serper API-powered Google News scraper.

---

## Features

- Real-Time News Fetching:
  - Uses Serper API to fetch the latest articles.
  - Custom scraper (news_scraper.py) for structured output.

- LLM Summarization:
  - Uses Groq-based LLMs.
  - Uses eleven labs api for text to speech
  - model.py handles summarization logic.
    

- FastAPI Backend:
  - Handles scraping, summarization, validation, error handling.

- Streamlit UI:
  - Simple interface for topic search and summary generation.

- Utilities:
  - utils.py contains helpers for formatting and environment handling.

---

## Project Structure

```
.
├── app.py                # Streamlit frontend
├── api.py                # FastAPI backend
├── model.py              # LLM wrapper for Groq/OpenAI
├── news_scraper.py       # Serper API scraper
├── utils.py              # Helper utilities
├── requirements.txt      # Dependencies
└── README.md
```

---

## Tech Stack

Backend: FastAPI, Pydantic, Uvicorn
Frontend: Streamlit
LLM Layer: Groq, ElevenLabs
Scraper: Serper API
Environment: python-dotenv

---

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Adarsh809/AI-Khabari
   cd AI-Khabari
   ```

2. Install dependencies:
   ```bash
  uv add -r requirements.txt
   ```

3. Create a `.env` file:
   ```
   SERPER_API_KEY=your_serper_key
   GROQ_API_KEY=your_groq_key
   ELEVEN_API_KEY = youe_elevenlabs_api_key
   ```

4. Start backend:
   ```bash
   uvicorn api:app --reload
   ```

5. Start Streamlit:
   ```bash
   streamlit run app.py
   ```

---

## Workflow

1. User enters topic in Streamlit.
2. Streamlit sends request to FastAPI.
3. news_scraper.py fetches articles.
4. model.py summarizes using Groq LLM.
5. Processed summary returns to UI.

---

## API Endpoints

### GET /health
Returns API status.

### POST /summarize
Request:
```json
{
  "query": "string"
}
```

Response:
```json
{
  "summary": "...",
  "articles": [ ... ]
}
```

---

## Future Enhancements

- Voice-based summaries
- Multi-language (Hindi, English)
- Multi-source scraping
- User accounts and saved summaries

---

## License
Open-source and free to modify.
