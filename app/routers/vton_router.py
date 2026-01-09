"""
IDM-VTON API Router
High-quality virtual try-on endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import base64

from app.services.vton_service import VTONService, VTONResult


router = APIRouter(prefix="/api/vton", tags=["vton"])

# Service instance
vton_service = VTONService()


class TryOnRequest(BaseModel):
    """Request body for try-on endpoint"""
    person_image: str  # URL or base64 data URI
    garment_image: str  # URL or base64 data URI
    garment_description: str = "shirt"
    category: str = "upper_body"
    denoise_steps: int = 30

    class Config:
        json_schema_extra = {
            "example": {
                "person_image": "https://example.com/model.jpg",
                "garment_image": "https://example.com/shirt.jpg",
                "garment_description": "blue cotton shirt",
                "category": "upper_body",
                "denoise_steps": 30
            }
        }


class TryOnResponse(BaseModel):
    """Response from try-on endpoint"""
    success: bool
    output_url: Optional[str] = None
    elapsed_time: float
    input_size: Optional[dict] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "output_url": "https://replicate.delivery/pbxt/...",
                "elapsed_time": 25.3,
                "input_size": {"person_kb": 120, "garment_kb": 85},
                "error": None
            }
        }


@router.post("/try-on", response_model=TryOnResponse)
async def try_on(request: TryOnRequest):
    """
    Virtual try-on using IDM-VTON model (ECCV2024)

    Supports multiple image input formats:
    - **person_image**: URL, base64 data URI, or local path
    - **garment_image**: URL, base64 data URI, or local path
    - **garment_description**: Text description of the garment (e.g., "blue cotton shirt")
    - **category**: "upper_body", "lower_body", or "dresses"
    - **denoise_steps**: Quality control (10-50, default 30)

    Returns the try-on result with output image URL.
    """
    result = await vton_service.try_on(
        person_image=request.person_image,
        garment_image=request.garment_image,
        garment_description=request.garment_description,
        category=request.category,
        denoise_steps=request.denoise_steps,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return TryOnResponse(
        success=result.success,
        output_url=result.output_url,
        elapsed_time=result.elapsed_time,
        input_size=result.input_size,
        error=result.error,
    )


@router.post("/try-on/upload", response_model=TryOnResponse)
async def try_on_upload(
    person_image: UploadFile = File(..., description="Model/person photo"),
    garment_image: UploadFile = File(..., description="Garment/clothing photo"),
    garment_description: str = Form("shirt", description="Description of garment"),
    category: str = Form("upper_body", description="Clothing category"),
    denoise_steps: int = Form(30, description="Denoising steps (10-50)"),
):
    """
    Virtual try-on with file uploads

    Upload images directly instead of providing URLs.
    Supports JPG, PNG image formats.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received upload request - person: {person_image.filename}, garment: {garment_image.filename}")

        # Convert uploads to data URIs
        person_data = await person_image.read()
        logger.info(f"Person image size: {len(person_data)} bytes")
        person_uri = f"data:{person_image.content_type};base64,{base64.b64encode(person_data).decode()}"

        garment_data = await garment_image.read()
        logger.info(f"Garment image size: {len(garment_data)} bytes")
        garment_uri = f"data:{garment_image.content_type};base64,{base64.b64encode(garment_data).decode()}"

        logger.info("Calling VTON service...")
        result = await vton_service.try_on(
            person_image=person_uri,
            garment_image=garment_uri,
            garment_description=garment_description,
            category=category,
            denoise_steps=denoise_steps,
        )

        if not result.success:
            logger.error(f"VTON service failed: {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        logger.info(f"VTON service succeeded in {result.elapsed_time:.1f}s")
        return TryOnResponse(
            success=result.success,
            output_url=result.output_url,
            elapsed_time=result.elapsed_time,
            input_size=result.input_size,
            error=result.error,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in try_on_upload")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/info")
async def get_info():
    """Get information about the IDM-VTON service"""
    return {
        "model": "IDM-VTON",
        "description": "High-quality virtual try-on model (ECCV2024)",
        "paper": "https://idm-vton.github.io/",
        "categories": ["upper_body", "lower_body", "dresses"],
        "parameters": {
            "denoise_steps": {
                "type": "integer",
                "min": 10,
                "max": 50,
                "default": 30,
                "description": "Higher values = better quality but slower"
            },
            "garment_description": {
                "type": "string",
                "description": "Text description of the garment",
                "examples": ["shirt", "dress", "blue cotton t-shirt"]
            }
        },
        "optimal_image_size": "768x768 or smaller",
        "supported_formats": ["JPG", "PNG"],
    }
