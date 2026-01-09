#!/usr/bin/env python3
"""
使用公开可用的VTON模型进行测试
"""
import os
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

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{data}"


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
                print(f"   💾 已保存: {filepath}")
                return filepath
    except Exception as e:
        print(f"   下载失败: {e}")
    return None


def main():
    print("\n" + "=" * 60)
    print("🎨 VTON 虚拟试穿测试")
    print("=" * 60)

    person_img = "test_data/test_data/model/model1.jpg"
    garment_img = "test_data/test_data/clother/clother2.jpg"

    print(f"\n📷 模特图: {person_img}")
    print(f"👕 衣服图: {garment_img}\n")

    # 测试几个已知的公开模型
    models_to_test = [
        {
            "name": "Katara AI VTON",
            "model": "kataraai/virtual-try-on",
            "inputs_fn": lambda p, g: {
                "cloth": g,
                "human_img": p,
            },
        },
    ]

    print(f"准备图片...")
    person_uri = image_to_data_uri(person_img)
    garment_uri = image_to_data_uri(garment_img)
    print(f"✓ 图片已转换为 data URI\n")

    for model_cfg in models_to_test:
        print(f"{'='*50}")
        print(f"🔄 测试: {model_cfg['name']}")
        print(f"{'='*50}")

        start = time.time()
        try:
            print(f"正在调用 Replicate API...")
            output = replicate.run(
                model_cfg["model"],
                input=model_cfg["inputs_fn"](person_uri, garment_uri)
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
            print(f"   URL: {result_url[:100]}...")

            # 下载
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            download_result(result_url, f"{timestamp}_{model_cfg['name'].replace(' ', '_')}.png")

        except Exception as e:
            elapsed = time.time() - start
            print(f"\n❌ 失败 ({elapsed:.1f}s)")
            print(f"   错误: {str(e)[:200]}")

        print()

    print("=" * 60)
    print("测试完成! 请查看 test_outputs/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
