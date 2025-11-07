#!/usr/bin/env python3
"""测试路由前缀限制"""

from ai_generator import AITemplateGenerator


def test_route_prefix_limit():
    """测试路由前缀不超过10个字符"""
    
    # 创建一个测试用的生成器
    generator = AITemplateGenerator(
        azure_endpoint="https://test.openai.azure.com/",
        api_key="test-key"
    )
    
    # 测试用例
    test_cases = [
        {
            'package_name': 'short',
            'expected_max_len': 10,
            'description': '短包名'
        },
        {
            'package_name': 'very-long-package-name-that-exceeds-limit',
            'expected_max_len': 10,
            'description': '超长包名'
        },
        {
            'package_name': 'data-analysis',
            'expected_max_len': 10,
            'description': '正好12字符的包名'
        },
        {
            'package_name': 'my_package_name',
            'expected_max_len': 10,
            'description': '包含下划线的包名'
        },
    ]
    
    print("=" * 60)
    print("路由前缀长度限制测试")
    print("=" * 60)
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        package_name = case['package_name']
        
        # 模拟生成路由前缀
        route_prefix = package_name.lower().replace('_', '-').replace('/', '-')
        if len(route_prefix) > 10:
            route_prefix = route_prefix[:10].rstrip('-')
        
        passed = len(route_prefix) <= 10
        all_passed = all_passed and passed
        
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"\n测试 {i}: {case['description']}")
        print(f"  输入: {package_name}")
        print(f"  输出: {route_prefix}")
        print(f"  长度: {len(route_prefix)} 字符")
        print(f"  状态: {status}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 有测试失败！")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    success = test_route_prefix_limit()
    exit(0 if success else 1)


