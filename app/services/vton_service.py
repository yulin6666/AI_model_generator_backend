"""
IDM-VTON Service - Replicate API Wrapper
High-quality virtual try-on using IDM-VTON (ECCV2024)
"""
import asyncio
import time
import base64
import httpx
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import io

import replicate
from app.config import get_settings


@dataclass
class VTONResult:
    """Result from IDM-VTON model"""
    success: bool
    output_url: Optional[str] = None
    elapsed_time: float = 0.0
    error: Optional[str] = None
    input_size: Optional[dict] = None  # {"person": "123KB", "garment": "456KB"}


class VTONService:
    """IDM-VTON Virtual Try-On Service using Replicate API"""

    def __init__(self):
        self.settings = get_settings()
        self.model_id = self.settings.idm_vton_model
        self.max_image_size = 768  # Optimal size for IDM-VTON

    def _resize_and_optimize_image(self, image_data: bytes) -> tuple[str, int]:
        """
        Resize and optimize image for IDM-VTON
        Returns (data_uri, size_in_kb)
        """
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize maintaining aspect ratio
        img.thumbnail((self.max_image_size, self.max_image_size), Image.Resampling.LANCZOS)

        # Save optimized
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        optimized_data = buffer.getvalue()

        # Encode to base64
        b64_data = base64.b64encode(optimized_data).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{b64_data}"

        return data_uri, len(b64_data) // 1024

    async def _image_to_data_uri(self, image_path: str) -> tuple[str, int]:
        """
        Convert local image to data URI for Replicate
        Returns (data_uri, size_in_kb)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(path, "rb") as f:
            image_data = f.read()

        return self._resize_and_optimize_image(image_data)

    async def _url_to_data_uri(self, url: str) -> tuple[str, int]:
        """
        Download image from URL and convert to data URI
        Returns (data_uri, size_in_kb)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            image_data = response.content

        return self._resize_and_optimize_image(image_data)

    async def _prepare_image(self, image_input: str) -> tuple[str, int]:
        """
        Prepare image from various input formats
        Supports: local path, HTTP(S) URL, or data URI
        Returns (data_uri, size_in_kb)
        """
        # If already a data URI, extract and re-optimize
        if image_input.startswith("data:"):
            # Extract base64 data
            b64_data = image_input.split(",", 1)[1]
            image_data = base64.b64decode(b64_data)
            return self._resize_and_optimize_image(image_data)

        # If URL, download it
        elif image_input.startswith(("http://", "https://")):
            return await self._url_to_data_uri(image_input)

        # Otherwise treat as local path
        else:
            return await self._image_to_data_uri(image_input)

    async def try_on(
        self,
        person_image: str,
        garment_image: str,
        garment_description: str = "shirt",
        category: str = "upper_body",
        denoise_steps: int = 30,
    ) -> VTONResult:
        """
        Run IDM-VTON virtual try-on

        Args:
            person_image: Person/model image (URL, data URI, or local path)
            garment_image: Garment/clothing image (URL, data URI, or local path)
            garment_description: Description of garment (e.g., "shirt", "dress")
            category: Clothing category ("upper_body", "lower_body", "dresses")
            denoise_steps: Number of denoising steps (default: 30)

        Returns:
            VTONResult with output image URL and timing
        """
        start_time = time.time()

        try:
            # Prepare and optimize images
            person_uri, person_kb = await self._prepare_image(person_image)
            garment_uri, garment_kb = await self._prepare_image(garment_image)

            # Build inputs for IDM-VTON
            inputs = {
                "human_img": person_uri,
                "garm_img": garment_uri,
                "garment_des": garment_description,
                "category": category,
                "is_checked": True,
                "is_checked_crop": False,
                "denoise_steps": denoise_steps,
            }

            # Run prediction on Replicate
            output = await asyncio.to_thread(
                replicate.run, self.model_id, input=inputs
            )

            # Parse output (IDM-VTON returns a file URL or bytes)
            output_url = self._parse_output(output)

            elapsed = time.time() - start_time

            return VTONResult(
                success=True,
                output_url=output_url,
                elapsed_time=elapsed,
                input_size={"person_kb": person_kb, "garment_kb": garment_kb},
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return VTONResult(
                success=False,
                elapsed_time=elapsed,
                error=str(e),
            )

    def _parse_output(self, output) -> str:
        """Parse output from IDM-VTON into image URL"""
        if isinstance(output, str):
            return output
        elif isinstance(output, list) and len(output) > 0:
            return output[0] if isinstance(output[0], str) else str(output[0])
        elif hasattr(output, "url"):
            return output.url
        elif hasattr(output, "read"):
            # If it's a file object, we would need to upload it somewhere
            # For now, just return a placeholder
            return "file_output"
        else:
            return str(output)
