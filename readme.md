# IDM-VTON API

高质量虚拟试穿API服务 - 基于IDM-VTON (ECCV2024)

[![Railway](https://img.shields.io/badge/Deploy-Railway-blueviolet)](https://railway.app)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)

## 📖 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [API文档](#api文档)
- [部署到Railway](#部署到railway)
- [测试](#测试)
- [常见问题](#常见问题)

## ✨ 功能特性

- 🎨 **高质量虚拟试穿** - 使用IDM-VTON (ECCV2024) 论文模型
- 🚀 **多种输入格式** - 支持URL、本地路径、base64 data URI
- 🖼️ **自动图片优化** - 自动调整大小和压缩，优化API调用
- ⚡ **异步处理** - 基于FastAPI的异步架构
- 📝 **完整文档** - 自动生成的OpenAPI文档
- 🔒 **环境变量管理** - 使用pydantic-settings管理配置
- 🐳 **Docker支持** - 可容器化部署
- 🚂 **Railway部署** - 一键部署到Railway

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd AI_model_generator_backend
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的Replicate API Token：

```env
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 🔑 在 [Replicate](https://replicate.com/account/api-tokens) 获取你的API Token

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务将运行在 `http://localhost:8000`

### 6. 查看文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API文档

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Content-Type**: `application/json`

### 端点列表

#### 1. Health Check

```bash
GET /
GET /health
```

检查服务状态。

**响应示例：**
```json
{
  "status": "ok",
  "service": "AI Model Generator API",
  "version": "0.1.0"
}
```

---

#### 2. 获取服务信息

```bash
GET /api/vton/info
```

获取IDM-VTON服务的详细信息。

**响应示例：**
```json
{
  "model": "IDM-VTON",
  "description": "High-quality virtual try-on model (ECCV2024)",
  "paper": "https://idm-vton.github.io/",
  "categories": ["upper_body", "lower_body", "dresses"],
  "parameters": {
    "denoise_steps": {
      "type": "integer",
      "min": 10,
      "max": 50,
      "default": 30,
      "description": "Higher values = better quality but slower"
    }
  }
}
```

---

#### 3. 虚拟试穿（JSON请求）

```bash
POST /api/vton/try-on
Content-Type: application/json
```

使用JSON格式提交虚拟试穿请求。

**请求体：**
```json
{
  "person_image": "https://example.com/model.jpg",
  "garment_image": "https://example.com/shirt.jpg",
  "garment_description": "blue cotton shirt",
  "category": "upper_body",
  "denoise_steps": 30
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| person_image | string | ✅ | - | 模特图片（URL或data URI） |
| garment_image | string | ✅ | - | 衣服图片（URL或data URI） |
| garment_description | string | ❌ | "shirt" | 衣服描述 |
| category | string | ❌ | "upper_body" | 衣服类别 |
| denoise_steps | integer | ❌ | 30 | 去噪步数（10-50） |

**类别选项：**
- `upper_body` - 上衣（衬衫、T恤、外套等）
- `lower_body` - 下装（裤子、裙子等）
- `dresses` - 连衣裙

**响应示例：**
```json
{
  "success": true,
  "output_url": "https://replicate.delivery/pbxt/xxx.jpg",
  "elapsed_time": 25.3,
  "input_size": {
    "person_kb": 120,
    "garment_kb": 85
  },
  "error": null
}
```

**cURL示例：**
```bash
curl -X POST "http://localhost:8000/api/vton/try-on" \
  -H "Content-Type: application/json" \
  -d '{
    "person_image": "https://example.com/model.jpg",
    "garment_image": "https://example.com/shirt.jpg",
    "garment_description": "blue cotton shirt",
    "category": "upper_body",
    "denoise_steps": 30
  }'
```

**Python示例：**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/vton/try-on",
    json={
        "person_image": "https://example.com/model.jpg",
        "garment_image": "https://example.com/shirt.jpg",
        "garment_description": "blue cotton shirt",
        "category": "upper_body",
        "denoise_steps": 30
    }
)

result = response.json()
if result["success"]:
    print(f"输出图片: {result['output_url']}")
    print(f"耗时: {result['elapsed_time']:.1f}秒")
```

---

#### 4. 虚拟试穿（文件上传）

```bash
POST /api/vton/try-on/upload
Content-Type: multipart/form-data
```

直接上传图片文件进行虚拟试穿。

**表单字段：**
- `person_image` (file, required) - 模特图片文件
- `garment_image` (file, required) - 衣服图片文件
- `garment_description` (string, optional) - 衣服描述
- `category` (string, optional) - 衣服类别
- `denoise_steps` (integer, optional) - 去噪步数

**cURL示例：**
```bash
curl -X POST "http://localhost:8000/api/vton/try-on/upload" \
  -F "person_image=@./test_data/model1.jpg" \
  -F "garment_image=@./test_data/shirt.jpg" \
  -F "garment_description=blue shirt" \
  -F "category=upper_body" \
  -F "denoise_steps=30"
```

**Python示例（使用requests）：**
```python
import requests

with open("model.jpg", "rb") as person_file, \
     open("shirt.jpg", "rb") as garment_file:

    response = requests.post(
        "http://localhost:8000/api/vton/try-on/upload",
        files={
            "person_image": person_file,
            "garment_image": garment_file
        },
        data={
            "garment_description": "blue cotton shirt",
            "category": "upper_body",
            "denoise_steps": 30
        }
    )

result = response.json()
print(result)
```

**JavaScript示例（使用FormData）：**
```javascript
const formData = new FormData();
formData.append('person_image', personFileInput.files[0]);
formData.append('garment_image', garmentFileInput.files[0]);
formData.append('garment_description', 'blue cotton shirt');
formData.append('category', 'upper_body');
formData.append('denoise_steps', '30');

fetch('http://localhost:8000/api/vton/try-on/upload', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

---

### 响应码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 422 | 请求参数错误 |
| 500 | 服务器错误（包含错误详情） |

### 错误处理

当请求失败时，响应会包含错误信息：

```json
{
  "success": false,
  "output_url": null,
  "elapsed_time": 2.5,
  "input_size": null,
  "error": "Invalid image URL or file"
}
```

## 🐳 Docker部署

### 构建镜像

```bash
docker build -t idm-vton-api .
```

### 运行容器

```bash
docker run -d \
  -p 8000:8000 \
  -e REPLICATE_API_TOKEN=your_token_here \
  --name idm-vton-api \
  idm-vton-api
```

## 🚂 部署到Railway

### 方法1: 使用Railway CLI

1. 安装Railway CLI：
```bash
npm install -g @railway/cli
```

2. 登录Railway：
```bash
railway login
```

3. 初始化项目：
```bash
railway init
```

4. 设置环境变量：
```bash
railway variables set REPLICATE_API_TOKEN=your_token_here
```

5. 部署：
```bash
railway up
```

### 方法2: 通过GitHub连接

1. 将代码推送到GitHub
2. 在 [Railway](https://railway.app) 创建新项目
3. 选择 "Deploy from GitHub repo"
4. 选择你的仓库
5. 添加环境变量 `REPLICATE_API_TOKEN`
6. Railway会自动检测并部署

### Railway环境变量配置

在Railway项目设置中添加以下环境变量：

```
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PORT=8000
```

Railway会自动设置`PORT`环境变量，应用会自动使用。

## 🧪 测试

### 使用测试脚本

项目包含完整的测试脚本 `test_api.py`：

```bash
# 测试本地服务
python test_api.py

# 测试远程服务
python test_api.py --url https://your-app.railway.app
```

测试脚本会执行以下操作：
1. ✅ 检查服务健康状态
2. ✅ 获取服务信息
3. ✅ 测试虚拟试穿API（使用测试图片）
4. ✅ 验证响应格式和数据
5. 📊 生成测试报告

### 手动测试

#### 1. 测试健康检查

```bash
curl http://localhost:8000/health
```

#### 2. 测试服务信息

```bash
curl http://localhost:8000/api/vton/info
```

#### 3. 测试虚拟试穿

使用项目提供的测试图片：

```bash
curl -X POST "http://localhost:8000/api/vton/try-on/upload" \
  -F "person_image=@./test_data/test_data/model/model1.jpg" \
  -F "garment_image=@./test_data/test_data/clother/clother2.jpg" \
  -F "garment_description=shirt" \
  -F "category=upper_body"
```

### 测试数据

项目包含测试图片位于 `test_data/test_data/` 目录：
- `model/` - 模特图片
- `clother/` - 衣服图片

## 📊 性能优化

API自动执行以下优化：
- ✅ 图片自动调整大小（最大768x768）
- ✅ 图片压缩（JPEG quality=85）
- ✅ 异步处理
- ✅ 自动重试机制（Replicate内置）

## ❓ 常见问题

### Q: API调用很慢怎么办？

A: IDM-VTON是高质量模型，通常需要20-40秒。可以：
- 降低`denoise_steps`参数（如20）来加快速度
- 确保输入图片不要太大（推荐768x768以下）

### Q: 返回错误"Invalid API token"？

A: 检查以下几点：
1. `.env`文件中的`REPLICATE_API_TOKEN`是否正确
2. Token是否以`r8_`开头
3. Token是否有效（在Replicate网站检查）

### Q: 支持哪些图片格式？

A: 支持：
- ✅ JPEG / JPG
- ✅ PNG
- ❌ GIF (会转换为静态图)
- ❌ WebP (需要先转换)

### Q: 如何获取更好的试穿效果？

A: 建议：
1. 使用高清图片（但不要超过2000x2000）
2. 模特图片：正面站立，清晰可见
3. 衣服图片：平铺或正面展示
4. 增加`denoise_steps`到40-50（会变慢）
5. 准确填写`garment_description`

### Q: 可以商用吗？

A: 本项目代码MIT协议。但请注意：
- IDM-VTON模型的使用需遵守其许可证
- Replicate API的使用需遵守其服务条款
- 建议查看[IDM-VTON项目](https://idm-vton.github.io/)了解详情

### Q: 如何处理大量请求？

A: 建议：
1. 使用Railway的Pro计划获取更多资源
2. 实现请求队列系统
3. 添加Redis缓存常见结果
4. 考虑使用Replicate的预测缓存功能

### Q: 支持批量处理吗？

A: 当前API是单次处理。批量处理建议：
1. 在客户端并行发送多个请求
2. 实现任务队列（如Celery + Redis）
3. 使用异步客户端库（如httpx）

## 📖 相关资源

- [IDM-VTON论文](https://idm-vton.github.io/)
- [Replicate平台](https://replicate.com)
- [FastAPI文档](https://fastapi.tiangolo.com)
- [Railway文档](https://docs.railway.app)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

## 🔧 技术栈

- **FastAPI** - 现代Web框架
- **Replicate** - AI模型托管平台
- **IDM-VTON** - ECCV2024虚拟试穿模型
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI服务器
- **httpx** - 异步HTTP客户端
- **Pillow** - 图片处理

## 📞 支持

遇到问题？
- 查看 [常见问题](#常见问题)
- 提交 [Issue](https://github.com/your-repo/issues)
- 查看 [API文档](http://localhost:8000/docs)

---

Made with ❤️ using IDM-VTON
