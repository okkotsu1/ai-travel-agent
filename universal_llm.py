import os
from dotenv import load_dotenv

load_dotenv()

def get_llm(provider="groq", model=None, temperature=0):
    provider = provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or "gemma2-9b-it",
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    elif provider == "openai":
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(
            model_name=model or "gpt-3.5-turbo",
            temperature=temperature
        )

    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=model or "llama3",
            temperature=temperature
        )

    elif provider == "openrouter":
        from langchain_community.chat_models import ChatOpenAI
        return ChatOpenAI(
            openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            model=model or "mistralai/mixtral-8x7b",
            temperature=temperature
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
