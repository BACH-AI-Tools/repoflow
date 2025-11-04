# 项目模板示例

## Python 项目结构

```
my-python-project/
├── src/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_main.py
├── requirements.txt
├── setup.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

### requirements.txt
```
requests>=2.28.0
click>=8.1.0
```

### setup.py
```python
from setuptools import setup, find_packages

setup(
    name="my-python-project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "click>=8.1.0",
    ],
)
```

## Node.js 项目结构

```
my-node-project/
├── src/
│   └── index.js
├── test/
│   └── index.test.js
├── package.json
├── README.md
├── LICENSE
└── .gitignore
```

### package.json
```json
{
  "name": "my-node-project",
  "version": "1.0.0",
  "description": "A sample Node.js project",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "test": "jest",
    "build": "webpack"
  },
  "keywords": ["example"],
  "author": "Your Name",
  "license": "MIT",
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
```

## Docker 项目结构

```
my-docker-project/
├── src/
│   └── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .dockerignore
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "src/app.py"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    volumes:
      - ./data:/app/data
```

## 通用 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# Node
node_modules/
npm-debug.log
yarn-error.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Env files
.env
.env.local
*.key
*.pem

# Build
dist/
build/
*.egg-info/
```

## 环境变量管理

### .env.example
```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=your_username
DB_PASSWORD=your_password

# API 密钥
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# 应用配置
APP_ENV=development
DEBUG=true
```

### 使用说明
1. 复制 `.env.example` 为 `.env`
2. 填入实际的配置值
3. 确保 `.env` 在 `.gitignore` 中
4. 提交 `.env.example` 到仓库作为模板

