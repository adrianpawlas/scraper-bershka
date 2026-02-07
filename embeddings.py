import os
from typing import Optional
from time import sleep
from io import BytesIO
import requests
import torch
from PIL import Image
from transformers import SiglipProcessor, SiglipModel

_processor: Optional[SiglipProcessor] = None
_model: Optional[SiglipModel] = None
_model_error: bool = False


def _get_model():
    global _processor, _model, _model_error
    if _model is None and not _model_error:
        model_name = os.getenv("EMBEDDINGS_MODEL", "google/siglip-base-patch16-384")
        try:
            print(f"[MODEL] Loading {model_name}...")
            _processor = SiglipProcessor.from_pretrained(model_name)
            _model = SiglipModel.from_pretrained(model_name)
            print(f"[MODEL] Loaded {model_name} successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load model {model_name}: {e}")
            _model_error = True
            return None, None
    return _processor, _model


def get_image_embedding(image_url: str, max_retries: int = 3) -> Optional[list]:
    """Get embedding using Google SigLIP model (768-dim, vision-language model)."""

    if not image_url or not str(image_url).strip():
        return None

    processor, model = _get_model()
    if model is None or processor is None:
        return None

    raw_url = str(image_url).strip()

    # Skip data URLs (base64 embedded images) - these are placeholders
    if raw_url.startswith("data:"):
        print(f"[SKIP] Data URL placeholder - no embedding needed")
        return None

    # Skip video files
    video_indicators = ['.m3u8', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', 'video.mp4', '/video']
    if any(indicator in raw_url.lower() for indicator in video_indicators):
        # Silently skip video files
        return None

    # Skip other non-image file types
    non_image_extensions = ['.html', '.htm', '.json', '.xml', '.txt', '.css', '.js']
    if any(raw_url.lower().endswith(ext) for ext in non_image_extensions):
        return None

    # Skip obviously incomplete or invalid URLs
    if "bershka" in raw_url.lower():
        # Bershka image URLs should have the static domain and proper path structure
        if not raw_url.startswith('https://static.bershka.net/'):
            return None
        # Valid Bershka URLs should be at least 80 chars and contain 'assets/public'
        if 'assets/public' not in raw_url and len(raw_url) < 80:
            return None

    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url

    # Clean up malformed URLs
    if "//" in raw_url and not raw_url.startswith("http"):
        parts = raw_url.split("//", 1)
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1]
            rest = "/".join(filter(None, rest.split("/")))
            raw_url = protocol + "//" + rest

    for attempt in range(max_retries):
        if attempt > 0:
            sleep_time = 2 ** (attempt - 1)
            print(f"[RETRY] Embedding attempt {attempt + 1}/{max_retries} after {sleep_time}s...")
            sleep(sleep_time)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            # Special handling for Bershka images
            if "bershka" in raw_url.lower():
                headers["Referer"] = "https://www.bershka.com/"

            resp = requests.get(raw_url, headers=headers, timeout=15)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content)).convert("RGB")

            # Process with SigLIP (requires both image and text inputs)
            inputs = processor(images=img, text=[""], return_tensors="pt")

            with torch.no_grad():
                outputs = model(**inputs)

                # Use image embeddings (768-dim for SigLIP base)
                embedding = outputs.image_embeds.squeeze().tolist()

            # Verify dimensions (should be exactly 768)
            if len(embedding) != 768:
                print(f"[ERROR] Embedding dimension mismatch: got {len(embedding)}, expected 768")
                return None

            return embedding

        except Exception as e:
            print(f"[ERROR] Embedding failed: {str(e)[:80]}")
            print(f"        URL: {raw_url}")

    print(f"[FAILED] All embedding attempts failed for: {image_url[:60]}")
    return None


def get_text_embedding(text: str, max_length: int = 512) -> Optional[list]:
    """Get text embedding using the same SigLIP model as image embeddings (768-dim).
    Use for info_embedding: title, description, price, metadata, etc.
    """
    if not text or not str(text).strip():
        return None

    processor, model = _get_model()
    if model is None or processor is None:
        return None

    text_str = str(text).strip()
    if not text_str:
        return None

    try:
        # Tokenize with the same processor (SigLIP uses text encoder)
        inputs = processor(
            text=[text_str],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        input_ids = inputs.get("input_ids")
        attention_mask = inputs.get("attention_mask")
        if input_ids is None:
            return None

        with torch.no_grad():
            # SigLIP text encoder - same model as image, same embedding space
            if hasattr(model, "get_text_features"):
                text_embeds = model.get_text_features(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                )
            else:
                # Fallback: some checkpoints use forward with text inputs
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                text_embeds = getattr(outputs, "text_embeds", None) or getattr(
                    outputs, "last_hidden_state", None
                )
                if text_embeds is not None and text_embeds.dim() > 1:
                    text_embeds = text_embeds[:, 0, :]  # CLS token or pool
                else:
                    return None

        embedding = text_embeds.squeeze().tolist()
        if isinstance(embedding[0], list):
            embedding = embedding[0]
        if len(embedding) != 768:
            return None
        return embedding
    except Exception as e:
        print(f"[ERROR] Text embedding failed: {str(e)[:80]}")
        return None
