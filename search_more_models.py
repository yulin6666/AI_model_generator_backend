#!/usr/bin/env python3
"""
搜索更多VTON模型并测试
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保API token已设置
if not os.getenv("REPLICATE_API_TOKEN"):
    raise ValueError("请在.env文件中设置REPLICATE_API_TOKEN")

import replicate

client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

print("\n搜索其他VTON相关模型...")
print("=" * 70)

# 更多已知模型
additional_models = [
    "fashn/fashn-ai-virtual-try-on",
    "tstramer/midjourney-vton",
    "salehhashemi1992/virtual-try-on",
    "cjwbw/virtual-try-on",
    "vton/idm-vton",
]

available = []

for model_name in additional_models:
    try:
        model = client.models.get(model_name)
        version_id = model.latest_version.id if model.latest_version else "N/A"
        print(f"✅ {model_name}")
        print(f"   版本: {version_id}")
        available.append((model_name, version_id))
    except Exception as e:
        error = str(e)
        if "404" not in error:
            print(f"❌ {model_name} - {error[:60]}")

print(f"\n找到 {len(available)} 个额外的可用模型")
print("=" * 70)
