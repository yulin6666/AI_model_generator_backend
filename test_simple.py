#!/usr/bin/env python3
"""
VTON 模型测试 - 更新版本
"""
import os
import sys
import time

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.environ.get("REPLICATE_API_TOKEN"):
    print("\n❌ 未设置 REPLICATE_API_TOKEN")
    print("\n请按以下步骤操作：")
    print("1. 访问 https://replicate.com/account/api-tokens 获取 API Token")
    print("2. 创建 .env 文件：cp .env.example .env")
    print("3. 编辑 .env 文件，设置你的 token")
    print("\n或者直接运行：")
    print("  REPLICATE_API_TOKEN=你的token python test_simple.py")
    sys.exit(1)

import replicate
import httpx
import base64
from pathlib import Path


def image_to_data_uri(image_path: str) -> str:
    """将本地图片转换为 data URI"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {image_path}")

    suffix = path.suffix.lower()
    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_types.get(suffix, "image/jpeg")

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{data}"


# 测试图片 - 使用本地文件
PERSON_IMAGE = "test_data/test_data/model/model1.jpg"
GARMENT_IMAGE = "test_data/test_data/clother/clother2.jpg"

# 更新后的模型配置
MODELS = {
    "idm_vton": {
        "name": "IDM-VTON",
        "version": "cuuupid/idm-vton:c871bb9b046c1b1c9a6dcc3a8a310993d7ab8716a4e0f3bb9e66c77823b75e58",
        "inputs": lambda p, g: {
            "human_img": p,
            "garm_img": g,
            "category": "upper_body",
            "is_checked": True,
            "is_checked_crop": False,
            "denoise_steps": 30,
        },
        "desc": "ECCV2024, 效果最好"
    },
    "ootd": {
        "name": "OOTDiffusion",
        "version": "viktorfa/oot_diffusion:9f8fa4956970dde99689af7488157a30aa152e23953526a605df1d77598343d7",
        "inputs": lambda p, g: {
            "model_image": p,
            "garment_image": g,
            "category": 0,
            "n_steps": 20,
        },
        "desc": "速度最快"
    },
    "catvton": {
        "name": "CatVTON",
        "version": "zhengchong/cat-vton:2e4e24460dd86bdb929df68ff1a76830c605ad1b7cbd4e51a6a1b71d4e5ed1f5",
        "inputs": lambda p, g: {
            "image": p,
            "cloth": g,
            "cloth_type": "upper body",
            "num_inference_steps": 50,
        },
        "desc": "2024 SOTA, 质量与速度平衡最佳"
    },
}


def download_result(url: str, filename: str):
    """下载结果图片"""
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                os.makedirs("test_outputs", exist_ok=True)
                filepath = f"test_outputs/{filename}"
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return filepath
    except Exception as e:
        print(f"  下载失败: {e}")
    return None


def run_model(model_key: str):
    """运行单个模型"""
    model_cfg = MODELS[model_key]
    print(f"\n{'='*50}")
    print(f"🔄 [{model_cfg['name']}] 开始测试...")
    print(f"   {model_cfg['desc']}")
    print(f"{'='*50}")

    start = time.time()
    try:
        print("   正在准备图片...")
        # 将本地图片转换为 data URI
        person_uri = image_to_data_uri(PERSON_IMAGE)
        garment_uri = image_to_data_uri(GARMENT_IMAGE)

        print("   正在调用 Replicate API...")
        output = replicate.run(
            model_cfg["version"],
            input=model_cfg["inputs"](person_uri, garment_uri)
        )
        elapsed = time.time() - start

        # 解析输出
        if isinstance(output, str):
            result_url = output
        elif isinstance(output, list) and len(output) > 0:
            result_url = str(output[0])
        elif hasattr(output, '__iter__'):
            # FileOutput iterator
            result_url = str(list(output)[0])
        else:
            result_url = str(output)

        print(f"\n✅ 成功! 耗时: {elapsed:.1f}s")
        print(f"   输出URL: {result_url[:100]}...")

        # 下载
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = download_result(result_url, f"{timestamp}_{model_key}.png")
        if filepath:
            print(f"   💾 已保存: {filepath}")

        return {"model": model_key, "success": True, "time": elapsed, "url": result_url, "file": filepath}

    except Exception as e:
        elapsed = time.time() - start
        error_msg = str(e)
        print(f"\n❌ 失败 ({elapsed:.1f}s)")
        print(f"   错误: {error_msg[:200]}")
        return {"model": model_key, "success": False, "time": elapsed, "error": error_msg}


def main():
    print("\n" + "=" * 60)
    print("🎨 VTON 虚拟试穿模型测试")
    print("=" * 60)
    print(f"\n📷 模特图: {PERSON_IMAGE}")
    print(f"👕 衣服图: {GARMENT_IMAGE}")

    # 选择要测试的模型
    if len(sys.argv) > 1 and sys.argv[1] in MODELS:
        models_to_test = [sys.argv[1]]
    else:
        models_to_test = list(MODELS.keys())

    print(f"\n📋 将测试: {[MODELS[m]['name'] for m in models_to_test]}")

    results = []
    for i, model_key in enumerate(models_to_test):
        if i > 0:
            print("\n⏳ 等待 5 秒避免 Rate Limit...")
            time.sleep(5)
        result = run_model(model_key)
        results.append(result)

    # 汇总
    print("\n\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    successful = [r for r in results if r["success"]]

    for r in results:
        name = MODELS[r["model"]]["name"]
        if r["success"]:
            print(f"\n✅ {name}")
            print(f"   耗时: {r['time']:.1f}s")
            print(f"   文件: {r.get('file', 'N/A')}")
        else:
            print(f"\n❌ {name}")
            print(f"   错误: {r.get('error', 'Unknown')[:80]}...")

    if successful:
        fastest = min(successful, key=lambda x: x["time"])
        print(f"\n🏆 最快: {MODELS[fastest['model']]['name']} ({fastest['time']:.1f}s)")

    print(f"\n📁 查看结果: open test_outputs/")
    print()


if __name__ == "__main__":
    main()
