#!/usr/bin/env python3
"""
下载最近一次虚拟试穿的结果图片
"""
import requests
import json
import sys
from pathlib import Path

# 运行测试并捕获输出
print("🔄 正在进行虚拟试穿测试...")
print()

# 调用API
import requests

API_URL = "https://web-production-ee100.up.railway.app"

# 测试图片路径
model_image = "test_data/test_data/model/model1.jpg"
garment_image = "test_data/test_data/clother/clother2.jpg"

try:
    with open(model_image, 'rb') as person_file, \
         open(garment_image, 'rb') as garment_file:

        print(f"📤 上传图片到 {API_URL}")
        print(f"   模特: {model_image}")
        print(f"   衣服: {garment_image}")
        print()

        files = {
            'person_image': (model_image, person_file, 'image/jpeg'),
            'garment_image': (garment_image, garment_file, 'image/jpeg')
        }

        data = {
            'garment_description': 'shirt',
            'category': 'upper_body',
            'denoise_steps': 30
        }

        print("⏳ 正在生成虚拟试穿效果... (需要20-40秒)")
        response = requests.post(
            f"{API_URL}/api/vton/try-on/upload",
            files=files,
            data=data,
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        if result.get('success'):
            output_url = result['output_url']
            elapsed_time = result['elapsed_time']

            print()
            print("✅ 生成成功！")
            print(f"⏱️  耗时: {elapsed_time:.1f}秒")
            print()
            print(f"🔗 结果URL:")
            print(f"   {output_url}")
            print()

            # 下载结果
            print("📥 正在下载结果...")
            img_response = requests.get(output_url)
            img_response.raise_for_status()

            # 保存到本地
            output_dir = Path("api_results")
            output_dir.mkdir(exist_ok=True)

            output_file = output_dir / "latest_result.jpg"
            with open(output_file, 'wb') as f:
                f.write(img_response.content)

            print(f"💾 已保存到: {output_file}")
            print()
            print("🖼️  打开图片查看:")
            print(f"   open {output_file}")
            print()

            # 自动打开图片（macOS）
            import subprocess
            subprocess.run(['open', str(output_file)])

        else:
            print(f"❌ 失败: {result.get('error', 'Unknown error')}")
            sys.exit(1)

except FileNotFoundError as e:
    print(f"❌ 文件未找到: {e}")
    print("请确保 test_data/test_data/ 目录存在并包含测试图片")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"❌ API请求失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
