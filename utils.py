from urllib.parse import quote_plus
from dotenv import load_dotenv
import requests
import os
from fastapi import HTTPException
import ollama
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime
from elevenlabs import ElevenLabs
from pathlib import Path
from gtts import gTTS

load_dotenv()


class MCPOverloadedError(Exception):
    """Custom exception for MCP service overloads"""
    pass


# ==========================================================
# ✅ News Fetcher (Serper)
# ==========================================================
def fetch_news_with_serper(topic: str, num_results: int = 10) -> str:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="SERPER_API_KEY not set in .env")

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": topic, "num": num_results}

    try:
        response = requests.post("https://api.serper.dev/search", headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Serper API error: {str(e)}")

    items = data.get("news") or data.get("organic") or []
    headlines = [f"{item.get('title', '')}: {item.get('snippet', '')}" for item in items]
    return "\n".join(headlines[:num_results]).strip()


# ==========================================================
# ✅ Summarization & Broadcast Functions
# ==========================================================
def summarize_with_ollama(headlines) -> str:
    """Summarize content using Ollama"""
    prompt = f"""You are my personal news editor. Summarize these headlines into a TV news script for me, focus on important headlines and remember that this text will be converted to audio:
    So no extra stuff other than text which the podcaster/newscaster should read, no special symbols or extra information in between and of course no preamble please.
    {headlines}
    News Script:"""

    try:
        client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        response = client.generate(
            model="llama3.2",
            prompt=prompt,
            options={"temperature": 0.4, "max_tokens": 800},
            stream=False
        )
        return response['response']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


def generate_broadcast_news(api_key, news_data, reddit_data, topics):
    """Generate natural, TTS-ready broadcast news from summarized data"""
    system_prompt = """
    You are broadcast_news_writer, a professional virtual news reporter. Generate natural, TTS-ready news reports using available sources:

    For each topic, STRUCTURE BASED ON AVAILABLE DATA:
    1. If news exists: "According to official reports..." + summary
    2. If both exist: Present news first, then Reddit reactions (not used now)
    3. If neither exists: Skip the topic

    Formatting rules:
    - ALWAYS start directly with the content, NO INTRODUCTIONS
    - Keep audio length 60-120 seconds per topic
    - Use natural speech transitions like "Meanwhile..."
    - Maintain neutral tone
    - End with "To wrap up this segment..." summary
    """

    try:
        topic_blocks = []
        for topic in topics:
            news_content = news_data["news_analysis"].get(topic) if news_data else ''
            if news_content:
                topic_blocks.append(
                    f"TOPIC: {topic}\n\nOFFICIAL NEWS CONTENT:\n{news_content}"
                )

        user_prompt = (
            "Create broadcast segments for these topics using available sources:\n\n" +
            "\n\n--- NEW TOPIC ---\n\n".join(topic_blocks)
        )

        llm = ChatGroq(
            model="llama-3.1-8b-instant",   # or "mixtral-8x7b"
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.4,
            max_tokens=1000
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        return response.content

    except Exception as e:
        raise e



def summarize_with_anthropic_news_script(api_key: str, headlines: str) -> str:
    """Summarize multiple news headlines into a TTS-friendly broadcast news script using Groq LLM."""
    system_prompt = """
You are my personal news editor and scriptwriter for a news podcast. 
Turn raw headlines into a clean, professional, and TTS-friendly news script.
Write like a news anchor speaking naturally, no markdown, no emojis, no framing.
"""
    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",   # or "mixtral-8x7b"
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.4,
            max_tokens=1000
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=headlines)
        ])
        return response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq error: {str(e)}")


# ==========================================================
# ✅ Text-to-Speech
# ==========================================================
def text_to_audio_elevenlabs_sdk(
    text: str,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
    output_dir: str = "audio",
    api_key: str = None
) -> str:
    """Converts text to speech using ElevenLabs SDK and saves it to audio/ directory."""
    try:
        api_key = api_key or os.getenv("ELEVEN_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key is required.")

        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format
        )

        os.makedirs(output_dir, exist_ok=True)
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        return filepath
    except Exception as e:
        raise e


AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

def tts_to_audio(text: str, language: str = 'en') -> str:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = AUDIO_DIR / f"tts_{timestamp}.mp3"
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filename))
        return str(filename)
    except Exception as e:
        print(f"gTTS Error: {str(e)}")
        return None
