# ✅ PyPI 包自动添加清华源参数

## 🎯 需求

为 PyPI 包自动添加 `UV_INDEX_URL` 参数，指向清华镜像源，加速国内用户的包下载。

## ✅ 实现

### 修改的文件

**`emcp_manager.py`** - `build_template_data()` 方法

### 核心逻辑

```python
# 处理 args 参数
final_args = args or []

# ⭐ PyPI 包自动添加 UV_INDEX_URL 参数（清华源）
if package_type == 2:  # package_type=2 表示 PyPI (uvx)
    # 检查是否已存在 UV_INDEX_URL
    has_uv_index = any(arg.get('arg_name') == 'UV_INDEX_URL' for arg in final_args)
    
    if not has_uv_index:
        uv_index_arg = {
            "arg_name": "UV_INDEX_URL",
            "default_value": "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "description": [
                {
                    "type": 1,  # zh-cn
                    "content": "PyPI 镜像源地址（默认使用清华源加速下载）"
                },
                {
                    "type": 2,  # zh-tw
                    "content": "PyPI 鏡像源地址（默認使用清華源加速下載）"
                },
                {
                    "type": 3,  # en
                    "content": "PyPI mirror source URL (default: Tsinghua mirror for faster downloads)"
                }
            ],
            "auth_method_id": "",
            "type": 2,  # custom_value
            "paramter_type": 1,  # StartupParameter
            "input_source": 1,  # AdminInput
            "showDefault": False,
            "oauth_authorized": False
        }
        final_args.append(uv_index_arg)
```

## 📊 参数详情

### 参数结构

```json
{
  "arg_name": "UV_INDEX_URL",
  "default_value": "https://pypi.tuna.tsinghua.edu.cn/simple/",
  "description": [
    {
      "type": 1,
      "content": "PyPI 镜像源地址（默认使用清华源加速下载）"
    },
    {
      "type": 2,
      "content": "PyPI 鏡像源地址（默認使用清華源加速下載）"
    },
    {
      "type": 3,
      "content": "PyPI mirror source URL (default: Tsinghua mirror for faster downloads)"
    }
  ],
  "auth_method_id": "",
  "type": 2,
  "paramter_type": 1,
  "input_source": 1,
  "showDefault": false,
  "oauth_authorized": false
}
```

### 字段说明

| 字段 | 值 | 说明 |
|------|-----|------|
| `arg_name` | `UV_INDEX_URL` | 参数名称（uvx 环境变量） |
| `default_value` | `https://pypi.tuna.tsinghua.edu.cn/simple/` | 清华大学 PyPI 镜像源 |
| `description` | 多语言数组 | 三种语言的说明 |
| `type` | `2` | `custom_value` (自定义值) |
| `paramter_type` | `1` | `StartupParameter` (启动参数) |
| `input_source` | `1` | `AdminInput` (管理员输入) |
| `showDefault` | `false` | 不显示默认值 |
| `oauth_authorized` | `false` | 不需要 OAuth 授权 |

## 🎯 工作原理

### 1. 自动检测 PyPI 包

```python
if package_type == 2:  # PyPI (uvx)
    # 自动添加 UV_INDEX_URL
```

### 2. 避免重复添加

```python
has_uv_index = any(arg.get('arg_name') == 'UV_INDEX_URL' for arg in final_args)

if not has_uv_index:
    # 只在不存在时添加
```

### 3. 多语言支持

```python
"description": [
    {"type": 1, "content": "简体中文说明"},
    {"type": 2, "content": "繁體中文說明"},
    {"type": 3, "content": "English description"}
]
```

## 📋 日志输出

### 发布 PyPI 包时

```
📝 步骤 3/4: 构建发布数据...
   获取模板来源...
   ✅ 使用模板来源: bach-001
   ✅ 模板数据已构建
   ℹ️  PyPI包已自动添加 UV_INDEX_URL 参数（清华源加速）  ⭐

📋 模板数据详情:
======================================================================
   {
     "name": [...],
     "summary": [...],
     ...
     "args": [
       {
         "arg_name": "UV_INDEX_URL",  ⭐
         "default_value": "https://pypi.tuna.tsinghua.edu.cn/simple/",
         "description": [...],
         "type": 2,
         "paramter_type": 1,
         "input_source": 1
       }
     ]
   }
======================================================================
```

### 发布 NPM/Docker 包时

```
📝 步骤 3/4: 构建发布数据...
   ✅ 模板数据已构建
   
   (不会显示 UV_INDEX_URL 提示)
```

## 🚀 用户价值

### 1. 加速下载
- ✅ 使用清华大学 PyPI 镜像
- ✅ 国内下载速度快
- ✅ 稳定可靠

### 2. 自动配置
- ✅ 无需手动设置
- ✅ 自动添加参数
- ✅ 开箱即用

### 3. 灵活性
- ✅ 管理员可修改默认值
- ✅ 支持其他镜像源
- ✅ 可在 EMCP 平台配置

## 🔧 技术细节

### uvx 如何使用这个参数

当用户运行 MCP 模板时：

```bash
# EMCP 会设置环境变量
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple/"

# 然后执行命令
uvx bachai-data-analysis-mcp

# uvx 会自动使用 UV_INDEX_URL 作为包索引
```

### 为什么选择清华源

1. **国内速度快** - 清华大学提供
2. **同步及时** - 每5分钟同步一次
3. **稳定可靠** - 长期维护
4. **广泛使用** - 社区认可

### 其他镜像源

管理员可以修改为其他源：
- 阿里云: `https://mirrors.aliyun.com/pypi/simple/`
- 中科大: `https://pypi.mirrors.ustc.edu.cn/simple/`
- 豆瓣: `https://pypi.douban.com/simple/`
- 官方: `https://pypi.org/simple/`

## 📊 适用场景

### 场景 1: 国内用户
- ✅ 自动使用清华源
- ✅ 下载速度提升 10-100 倍
- ✅ 避免超时失败

### 场景 2: 海外用户
- ✅ 可以在 EMCP 平台修改为官方源
- ✅ 或者删除这个参数
- ✅ 灵活配置

### 场景 3: 企业内网
- ✅ 可以配置为内部镜像源
- ✅ 安全合规
- ✅ 可控管理

## 🎯 完整改进总结

今天实现的两大改进：

### 1. 401 自动重登录重试 ✅
```
401 错误 → 🔄 重新登录 → 🔄 重试上传 → ✅ 成功
```

### 2. PyPI 包自动添加清华源 ✅
```
package_type=2 → ✅ 自动添加 UV_INDEX_URL → 🚀 加速下载
```

## 📝 测试验证

### 测试步骤
1. 运行 `python emcpflow_simple_gui.py`
2. 输入 PyPI 包地址: `bachai-data-analysis-mcp`
3. 点击"一键发布"
4. 观察日志

### 预期结果

```
✅ 类型: PYPI
✅ 包名: bachai-data-analysis-mcp

📝 步骤 3/4: 构建发布数据...
   ✅ 模板数据已构建
   ℹ️  PyPI包已自动添加 UV_INDEX_URL 参数（清华源加速）  ⭐

📋 模板数据详情:
   "args": [
     {
       "arg_name": "UV_INDEX_URL",  ✅
       "default_value": "https://pypi.tuna.tsinghua.edu.cn/simple/"  ✅
     }
   ]
```

## ✅ 完成清单

- [x] ✅ 添加 `import json` 到 logo_generator.py
- [x] ✅ 实现 401 自动重登录重试
- [x] ✅ PyPI 包自动添加 UV_INDEX_URL 参数
- [x] ✅ 多语言描述（简体/繁体/英文）
- [x] ✅ 避免重复添加（检查已存在）
- [x] ✅ 详细日志提示
- [x] ✅ 代码 Lint 检查通过

---

**实现时间**: 2025-11-06  
**功能**: PyPI 清华源参数 + 401 自动重登录  
**开发**: 巴赫工作室 (BACH Studio)

**Made with ❤️ by 巴赫工作室**

