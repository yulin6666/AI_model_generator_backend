# VTON虚拟试穿测试报告
**测试时间**: 2026-01-09
**测试图片**: model1.jpg + clother2.jpg

## 测试结果总结

### ✅ 成功的模型

#### 1. IDM-VTON (cuuupid/idm-vton)
- **状态**: ✅ 成功
- **耗时**: 20.2秒
- **质量**: 高质量，自然合成
- **输出文件**: `test_outputs/20260109_131217_idm_vton.jpg`
- **描述**: ECCV2024论文模型，虚拟试穿效果非常好，成功将粉色连帽外套合成到模特身上

**优点**:
- 生成速度快（~20秒）
- 衣服细节保留完整（帽子、拉链、口袋）
- 身体姿态自然
- 肤色和光照处理合理

### ❌ 失败/超时的模型

#### 2. OOTDiffusion (viktorfa/oot_diffusion)
- **状态**: ❌ 超时
- **原因**: The read operation timed out (61秒后超时)
- **可能原因**:
  - API响应慢
  - 网络不稳定
  - 模型负载高

#### 3. CatVTON (zhengchong/cat-vton)
- **状态**: ❌ 模型不存在
- **原因**: Model not found (404)

## 测试配置

### 图片优化
- 原始模特图: 237KB → 优化后: 64KB (768x768)
- 原始衣服图: 108KB → 优化后: 27KB (768x768)
- 优化方式: JPEG压缩 (quality=85)

### API配置
- Replicate API Token: 已配置
- Python版本: 3.11.14
- replicate库: 最新版本

## 可用的VTON模型列表

根据测试，Replicate上目前可用的VTON模型：

1. ✅ **cuuupid/idm-vton** - 推荐使用
   - 版本: `0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985`
   - 速度: 快 (~20秒)
   - 质量: 高

2. ⚠️ **viktorfa/oot_diffusion** - 不稳定
   - 版本: `9f8fa4956970dde99689af7488157a30aa152e23953526a605df1d77598343d7`
   - 速度: 慢/超时
   - 质量: 未知（未成功测试）

## 使用建议

### 推荐方案
使用 **IDM-VTON** 作为主要的虚拟试穿模型：
- 稳定可靠
- 速度快
- 质量高
- API调用简单

### 图片要求
- 格式: JPEG/PNG
- 建议尺寸: 768x768或更小
- 文件大小: < 100KB
- 模特图: 清晰的正面照，姿势自然
- 衣服图: 白色背景，衣服平铺或模特展示

### 成本预估
- 每次调用耗时: ~20秒
- Replicate定价: 按秒计费
- 建议: 账户余额保持 > $5 避免速率限制

## 运行测试脚本

```bash
# 使用虚拟环境
source .venv/bin/activate  # 或使用: .venv/bin/python

# 运行测试（推荐）
python test_vton_final2.py

# 查看结果
open test_outputs/
```

## 文件说明

- `test_vton_final2.py` - 主测试脚本（推荐）
- `test_outputs/` - 生成的结果图片目录
- `test_data/test_data/model/` - 模特图片目录
- `test_data/test_data/clother/` - 衣服图片目录

## 总结

🎉 **测试成功！** IDM-VTON模型效果优秀，能够高质量地将衣服合成到模特身上。

建议在生产环境中使用IDM-VTON，并根据实际需求调整图片尺寸和质量参数。
