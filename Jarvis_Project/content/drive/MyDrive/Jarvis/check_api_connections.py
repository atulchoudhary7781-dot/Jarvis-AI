import os
import sys
import logging

# Configure logging for better output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Try to load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env file (if present).")
except ImportError:
    logging.warning("python-dotenv not installed. API keys must be set as system environment variables.")

def check_openrouter_api():
    logging.info("--- Checking Open Router API Connection ---")
    try:
        from openai import OpenAI
        OPENROUTER_AVAILABLE = True
    except ImportError:
        logging.error("OpenAI library not found. Please install with: pip install openai")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logging.warning("OPENROUTER_API_KEY environment variable not set in .env or system.")
        logging.info("Open Router API check skipped.")
        return

    if not api_key.startswith("sk-or-v1-"):
        logging.error(f"Invalid Open Router API key format. Key starts with '{api_key[:9]}...', but should start with 'sk-or-v1-'.")
        return

    try:
        logging.info(f"Attempting connection with key: {api_key[:10]}...{api_key[-4:]}")
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        # Attempt a small chat completion to verify connection
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="openai/gpt-4o-mini", # Using a common model for quick check
            max_tokens=10,
            temperature=0.0,
            timeout=10.0
        )
        logging.info(f"Open Router API connection successful. Response: '{chat_completion.choices[0].message.content.strip()}'")
    except Exception as e:
        if "401" in str(e) or "invalid_api_key" in str(e).lower():
            logging.error("Open Router API connection failed: 401 Unauthorized - The API Key is invalid.")
        logging.error(f"Open Router API connection failed: {e}")

def check_google_genai_api():
    logging.info("--- Checking Google Generative AI API Connection ---")
    try:
        from google import generativeai as genai
        GENAI_AVAILABLE = True
    except ImportError:
        logging.error("Google Generative AI library not found. Please install with: pip install google-generativeai")
        return

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logging.warning("GOOGLE_API_KEY environment variable not set.")
        logging.info("Google Generative AI API check skipped.")
        return

    try:
        genai.configure(api_key=api_key)
        # Attempt to list models to verify connection
        models = list(genai.list_models())
        if models:
            logging.info(f"Google Generative AI API connection successful. Found {len(models)} models, e.g., '{models[0].name}'")
        else:
            logging.warning("Google Generative AI API connected, but no models were listed.")
    except Exception as e:
        logging.error(f"Google Generative AI API connection failed: {e}")

def check_huggingface_hub_api():
    logging.info("--- Checking Hugging Face Hub API Connection ---")
    try:
        import huggingface_hub
        HF_HUB_AVAILABLE = True
    except ImportError:
        logging.error("huggingface_hub library not found. Please install with: pip install huggingface_hub")
        return

    token = os.environ.get("HF_TOKEN")
    if not token:
        logging.warning("HF_TOKEN environment variable not set.")
        logging.info("Hugging Face Hub API check skipped.")
        return

    try:
        # Attempt to get user info to verify token and connection
        user_info = huggingface_hub.whoami(token=token)
        logging.info(f"Hugging Face Hub API connection successful. Logged in as: '{user_info['name']}'")
    except Exception as e:
        logging.error(f"Hugging Face Hub API connection failed: {e}")

def main():
    logging.info("Starting API Connection Checks...")
    print("-" * 50)
    check_openrouter_api()
    print("-" * 50)
    check_google_genai_api()
    print("-" * 50)
    check_huggingface_hub_api()
    print("-" * 50)
    logging.info("All API checks completed.")

if __name__ == "__main__":
    main()