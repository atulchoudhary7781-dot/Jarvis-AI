# jarvis_image_gen.py - Image Generation and Editing
# Integrates multiple image generation APIs (DALL-E, local models)

import os
import base64
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

from typing import Optional, Dict, Any, List
from pathlib import Path
import io
import logging

try:
    from PIL import Image, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageFilter = None
    ImageEnhance = None
    PIL_AVAILABLE = False


class ImageGenerationHandler:
    """
    Handles AI image generation using multiple backends:
    - OpenAI DALL-E API
    - Hugging Face Stable Diffusion (remote)
    - Local image editing with PIL
    """
    
    def __init__(self):
        self.pil_available = PIL_AVAILABLE
        
        # Image quality presets
        self.quality_presets = {
            "draft": {"size": "256x256", "quality": "standard"},
            "standard": {"size": "512x512", "quality": "standard"},
            "hd": {"size": "1024x1024", "quality": "hd"},
            "ultra": {"size": "1792x1024", "quality": "hd"},
        }
    
    def generate_image_stable_diffusion(
        self,
        prompt: str,
        model_id: str = "stabilityai/stable-diffusion-2",
        negative_prompt: str = None,
        num_inference_steps: int = 50
    ) -> Dict[str, Any]:
        """
        Generate image using Hugging Face Stable Diffusion API.
        Requires HF_API_KEY environment variable.
        
        Args:
            prompt: Image description
            model_id: Hugging Face model ID
            negative_prompt: What to avoid in image
            num_inference_steps: Quality/speed tradeoff (20-100)
            
        Returns:
            Dict with generated image path
        """
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Requests library not installed. Run: pip install requests"
            }

        hf_api_key = os.environ.get("HF_API_KEY")
        if not hf_api_key:
            return {
                "success": False,
                "error": "Hugging Face API key not set. Set HF_API_KEY environment variable."
            }
        
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {"Authorization": f"Bearer {hf_api_key}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": negative_prompt or "",
                    "num_inference_steps": num_inference_steps
                }
            }
            
            response = requests.post(API_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                # Save image
                image_dir = Path.home() / "JARVIS_Generated_Images"
                image_dir.mkdir(exist_ok=True)
                
                timestamp = __import__('time').strftime("%Y%m%d_%H%M%S")
                image_path = image_dir / f"generated_{timestamp}.png"
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "model": "stable-diffusion",
                    "image_path": str(image_path),
                    "prompt": prompt
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "model": "stable-diffusion"
                }
        except Exception as e:
            return {"success": False, "error": str(e), "model": "stable-diffusion"}
    
    def generate_image(
        self,
        prompt: str,
        backend: str = "dall-e",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image with automatic backend selection.
        
        Args:
            prompt: Image description
            backend: "dall-e", "stable-diffusion", or "auto"
            **kwargs: Additional parameters for the backend
            
        Returns:
            Dict with generation result
        """
        if backend == "auto":
            return self.generate_image_stable_diffusion(prompt, **kwargs)
        
        elif backend in ["stable-diffusion", "sd"]:
            return self.generate_image_stable_diffusion(prompt, **kwargs)
        
        else:
            return {"success": False, "error": f"Unknown backend: {backend}"}
    
    def edit_image(
        self,
        image_path: str,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply filters and edits to local images using PIL.
        
        Args:
            image_path: Path to image file
            operation: "blur", "sharpen", "brighten", "contrast", "resize", "rotate"
            **kwargs: Operation parameters
            
        Returns:
            Dict with result
        """
        if not self.pil_available:
            return {"success": False, "error": "PIL not available. Install with: pip install Pillow"}
        
        if not Path(image_path).exists():
            return {"success": False, "error": f"Image not found: {image_path}"}
        
        try:
            img = Image.open(image_path)
            
            if operation == "blur":
                radius = kwargs.get("radius", 5)
                img = img.filter(ImageFilter.GaussianBlur(radius))
            
            elif operation == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)
            
            elif operation == "brighten":
                factor = kwargs.get("factor", 1.5)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(factor)
            
            elif operation == "contrast":
                factor = kwargs.get("factor", 1.5)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(factor)
            
            elif operation == "resize":
                width = kwargs.get("width", 512)
                height = kwargs.get("height", 512)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            elif operation == "rotate":
                angle = kwargs.get("angle", 90)
                img = img.rotate(angle, expand=True)
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
            
            # Save edited image
            output_dir = Path.home() / "JARVIS_Edited_Images"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = __import__('time').strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"edited_{timestamp}.png"
            
            img.save(str(output_path))
            
            return {
                "success": True,
                "operation": operation,
                "input_path": image_path,
                "output_path": str(output_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_image(self, url: str, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Download image from URL.
        
        Args:
            url: Image URL
            save_path: Where to save (default: ~/JARVIS_Downloaded_Images/)
            
        Returns:
            Dict with file path
        """
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Requests library not installed. Run: pip install requests"
            }

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if save_path is None:
                save_dir = Path.home() / "JARVIS_Downloaded_Images"
                save_dir.mkdir(exist_ok=True)
                timestamp = __import__('time').strftime("%Y%m%d_%H%M%S")
                save_path = save_dir / f"image_{timestamp}.png"
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return {
                "success": True,
                "url": url,
                "saved_to": str(save_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, bool]:
        """Get availability status of all image generation backends."""
        return {
            "pil_local_editing": self.pil_available,
            "huggingface_sd": bool(os.environ.get("HF_API_KEY")) and REQUESTS_AVAILABLE,
            "requests_available": REQUESTS_AVAILABLE
        }


# Example usage
if __name__ == "__main__":
    handler = ImageGenerationHandler()
    status = handler.get_status()
    logging.info("Image Generation Handler initialized")
    logging.info(f"Available backends: {status}")
