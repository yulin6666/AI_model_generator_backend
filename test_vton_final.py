#!/usr/bin/env python3
"""
使用确认可用的VTON模型进行测试
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

    # 根据文件扩展名判断MIME类型
    suffix = path.suffix.lower()
    if suffix == '.png':
        mime = 'image/png'
    else:
        mime = 'image/jpeg'

    return f"data:{mime};base64,{data}"


def download_result(url: str, filename: str):
    """下载结果图片"""
    try:
        with httpx.Client(timeout=120) as client:
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
    print("\n" + "=" * 70)
    print("🎨 VTON 虚拟试穿模型对比测试")
    print("=" * 70)

    person_img = "test_data/test_data/model/model1.jpg"
    garment_img = "test_data/test_data/clother/clother2.jpg"

    print(f"\n📷 模特图: {person_img}")
    print(f"👕 衣服图: {garment_img}\n")

    # 确认可用的两个模型
    models = [
        {
            "name": "IDM-VTON",
            "model": "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
            "inputs_fn": lambda p, g: {
                "human_img": p,
                "garm_img": g,
                "garment_des": "shirt",
            },
            "desc": "IDM-VTON - ECCV2024高质量虚拟试穿"
        },
        {
            "name": "OOTDiffusion",
            "model": "viktorfa/oot_diffusion:9f8fa4956970dde99689af7488157a30aa152e23953526a605df1d77598343d7",
            "inputs_fn": lambda p, g: {
                "model_image": p,
                "garment_image": g,
                "category": 0,  # 0 = upper body
                "n_steps": 20,
            },
            "desc": "OOTDiffusion - 速度优化版本"
        },
    ]

    print(f"准备图片...")
    person_uri = image_to_data_uri(person_img)
    garment_uri = image_to_data_uri(garment_img)
    print(f"✓ 图片已转换为 data URI (person: {len(person_uri)} bytes, garment: {len(garment_uri)} bytes)\n")

    results = []

    for i, model_cfg in enumerate(models):
        print(f"{'='*70}")
        print(f"🔄 [{i+1}/{len(models)}] {model_cfg['name']}")
        print(f"   {model_cfg['desc']}")
        print(f"{'='*70}")

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
                results_list = list(output)
                result_url = str(results_list[0]) if results_list else None
            else:
                result_url = str(output)

            if result_url:
                print(f"\n✅ 成功! 耗时: {elapsed:.1f}秒")
                print(f"   输出URL: {result_url[:80]}...")

                # 下载
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{model_cfg['name'].replace('-', '_').lower()}.png"
                filepath = download_result(result_url, filename)

                results.append({
                    "name": model_cfg['name'],
                    "success": True,
                    "time": elapsed,
                    "file": filepath
                })
            else:
                raise Exception("无法从输出中提取结果URL")

        except Exception as e:
            elapsed = time.time() - start
            print(f"\n❌ 失败 ({elapsed:.1f}秒)")
            error_msg = str(e)
            print(f"   错误: {error_msg[:150]}")
            results.append({
                "name": model_cfg['name'],
                "success": False,
                "time": elapsed,
                "error": error_msg
            })

        # 如果不是最后一个模型，等待一段时间避免速率限制
        if i < len(models) - 1:
            wait_time = 10
            print(f"\n⏳ 等待 {wait_time} 秒避免速率限制...")
            time.sleep(wait_time)
        print()

    # 汇总结果
    print("=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)

    successful = [r for r in results if r["success"]]

    for r in results:
        if r["success"]:
            print(f"\n✅ {r['name']}")
            print(f"   耗时: {r['time']:.1f}秒")
            print(f"   文件: {r.get('file', 'N/A')}")
        else:
            print(f"\n❌ {r['name']}")
            error = r.get('error', 'Unknown')[:120]
            print(f"   错误: {error}...")

    if successful:
        fastest = min(successful, key=lambda x: x["time"])
        print(f"\n🏆 最快模型: {fastest['name']} ({fastest['time']:.1f}秒)")
    else:
        print(f"\n⚠️  所有模型测试都失败了")
        print(f"   可能原因:")
        print(f"   1. API配额不足（需要至少$5余额）")
        print(f"   2. 速率限制")
        print(f"   3. 图片格式或大小问题")

    print(f"\n📁 查看结果图片: open test_outputs/")
    print("=" * 70)


if __name__ == "__main__":
    main()
