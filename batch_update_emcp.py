#!/usr/bin/env python3
"""
批量更新 EMCP 平台已发布的 MCP 模板
- 不查询包源，直接使用 EMCP 已有描述
- 重新根据已有描述生成正确的分类
- 重新生成简洁的介绍（summary）
- 重新生成完整描述（description）
- 重新生成 Logo
- ⭐ 记录已更新的模板，避免重复更新
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.emcp_manager import EMCPManager
from src.ai_generator import AITemplateGenerator
from src.unified_config_manager import UnifiedConfigManager
from src.jimeng_logo_generator import JimengLogoGenerator
from src.jimeng_api_generator import JimengAPIGenerator

# 已处理模板记录文件
PROCESSED_FILE = Path("outputs/batch_update_processed.json")


class BatchEMCPUpdater:
    """批量更新 EMCP 模板（不查询包源）"""
    
    def __init__(self):
        self.config_mgr = UnifiedConfigManager()
        self.emcp_manager = None
        self.ai_generator = None
        self.jimeng_client = None
        
        # 已处理的模板记录
        self.processed_templates: Dict[str, dict] = {}
        self._load_processed_records()
        
        # 统计
        self.stats = {
            "total": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "logo_generated": 0
        }
    
    def _load_processed_records(self):
        """加载已处理的模板记录"""
        try:
            if PROCESSED_FILE.exists():
                with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                    self.processed_templates = json.load(f)
                print(f"📋 已加载 {len(self.processed_templates)} 条处理记录")
        except Exception as e:
            print(f"⚠️ 加载处理记录失败: {e}")
            self.processed_templates = {}
    
    def _save_processed_record(self, template_id: str, source_id: str):
        """保存已处理的模板记录"""
        try:
            PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.processed_templates[template_id] = {
                "source_id": source_id,
                "updated_at": datetime.now().isoformat()
            }
            with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.processed_templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存处理记录失败: {e}")
    
    def is_already_processed(self, template_id: str) -> bool:
        """检查模板是否已处理过"""
        return template_id in self.processed_templates
    
    def login_emcp(self) -> bool:
        """登录 EMCP 平台"""
        print("\n" + "="*60)
        print("🔐 登录 EMCP 平台")
        print("="*60)
        
        emcp_config = self.config_mgr.get_emcp_config()
        
        if not emcp_config.get("phone_number"):
            print("❌ 未配置 EMCP 账号，请先在设置中配置")
            return False
        
        self.emcp_manager = EMCPManager()
        self.emcp_manager.base_url = emcp_config.get('base_url', 'https://sit-emcp.kaleido.guru')
        
        try:
            user_info = self.emcp_manager.login(
                emcp_config['phone_number'],
                emcp_config['validation_code'],
                fallback_token=emcp_config.get('fallback_token')
            )
            print(f"✅ 登录成功")
            print(f"   👤 用户: {user_info.get('user_name', 'Unknown')}")
            print(f"   🆔 用户ID: {user_info.get('uid')}")
            return True
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False
    
    def init_ai_generator(self) -> bool:
        """初始化 AI 生成器"""
        print("\n" + "="*60)
        print("🤖 初始化 AI 生成器")
        print("="*60)
        
        config = self.config_mgr.load_config()
        ai_config = config.get("azure_openai", {})
        
        if not ai_config.get("endpoint") or not ai_config.get("api_key"):
            print("❌ 未配置 Azure OpenAI，无法使用 AI 生成")
            return False
        
        try:
            self.ai_generator = AITemplateGenerator(
                azure_endpoint=ai_config['endpoint'],
                api_key=ai_config['api_key'],
                api_version=ai_config.get('api_version', '2024-02-15-preview'),
                deployment_name=ai_config['deployment_name'],
                emcp_manager=self.emcp_manager
            )
            print(f"✅ AI 生成器初始化成功")
            print(f"   📍 Endpoint: {ai_config['endpoint'][:50]}...")
            print(f"   🤖 Model: {ai_config['deployment_name']}")
            return True
        except Exception as e:
            print(f"❌ AI 生成器初始化失败: {e}")
            return False
    
    def init_jimeng_client(self) -> bool:
        """初始化即梦 Logo 生成器（使用 API 方式，从配置读取密钥）"""
        print("\n" + "="*60)
        print("🎨 初始化即梦 API Logo 生成器")
        print("="*60)
        
        try:
            # 从配置读取密钥
            ak, sk = self.config_mgr.get_jimeng_api_credentials()
            if not ak or not sk:
                print("⚠️  即梦 API 密钥未配置，请在设置中配置 Access Key 和 Secret Key")
                return False
            
            self.jimeng_api = JimengAPIGenerator(ak, sk)
            return True
            
        except Exception as e:
            print(f"⚠️  即梦 API 初始化失败: {e}")
            return False
    
    def generate_logo(self, source_id: str, description: str) -> Optional[str]:
        """根据描述生成 Logo（使用即梦 API）并上传到 EMCP"""
        if not hasattr(self, 'jimeng_api') or not self.jimeng_api:
            return None
        
        try:
            # ⭐ 使用即梦 API 生成 Logo
            result = self.jimeng_api.generate_logo_for_mcp(
                description=description,
                mcp_name=source_id
            )
            
            if result.get('success') and result.get('image_url'):
                image_url = result['image_url']
                print(f"      📥 即梦原始 URL: {image_url[:60]}...")
                
                # ⭐ 必须上传到 EMCP，不能使用即梦的临时 URL
                if image_url.startswith('http'):
                    emcp_url = self._upload_to_emcp(image_url)
                    if emcp_url:
                        print(f"      ✅ EMCP URL: {emcp_url}")
                        return emcp_url
                    else:
                        print(f"      ❌ 上传 EMCP 失败，Logo 将不更新")
                        return None  # ⭐ 不使用即梦临时 URL
                elif image_url.startswith('data:'):
                    emcp_url = self._upload_base64_to_emcp(image_url)
                    if emcp_url:
                        print(f"      ✅ EMCP URL: {emcp_url}")
                        return emcp_url
                    else:
                        print(f"      ❌ 上传 EMCP 失败，Logo 将不更新")
                        return None
                
                # 其他格式（不应该出现）
                return None
            
        except Exception as e:
            print(f"      ⚠️ Logo 生成失败: {e}")
        
        return None
    
    def _upload_to_emcp(self, image_url: str) -> Optional[str]:
        """上传图片到 EMCP"""
        try:
            if not self.emcp_manager:
                return None
            
            emcp_config = self.config_mgr.get_emcp_config()
            base_url = emcp_config.get("base_url", "https://sit-emcp.kaleido.guru")
            
            # 下载图片
            import requests
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return None
            
            # 上传到 EMCP
            upload_url = f"{base_url}/api/proxyStorage/upload"
            files = {'file': ('logo.png', response.content, 'image/png')}
            headers = {'token': self.emcp_manager.session_key}
            
            upload_response = requests.post(upload_url, files=files, headers=headers, timeout=30)
            if upload_response.status_code == 200:
                data = upload_response.json()
                if data.get('err_code') == 0:
                    return data.get('body', {}).get('fileUrl', '')
            
        except Exception as e:
            print(f"      ⚠️ 上传失败: {e}")
        
        return None
    
    def _upload_base64_to_emcp(self, base64_data: str) -> Optional[str]:
        """上传 base64 图片到 EMCP"""
        try:
            if not self.emcp_manager:
                return None
            
            import base64 as b64
            
            # 解析 base64
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            image_bytes = b64.b64decode(base64_data)
            
            emcp_config = self.config_mgr.get_emcp_config()
            base_url = emcp_config.get("base_url", "https://sit-emcp.kaleido.guru")
            
            # 上传
            import requests
            upload_url = f"{base_url}/api/proxyStorage/upload"
            files = {'file': ('logo.png', image_bytes, 'image/png')}
            headers = {'token': self.emcp_manager.session_key}
            
            response = requests.post(upload_url, files=files, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('err_code') == 0:
                    return data.get('body', {}).get('fileUrl', '')
            
        except Exception as e:
            print(f"      ⚠️ 上传失败: {e}")
        
        return None
    
    def extract_text(self, data, lang_type: int = 1) -> str:
        """从多语言数据中提取文本"""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('type') == lang_type:
                    return item.get('content', '')
        elif isinstance(data, str):
            return data
        return ''
    
    def extract_existing_description(self, template: Dict) -> str:
        """从已有模板中提取描述（不查询包源）"""
        # 优先使用 description
        desc = self.extract_text(template.get('description', []))
        if desc and len(desc) > 20:
            return desc
        
        # 降级使用 summary
        summary = self.extract_text(template.get('summary', []))
        if summary:
            return summary
        
        return ''
    
    def get_all_my_templates(self) -> List[Dict]:
        """获取我发布的所有模板"""
        print("\n" + "="*60)
        print("📋 获取已发布的模板列表")
        print("="*60)
        
        all_templates = []
        page = 1
        page_size = 50
        
        while True:
            try:
                result = self.emcp_manager.query_mcp_templates(
                    template_source_id=None,  # 获取所有
                    page_index=page,
                    page_size=page_size
                )
                
                if not result:
                    break
                
                # result 可能是列表或包含 items 的字典
                items = result if isinstance(result, list) else result.get('items', [])
                
                if not items:
                    break
                
                all_templates.extend(items)
                print(f"   📄 第 {page} 页: 获取 {len(items)} 个模板")
                
                # 如果返回数量少于 page_size，说明已经是最后一页
                if len(items) < page_size:
                    break
                
                page += 1
                time.sleep(0.5)  # 避免请求过快
                
            except Exception as e:
                print(f"   ⚠️ 获取第 {page} 页失败: {e}")
                break
        
        print(f"\n✅ 共获取到 {len(all_templates)} 个模板")
        return all_templates
    
    def update_single_template(self, template: Dict, categories: List[Dict], 
                                category_map: Dict,
                                dry_run: bool = False, regenerate_logo: bool = True,
                                force: bool = False) -> bool:
        """更新单个模板（不查询包源，使用已有描述）"""
        template_id = template.get('template_id', '')
        source_id = template.get('template_source_id', '')
        
        # 获取当前名称
        current_name = self.extract_text(template.get('name', []))
        if not current_name:
            current_name = source_id
        
        print(f"\n   📦 {source_id}")
        print(f"      当前名称: {current_name}")
        
        # ⭐ 检查是否已处理过
        if not force and self.is_already_processed(template_id):
            record = self.processed_templates.get(template_id, {})
            updated_at = record.get('updated_at', '未知')
            print(f"      ⏭️ 已处理过 (更新于: {updated_at})，跳过")
            self.stats["skipped"] += 1
            return True
        
        # ⭐ 从已有模板提取描述（不查询包源）
        existing_desc = self.extract_existing_description(template)
        if not existing_desc:
            print(f"      ⚠️ 无可用描述，跳过")
            return False
        
        print(f"      📄 已有描述: {len(existing_desc)} 字符")
        
        # ⭐ 构建虚拟的 package_info（基于已有描述）
        package_info = {
            "package_name": source_id,
            "type": "mcp",
            "info": {
                "name": current_name,
                "summary": existing_desc[:200],
                "description": existing_desc,
                "readme": existing_desc
            }
        }
        
        # 构建分类列表文本
        category_text = "可选的分类列表：\n"
        for cat_id, cat_name in category_map.items():
            category_text += f"- ID: {cat_id}, 名称: {cat_name}\n"
        
        # 调用 AI 生成新的信息
        print(f"      🤖 调用 AI 生成...")
        try:
            ai_result = self.ai_generator.generate_template_info(
                package_info,
                "mcp",  # 使用 mcp 类型
                category_text
            )
        except Exception as e:
            print(f"      ❌ AI 生成失败: {e}")
            return False
        
        # 获取 AI 生成的分类
        new_category_id = ai_result.get('category_id', '')
        
        # 验证分类
        if str(new_category_id) in category_map:
            category_name = category_map[str(new_category_id)]
            print(f"      ✅ AI 选择分类: {category_name} (ID: {new_category_id})")
        else:
            print(f"      ⚠️ AI 分类无效: {new_category_id}，保持原分类")
            new_category_id = template.get('template_category_id', '')
        
        # 获取 AI 生成的名称
        new_name = ai_result.get('name', ai_result.get('name_zh_cn', current_name))
        new_name_tw = ai_result.get('name_tw', ai_result.get('name_zh_tw', new_name))
        new_name_en = ai_result.get('name_en', source_id)
        print(f"      📛 新名称: {new_name}")
        
        # 获取 AI 生成的简介
        new_summary = ai_result.get('summary', ai_result.get('summary_zh_cn', ''))
        new_summary_tw = ai_result.get('summary_tw', ai_result.get('summary_zh_tw', ''))
        new_summary_en = ai_result.get('summary_en', '')
        print(f"      📝 新简介: {new_summary[:60]}...")
        
        # 获取 AI 生成的描述
        new_desc = ai_result.get('description', ai_result.get('description_zh_cn', ''))
        new_desc_tw = ai_result.get('description_tw', ai_result.get('description_zh_tw', ''))
        new_desc_en = ai_result.get('description_en', '')
        if new_desc:
            print(f"      📄 新描述: {len(new_desc)} 字符")
        
        # ⭐ 获取 Logo URL（AITemplateGenerator 内部已经生成并上传到 EMCP）
        new_logo_url = None
        if regenerate_logo:
            # 直接使用 AI 生成结果中的 logo_url（已经是 EMCP 路径）
            ai_logo_url = ai_result.get('logo_url', '')
            if ai_logo_url and ai_logo_url.startswith('/api/'):
                # 正确的 EMCP 路径格式
                new_logo_url = ai_logo_url
                print(f"      ✅ Logo URL: {new_logo_url}")
                self.stats["logo_generated"] += 1
            elif ai_logo_url and not ai_logo_url.startswith('http'):
                # 其他本地路径格式也接受
                new_logo_url = ai_logo_url
                print(f"      ✅ Logo URL: {new_logo_url}")
                self.stats["logo_generated"] += 1
            else:
                # 如果是外部 URL 或默认 Logo，不使用
                print(f"      ⚠️ Logo 生成失败或返回外部 URL，保留原 Logo")
        
        if dry_run:
            print(f"      🔸 [DRY RUN] 跳过实际更新")
            return True
        
        # 构建更新数据
        update_data = {
            "template_id": template_id,
            "template_category_id": str(new_category_id),
            "name": self.emcp_manager.make_multi_lang(
                new_name,
                new_name_tw,
                new_name_en
            ),
            "summary": self.emcp_manager.make_multi_lang(
                new_summary,
                new_summary_tw,
                new_summary_en
            ),
            "template_source_id": source_id,
            "command": template.get('command', ''),
            "route_prefix": template.get('route_prefix', ''),
            "package_type": template.get('package_type', 1),
            "args": template.get('args', []),
            # ⭐ API 需要的额外字段（空值即可）
            "server_image": template.get('server_image', ''),
            "container_port": template.get('container_port', ''),
            "TargetSseServerHost": template.get('TargetSseServerHost', ''),
        }
        
        # 更新描述
        if new_desc and len(new_desc) > 50:
            update_data["description"] = self.emcp_manager.make_multi_lang(
                new_desc,
                new_desc_tw,
                new_desc_en
            )
        else:
            update_data["description"] = template.get('description', [])
        
        # 更新 Logo
        if new_logo_url:
            update_data["logo_url"] = new_logo_url
        else:
            update_data["logo_url"] = template.get('logo_url', '')
        
        # ⭐ 执行更新 - 直接使用 update_mcp_template（已存在的模板）
        try:
            result = self.emcp_manager.update_mcp_template(
                template_id=template_id,
                template_data=update_data
            )
            print(f"      ✅ 更新成功!")
            
            # ⭐ 记录已处理
            self._save_processed_record(template_id, source_id)
            
            # ⭐ 统计成功更新数
            self.stats["updated"] += 1
            
            return True
        except Exception as e:
            print(f"      ❌ 更新失败: {e}")
            return False
    
    def run(self, dry_run: bool = False, limit: int = None, regenerate_logo: bool = True, force: bool = False):
        """运行批量更新"""
        print("\n" + "="*60)
        print("🚀 EMCP 模板批量更新工具")
        print("="*60)
        
        if dry_run:
            print("⚠️  DRY RUN 模式：只预览，不实际更新")
        if force:
            print("⚠️  FORCE 模式：强制重新更新所有模板")
        
        print(f"\n📋 更新内容（不查询包源，使用已有描述）:")
        print(f"   ✅ 分类 (根据已有描述智能选择)")
        print(f"   ✅ 名称 (AI 生成)")
        print(f"   ✅ 简介 (简洁版，20-50字)")
        print(f"   ✅ 描述 (完整版，Markdown 格式)")
        print(f"   {'✅' if regenerate_logo else '❌'} Logo (即梦 AI 生成)")
        print(f"   📋 已处理记录: {len(self.processed_templates)} 条")
        
        # 1. 登录
        if not self.login_emcp():
            return
        
        # 2. 初始化 AI
        if not self.init_ai_generator():
            return
        
        # 3. 初始化即梦 Logo 生成器
        if regenerate_logo:
            self.init_jimeng_client()
        
        # 4. 获取分类列表
        print("\n📋 获取分类列表...")
        category_map = {}
        try:
            categories = self.emcp_manager.get_all_template_categories()
            print(f"   ✅ 获取到 {len(categories)} 个分类")
            for cat in categories:
                cat_id = (cat.get('templateCategoryId') or 
                         cat.get('template_category_id') or 
                         cat.get('id'))
                cat_name = self.extract_text(cat.get('name', []))
                if cat_id:
                    category_map[str(cat_id)] = cat_name
                    print(f"      - {cat_id}: {cat_name}")
        except Exception as e:
            print(f"   ❌ 获取分类失败: {e}")
            return
        
        # 5. 获取所有模板
        all_templates = self.get_all_my_templates()
        if not all_templates:
            print("❌ 没有找到任何模板")
            return
        
        # ⭐ 过滤：只处理旧的 MCP 项目（名字带巴赫/MCP Server，或命令带bach）
        templates = []
        print(f"\n🔍 过滤旧 MCP 项目...")
        for tpl in all_templates:
            name = self.extract_text(tpl.get('name', []))
            command = tpl.get('command', '')
            source_id = tpl.get('template_source_id', '')
            
            # 判断是否是旧项目
            is_old_project = (
                '巴赫' in name or
                'MCP Server' in name or
                'MCP 服务' in name or
                'bach' in command.lower() or
                'bach' in source_id.lower()
            )
            
            if is_old_project:
                templates.append(tpl)
                print(f"   ✅ {source_id} ({name[:20]}...)")
        
        print(f"\n✅ 找到 {len(templates)} 个旧 MCP 项目（共 {len(all_templates)} 个模板）")
        
        if not templates:
            print("❌ 没有找到需要更新的旧 MCP 项目")
            return
        
        self.stats["total"] = len(templates)
        
        # 6. 应用限制
        if limit and limit > 0:
            templates = templates[:limit]
            print(f"\n⚠️  限制处理前 {limit} 个模板")
        
        # 7. 逐个更新
        print("\n" + "="*60)
        print(f"📝 开始更新 {len(templates)} 个模板")
        print("="*60)
        
        for i, template in enumerate(templates, 1):
            print(f"\n[{i}/{len(templates)}] ", end="")
            
            template_id = template.get('template_id', '')
            was_processed_before = self.is_already_processed(template_id)
            
            try:
                success = self.update_single_template(
                    template, categories, category_map, dry_run, regenerate_logo, force
                )
                # ⭐ stats 已在 update_single_template 中统计
                if not success:
                    self.stats["failed"] += 1
            except Exception as e:
                print(f"      ❌ 异常: {e}")
                import traceback
                traceback.print_exc()
                self.stats["failed"] += 1
            
            # 避免请求过快（跳过的不需要等待）
            if not dry_run and not was_processed_before:
                time.sleep(3)  # Logo 生成需要更多时间
        
        # 8. 打印统计
        print("\n" + "="*60)
        print("📊 更新统计")
        print("="*60)
        print(f"   总数: {self.stats['total']}")
        print(f"   成功: {self.stats['updated']}")
        print(f"   失败: {self.stats['failed']}")
        print(f"   跳过: {self.stats['skipped']}")
        if regenerate_logo:
            print(f"   Logo 生成: {self.stats['logo_generated']}")
        print("="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量更新 EMCP 模板')
    parser.add_argument('--dry-run', action='store_true', help='只预览，不实际更新')
    parser.add_argument('--limit', type=int, default=None, help='限制处理数量')
    parser.add_argument('--no-logo', action='store_true', help='不重新生成 Logo')
    parser.add_argument('--force', action='store_true', help='强制重新更新已处理过的模板')
    parser.add_argument('--clear-history', action='store_true', help='清除处理历史记录')
    
    args = parser.parse_args()
    
    # 清除历史记录
    if args.clear_history:
        if PROCESSED_FILE.exists():
            PROCESSED_FILE.unlink()
            print(f"✅ 已清除处理历史记录: {PROCESSED_FILE}")
        else:
            print(f"ℹ️ 无历史记录需要清除")
        return
    
    updater = BatchEMCPUpdater()
    updater.run(
        dry_run=args.dry_run, 
        limit=args.limit,
        regenerate_logo=not args.no_logo,
        force=args.force
    )


if __name__ == '__main__':
    main()



