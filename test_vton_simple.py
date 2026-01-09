#!/usr/bin/env python3
"""
简化的VTON测试脚本 - 使用最新可用的模型
"""
import os
import sys
import time
import base64
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保API token已设置
if not os.getenv("REPLICATE_API_TOKEN"):
    raise ValueError("请在.env文件中设置REPLICATE_API_TOKEN")

import replicate
import httpx


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


# 测试图片
PERSON_IMAGE = "test_data/test_data/model/model1.jpg"
GARMENT_IMAGE = "test_data/test_data/clother/clother2.jpg"

# 使用可用的VTON模型
MODELS = [
    {
        "name": "IDM-VTON (yisol)",
        "model": "yisol/idm-vton:c871bb9b046c1b1c9a6dcc3a8a310993d7ab8716a4e0f3bb9e66c77823b75e58",
        "inputs_fn": lambda p, g: {
            "human_img": p,
            "garm_img": g,
            "garment_des": "cute shirt",
        },
        "desc": "高质量虚拟试穿"
    },
    {
        "name": "OOTDiffusion",
        "model": "viktorfa/oot_diffusion:9f8fa4956970dde99689af7488157a30aa152e23953526a605df1d77598343d7",
        "inputs_fn": lambda p, g: {
            "model_image": p,
            "garment_image": g,
            "category": 0,  # 0=upper body
            "n_steps": 20,
        },
        "desc": "速度较快"
    },
]


def test_model(model_config):
    """测试单个模型"""
    print(f"\n{'='*50}")
    print(f"🔄 [{model_config['name']}] 开始测试...")
    print(f"   {model_config['desc']}")
    print(f"{'='*50}")

    start = time.time()
    try:
        print("   正在准备图片...")
        person_uri = image_to_data_uri(PERSON_IMAGE)
        garment_uri = image_to_data_uri(GARMENT_IMAGE)

        print("   正在调用 Replicate API...")
        output = replicate.run(
            model_config["model"],
            input=model_config["inputs_fn"](person_uri, garment_uri)
        )
        elapsed = time.time() - start

        # 解析输出
        if isinstance(output, str):
            result_url = output
        elif isinstance(output, list) and len(output) > 0:
            result_url = str(output[0])
        elif hasattr(output, '__iter__'):
            result_url = str(list(output)[0])
        else:
            result_url = str(output)

        print(f"\n✅ 成功! 耗时: {elapsed:.1f}s")
        print(f"   输出URL: {result_url[:100]}...")

        # 下载
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        model_key = model_config['name'].lower().replace('-', '_').replace(' ', '_')
        filepath = download_result(result_url, f"{timestamp}_{model_key}.png")
        if filepath:
            print(f"   💾 已保存: {filepath}")

        return {
            "name": model_config['name'],
            "success": True,
            "time": elapsed,
            "url": result_url,
            "file": filepath
        }

    except Exception as e:
        elapsed = time.time() - start
        error_msg = str(e)
        print(f"\n❌ 失败 ({elapsed:.1f}s)")
        print(f"   错误: {error_msg[:200]}")
        return {
            "name": model_config['name'],
            "success": False,
            "time": elapsed,
            "error": error_msg
        }


def main():
    print("\n" + "=" * 60)
    print("🎨 VTON 虚拟试穿模型测试")
    print("=" * 60)
    print(f"\n📷 模特图: {PERSON_IMAGE}")
    print(f"👕 衣服图: {GARMENT_IMAGE}")
    print(f"\n📋 将测试 {len(MODELS)} 个模型")

    results = []
    for i, model_config in enumerate(MODELS):
        if i > 0:
            wait_time = 15  # 增加等待时间避免速率限制
            print(f"\n⏳ 等待 {wait_time} 秒避免 Rate Limit...")
            time.sleep(wait_time)

        result = test_model(model_config)
        results.append(result)

    # 汇总
    print("\n\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    successful = [r for r in results if r["success"]]

    for r in results:
        if r["success"]:
            print(f"\n✅ {r['name']}")
            print(f"   耗时: {r['time']:.1f}s")
            print(f"   文件: {r.get('file', 'N/A')}")
        else:
            print(f"\n❌ {r['name']}")
            error = r.get('error', 'Unknown')
            # 只显示前80个字符的错误信息
            print(f"   错误: {error[:80]}...")

    if successful:
        fastest = min(successful, key=lambda x: x["time"])
        print(f"\n🏆 最快: {fastest['name']} ({fastest['time']:.1f}s)")

    print(f"\n📁 查看结果: open test_outputs/")
    print()


if __name__ == "__main__":
    main()
