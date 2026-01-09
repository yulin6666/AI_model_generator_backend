#!/usr/bin/env python3
"""
搜索 Replicate 上可用的 VTON 模型
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保API token已设置
if not os.getenv("REPLICATE_API_TOKEN"):
    raise ValueError("请在.env文件中设置REPLICATE_API_TOKEN")

import replicate

try:
    client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

    print("\n搜索 'virtual try on' 模型...")
    print("=" * 60)

    # 尝试几个已知的模型
    known_models = [
        "yisol/idm-vton",
        "cuuupid/idm-vton",
        "viktorfa/oot_diffusion",
        "zhengchong/cat-vton",
        "kataraai/virtual-try-on",
        "levihsu/ootdiffusion",
    ]

    available_models = []

    for model_name in known_models:
        try:
            model = client.models.get(model_name)
            print(f"✅ {model_name}")
            print(f"   最新版本: {model.latest_version.id if model.latest_version else 'N/A'}")
            available_models.append(model_name)
        except Exception as e:
            print(f"❌ {model_name} - {str(e)[:80]}")

    print("\n" + "=" * 60)
    print(f"找到 {len(available_models)} 个可用模型")
    print("=" * 60)

except Exception as e:
    print(f"错误: {e}")
