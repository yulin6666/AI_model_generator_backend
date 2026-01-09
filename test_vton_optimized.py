#!/usr/bin/env python3
"""
优化图片并重试VTON测试
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
import httpx


def resize_and_encode_image(image_path: str, max_size=1024) -> str:
    """调整图片大小并转换为data URI"""
    img = Image.open(image_path)

    # 转换为RGB（如果是RGBA或其他格式）
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 保持宽高比调整大小
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # 转换为JPEG并压缩
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    img_data = buffer.getvalue()

    # 编码为base64
    b64_data = base64.b64encode(img_data).decode('utf-8')

    return f"data:image/jpeg;base64,{b64_data}", len(b64_data)


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
                return filepath
    except Exception as e:
        print(f"   下载失败: {e}")
    return None


def main():
    print("\n" + "=" * 70)
    print("🎨 VTON 虚拟试穿测试 (优化版)")
    print("=" * 70)

    person_img = "test_data/test_data/model/model1.jpg"
    garment_img = "test_data/test_data/clother/clother2.jpg"

    print(f"\n📷 模特图: {person_img}")
    print(f"👕 衣服图: {garment_img}\n")

    print("📐 优化图片尺寸...")
    person_uri, person_size = resize_and_encode_image(person_img, max_size=768)
    garment_uri, garment_size = resize_and_encode_image(garment_img, max_size=768)
    print(f"✓ 模特图优化: {person_size:,} bytes (~{person_size//1024}KB)")
    print(f"✓ 衣服图优化: {garment_size:,} bytes (~{garment_size//1024}KB)\n")

    # 只测试一个模型，避免速率限制
    model_cfg = {
        "name": "IDM-VTON",
        "model": "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
        "inputs": {
            "human_img": person_uri,
            "garm_img": garment_uri,
            "garment_des": "beautiful shirt",
        },
        "desc": "IDM-VTON - ECCV2024 高质量虚拟试穿"
    }

    print(f"{'='*70}")
    print(f"🔄 {model_cfg['name']}")
    print(f"   {model_cfg['desc']}")
    print(f"{'='*70}")

    start = time.time()
    try:
        print(f"正在调用 Replicate API (这可能需要1-2分钟)...")

        # 使用更长的超时时间
        output = replicate.run(
            model_cfg["model"],
            input=model_cfg["inputs"]
        )
        elapsed = time.time() - start

        # 解析输出
        result_url = None
        if isinstance(output, str):
            result_url = output
        elif isinstance(output, list) and len(output) > 0:
            result_url = str(output[0])
        elif hasattr(output, '__iter__'):
            try:
                results_list = list(output)
                result_url = str(results_list[0]) if results_list else None
            except:
                pass

        if result_url:
            print(f"\n✅ 成功! 耗时: {elapsed:.1f}秒")
            print(f"   输出URL: {result_url}\n")

            # 下载结果
            print("💾 正在下载结果图片...")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_idm_vton_result.png"
            filepath = download_result(result_url, filename)

            if filepath:
                print(f"✅ 已保存: {filepath}")
                print(f"\n🎉 成功！你可以查看结果图片:")
                print(f"   {filepath}")
            else:
                print(f"❌ 下载失败，但可以访问URL查看:")
                print(f"   {result_url}")
        else:
            print(f"\n❌ 无法从API响应中提取结果")
            print(f"   输出类型: {type(output)}")
            print(f"   输出内容: {output}")

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ 失败 ({elapsed:.1f}秒)")
        error_msg = str(e)
        print(f"   错误: {error_msg}\n")

        # 提供故障排查建议
        print("💡 故障排查:")
        if "throttled" in error_msg.lower() or "429" in error_msg:
            print("   - API速率限制，请稍后重试")
        elif "quota" in error_msg.lower() or "balance" in error_msg.lower():
            print("   - API配额不足，请充值账户")
            print("   - 访问: https://replicate.com/account/billing")
        elif "timeout" in error_msg.lower():
            print("   - 请求超时，可能是图片太大或网络问题")
        elif "404" in error_msg:
            print("   - 模型不存在或已删除")
        else:
            print("   - 请检查API token是否有效")
            print("   - 访问: https://replicate.com/account/api-tokens")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
