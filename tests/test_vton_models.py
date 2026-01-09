#!/usr/bin/env python3
"""
VTON Model Comparison Test Script
测试三个虚拟试穿模型的效果和性能对比

Usage:
    python tests/test_vton_models.py --person <person_image> --garment <garment_image>

Example:
    python tests/test_vton_models.py \
        --person "https://example.com/model.jpg" \
        --garment "https://example.com/shirt.jpg"
"""
import asyncio
import argparse
import sys
import os
import httpx
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.vton_service import VTONService, VTONModel


# Sample test images (public domain / CC0)
SAMPLE_PERSON = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=512"
SAMPLE_GARMENT = "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=512"


async def download_image(url: str, save_path: Path) -> None:
    """Download image from URL to local file"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        save_path.write_bytes(response.content)
        print(f"Downloaded: {save_path}")


async def run_comparison(
    person_image: str,
    garment_image: str,
    category: str = "upper_body",
    models: list[VTONModel] | None = None,
    save_outputs: bool = True,
) -> None:
    """Run comparison test across all or specified models"""

    print("\n" + "=" * 60)
    print("VTON Model Comparison Test")
    print("=" * 60)
    print(f"\nPerson Image: {person_image[:80]}...")
    print(f"Garment Image: {garment_image[:80]}...")
    print(f"Category: {category}")
    print(f"Models: {[m.value for m in (models or list(VTONModel))]}")
    print("\n" + "-" * 60)

    service = VTONService()

    if models is None:
        models = list(VTONModel)

    # Run each model
    results = []
    for model in models:
        print(f"\n[{model.value}] Running...")
        result = await service.try_on(
            model=model,
            person_image=person_image,
            garment_image=garment_image,
            category=category,
        )
        results.append(result)

        if result.success:
            print(f"[{model.value}] Success - {result.elapsed_time:.2f}s")
            print(f"  Output: {result.output_url[:80]}...")
        else:
            print(f"[{model.value}] Failed - {result.error}")

    # Save outputs
    if save_outputs:
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for result in results:
            if result.success and result.output_url:
                filename = f"{timestamp}_{result.model.value}.png"
                filepath = output_dir / filename
                try:
                    await download_image(result.output_url, filepath)
                except Exception as e:
                    print(f"Failed to save {result.model.value}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\n{'Model':<15} {'Status':<10} {'Time (s)':<12} {'Notes'}")
    print("-" * 60)

    for result in sorted(results, key=lambda r: (not r.success, r.elapsed_time)):
        status = "OK" if result.success else "FAIL"
        time_str = f"{result.elapsed_time:.2f}" if result.success else "-"
        notes = result.error[:30] if result.error else ""
        print(f"{result.model.value:<15} {status:<10} {time_str:<12} {notes}")

    # Recommendations
    print("\n" + "-" * 60)
    print("Recommendations:")

    successful = [r for r in results if r.success]
    if successful:
        fastest = min(successful, key=lambda r: r.elapsed_time)
        print(f"  Fastest: {fastest.model.value} ({fastest.elapsed_time:.2f}s)")
        print(f"  Best Quality (expected): IDM-VTON (ECCV2024)")
        print(f"  Best Balance: CatVTON (2024 SOTA)")
    else:
        print("  No successful results. Check your REPLICATE_API_TOKEN.")

    print()


async def run_single_model_test(
    model_name: str,
    person_image: str,
    garment_image: str,
) -> None:
    """Test a single model"""
    model = VTONModel(model_name)
    await run_comparison(
        person_image=person_image,
        garment_image=garment_image,
        models=[model],
    )


def main():
    parser = argparse.ArgumentParser(description="Test VTON models")
    parser.add_argument(
        "--person",
        type=str,
        default=SAMPLE_PERSON,
        help="Person/model image URL or local path",
    )
    parser.add_argument(
        "--garment",
        type=str,
        default=SAMPLE_GARMENT,
        help="Garment image URL or local path",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="upper_body",
        choices=["upper_body", "lower_body", "dresses"],
        help="Clothing category",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        choices=["idm_vton", "ootd", "catvton"],
        help="Test only this model (default: all)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output images",
    )

    args = parser.parse_args()

    # Check API token
    if not os.getenv("REPLICATE_API_TOKEN"):
        print("\nError: REPLICATE_API_TOKEN not set!")
        print("\n1. Get your token: https://replicate.com/account/api-tokens")
        print("2. Create .env file with: REPLICATE_API_TOKEN=your_token")
        print("3. Or export: export REPLICATE_API_TOKEN=your_token")
        sys.exit(1)

    # Run test
    models = [VTONModel(args.model)] if args.model else None

    asyncio.run(
        run_comparison(
            person_image=args.person,
            garment_image=args.garment,
            category=args.category,
            models=models,
            save_outputs=not args.no_save,
        )
    )


if __name__ == "__main__":
    main()
