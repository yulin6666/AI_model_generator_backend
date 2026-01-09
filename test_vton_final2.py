#!/usr/bin/env python3
"""
VTON测试 - 处理返回的原始字节数据
"""
import os
import time
from pathlib import Path
from PIL import Image
import io
import base64
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保API token已设置
if not os.getenv("REPLICATE_API_TOKEN"):
    raise ValueError("请在.env文件中设置REPLICATE_API_TOKEN")

import replicate


def resize_and_encode_image(image_path: str, max_size=768) -> str:
    """调整图片大小并转换为data URI"""
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    img_data = buffer.getvalue()
    b64_data = base64.b64encode(img_data).decode('utf-8')

    return f"data:image/jpeg;base64,{b64_data}", len(b64_data)


def save_result(output, filename):
    """保存模型输出"""
    os.makedirs("test_outputs", exist_ok=True)
    filepath = f"test_outputs/{filename}"

    # 如果是bytes直接保存
    if isinstance(output, bytes):
        with open(filepath, 'wb') as f:
            f.write(output)
        return filepath

    # 如果是FileOutput对象
    if hasattr(output, 'read'):
        with open(filepath, 'wb') as f:
            f.write(output.read())
        return filepath

    return None


def main():
    print("\n" + "=" * 70)
    print("🎨 VTON 虚拟试穿模型测试")
    print("=" * 70)

    person_img = "test_data/test_data/model/model1.jpg"
    garment_img = "test_data/test_data/clother/clother2.jpg"

    print(f"\n📷 模特图: {person_img}")
    print(f"👕 衣服图: {garment_img}\n")

    print("📐 优化图片...")
    person_uri, person_size = resize_and_encode_image(person_img, max_size=768)
    garment_uri, garment_size = resize_and_encode_image(garment_img, max_size=768)
    print(f"✓ 模特图: {person_size//1024}KB")
    print(f"✓ 衣服图: {garment_size//1024}KB\n")

    # 要测试的两个模型
    models = [
        {
            "name": "IDM-VTON",
            "model": "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
            "inputs": {
                "human_img": person_uri,
                "garm_img": garment_uri,
                "garment_des": "shirt",
            },
        },
        {
            "name": "OOTDiffusion",
            "model": "viktorfa/oot_diffusion:9f8fa4956970dde99689af7488157a30aa152e23953526a605df1d77598343d7",
            "inputs": {
                "model_image": person_uri,
                "garment_image": garment_uri,
                "category": 0,
                "n_steps": 20,
            },
        },
    ]

    results = []
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    for i, model_cfg in enumerate(models):
        print(f"{'='*70}")
        print(f"🔄 [{i+1}/{len(models)}] {model_cfg['name']}")
        print(f"{'='*70}")

        start = time.time()
        try:
            print(f"正在调用 Replicate API...")
            output = replicate.run(model_cfg["model"], input=model_cfg["inputs"])
            elapsed = time.time() - start

            print(f"✅ API调用成功! 耗时: {elapsed:.1f}秒")
            print(f"   输出类型: {type(output)}")

            # 保存结果
            filename = f"{timestamp}_{model_cfg['name'].replace('-', '_').lower()}.jpg"
            filepath = save_result(output, filename)

            if filepath:
                print(f"💾 已保存: {filepath}")
                # 检查文件大小
                file_size = Path(filepath).stat().st_size
                print(f"   文件大小: {file_size:,} bytes (~{file_size//1024}KB)")

                results.append({
                    "name": model_cfg['name'],
                    "success": True,
                    "time": elapsed,
                    "file": filepath
                })
            else:
                print(f"❌ 保存失败")
                results.append({
                    "name": model_cfg['name'],
                    "success": False,
                    "time": elapsed,
                    "error": "无法保存输出"
                })

        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ 失败 ({elapsed:.1f}秒): {str(e)[:100]}")
            results.append({
                "name": model_cfg['name'],
                "success": False,
                "time": elapsed,
                "error": str(e)
            })

        # 等待避免速率限制
        if i < len(models) - 1:
            wait = 15
            print(f"\n⏳ 等待 {wait} 秒...")
            time.sleep(wait)

        print()

    # 汇总
    print("=" * 70)
    print("📊 测试结果")
    print("=" * 70)

    for r in results:
        if r["success"]:
            print(f"\n✅ {r['name']}")
            print(f"   耗时: {r['time']:.1f}秒")
            print(f"   文件: {r['file']}")
        else:
            print(f"\n❌ {r['name']}")
            print(f"   {r.get('error', 'Unknown')[:100]}")

    successful = [r for r in results if r["success"]]
    if successful:
        print(f"\n🎉 成功生成 {len(successful)} 个结果！")
        print(f"📁 查看: open test_outputs/")

        fastest = min(successful, key=lambda x: x["time"])
        print(f"\n🏆 最快: {fastest['name']} ({fastest['time']:.1f}秒)")
    else:
        print(f"\n⚠️  所有测试都失败了")

    print("=" * 70)


if __name__ == "__main__":
    main()
