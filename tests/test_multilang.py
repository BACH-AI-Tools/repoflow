#!/usr/bin/env python3
"""测试多语言生成"""

from emcp_manager import EMCPManager
from chinese_converter import ChineseConverter


def test_multi_lang():
    """测试多语言数组生成"""
    
    emcp_mgr = EMCPManager()
    
    test_cases = [
        ("智能文件搜索服务器", "Intelligent File Search Server"),
        ("基于 Model Context Protocol 的文件搜索解决方案，高效支持文件名和内容检索。", 
         "A Model Context Protocol-based file search solution enabling efficient file name and content searches."),
        ("数据分析MCP服务器", "Data Analysis MCP Server"),
        ("网页解析", "Web Page Parsing"),
    ]
    
    print("=" * 80)
    print("多语言数组生成测试")
    print("=" * 80)
    print("\n期望格式:")
    print("  type 1: zh-cn (中文简体)")
    print("  type 2: zh-tw (中文繁体)")
    print("  type 3: en (英文)")
    print("=" * 80)
    
    for i, (zh_cn, en) in enumerate(test_cases, 1):
        print(f"\n测试 {i}:")
        print(f"  输入 (简体): {zh_cn}")
        print(f"  输入 (英文): {en}")
        
        result = emcp_mgr.make_multi_lang(zh_cn, en)
        
        print(f"\n  输出:")
        for item in result:
            type_name = {1: "简体", 2: "繁体", 3: "英文"}[item['type']]
            print(f"    type {item['type']} ({type_name}): {item['content'][:50]}...")
        
        # 验证
        assert len(result) == 3, "应该有3个语言版本"
        assert result[0]['type'] == 1, "第一个应该是简体"
        assert result[1]['type'] == 2, "第二个应该是繁体"
        assert result[2]['type'] == 3, "第三个应该是英文"
        
        # 检查内容
        assert result[0]['content'] == zh_cn, "简体内容应该一致"
        assert result[2]['content'] == en, "英文内容应该一致"
        
        # 检查繁体是否和简体不同（对于包含常用字的情况）
        zh_tw = result[1]['content']
        if any(char in zh_cn for char in ['个', '为', '务', '发', '网', '数', '据', '档', '检', '服']):
            assert zh_tw != zh_cn, f"繁体应该和简体不同: {zh_cn} vs {zh_tw}"
            print(f"  ✅ 繁体转换成功: {zh_tw[:50]}...")
        
        print(f"  ✅ 测试通过")
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


def test_converter_directly():
    """直接测试转换器"""
    
    print("\n" + "=" * 80)
    print("繁简转换器直接测试")
    print("=" * 80)
    
    converter = ChineseConverter()
    
    test_words = [
        "智能文件搜索服务器",
        "基于 Model Context Protocol 的文件搜索解决方案",
        "数据分析",
        "网络",
        "系统",
        "软件",
        "服务器",
        "检索",
        "获取",
        "处理",
    ]
    
    for word in test_words:
        traditional = converter.to_traditional(word)
        print(f"  简体: {word:30} → 繁体: {traditional}")
        
        # 如果包含应该被转换的字，检查是否真的转换了
        should_convert = any(char in word for char in converter.SIMPLIFIED_TO_TRADITIONAL.keys())
        if should_convert:
            assert traditional != word, f"应该转换但没有转换: {word}"


if __name__ == '__main__':
    test_converter_directly()
    test_multi_lang()

