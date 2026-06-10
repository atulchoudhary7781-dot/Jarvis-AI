import os
import threading
from typing import Callable, Optional

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    AutoTokenizer = None
    AutoModelForCausalLM = None
    TRANSFORMERS_AVAILABLE = False

def train_and_save_model(
    model_name: str,
    output_dir: str = "./jarvis_brain",
    progress_callback: Optional[Callable[[str], None]] = None
):
    """
    Loads a model, simulates training, and saves it.
    This function is designed to be run in a background thread.
    """
    if not TRANSFORMERS_AVAILABLE:
        if progress_callback:
            progress_callback("Error: The 'transformers' library is not installed. Please run: pip install transformers")
        return

    if progress_callback:
        progress_callback(f"Loading model '{model_name}' for training...")

    try:
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        # Add padding token if missing (common issue with GPT-2)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            if hasattr(model, 'config'):
                 model.config.pad_token_id = model.config.eos_token_id

        # ... (Actual training code would go here) ...

        # Save the finished 'brain' to your project folder
        os.makedirs(output_dir, exist_ok=True)
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        if progress_callback:
            progress_callback(f"Model and tokenizer saved successfully to '{output_dir}'")

    except Exception as e:
        if progress_callback:
            progress_callback(f"Error during training/saving: {e}")