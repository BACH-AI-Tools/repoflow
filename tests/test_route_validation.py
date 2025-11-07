#!/usr/bin/env python3
"""测试路由前缀验证规则"""

import re


def normalize_route_prefix(route_prefix: str) -> str:
    """
    规范化路由前缀
    
    规则：
    - 只能包含小写字母和数字
    - 不能以数字开头
    - 长度不超过10个字符
    """
    # 移除所有非字母数字字符
    route_prefix = re.sub(r'[^a-z0-9]', '', route_prefix.lower())
    
    # 如果以数字开头，添加字母前缀
    if route_prefix and route_prefix[0].isdigit():
        route_prefix = 'mcp' + route_prefix
    
    # 如果为空，使用默认值
    if not route_prefix:
        route_prefix = 'mcp'
    
    # 限制长度不超过10个字符
    if len(route_prefix) > 10:
        route_prefix = route_prefix[:10]
    
    return route_prefix


def validate_route_prefix(route_prefix: str) -> bool:
    """
    验证路由前缀是否符合规则
    
    Returns:
        True if valid, False otherwise
    """
    # 检查是否为空
    if not route_prefix:
        return False
    
    # 检查长度
    if len(route_prefix) > 10:
        return False
    
    # 检查是否只包含小写字母和数字
    if not re.match(r'^[a-z0-9]+$', route_prefix):
        return False
    
    # 检查是否以数字开头
    if route_prefix[0].isdigit():
        return False
    
    return True


def test_route_prefix():
    """测试路由前缀规范化"""
    
    test_cases = [
        # (输入, 预期输出, 是否有效)
        ('data-analysis', 'dataanalys', True),
        ('file-search', 'filesearch', True),
        ('web_parser', 'webparser', True),
        ('@bachstudio/mcp-file-search', 'bachstudio', True),
        ('123-test', 'mcp123test', True),  # 以数字开头，添加mcp前缀
        ('test-123', 'test123', True),
        ('UPPERCASE', 'uppercase', True),
        ('very-long-package-name-exceeds-limit', 'verylongpa', True),
        ('test!@#$%', 'test', True),
        ('', 'mcp', True),  # 空字符串，使用默认值
        ('mcp', 'mcp', True),
        ('a', 'a', True),
        ('1', 'mcp1', True),
        ('abc123def456', 'abc123def4', True),  # 超长截断
    ]
    
    print("=" * 70)
    print("路由前缀规范化测试")
    print("=" * 70)
    print("\n规则：")
    print("  1. 只能包含小写字母(a-z)和数字(0-9)")
    print("  2. 不能以数字开头")
    print("  3. 长度不超过10个字符")
    print("=" * 70)
    
    all_passed = True
    
    for i, (input_val, expected, should_be_valid) in enumerate(test_cases, 1):
        result = normalize_route_prefix(input_val)
        is_valid = validate_route_prefix(result)
        passed = (result == expected and is_valid == should_be_valid)
        all_passed = all_passed and passed
        
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"\n测试 {i}:")
        print(f"  输入: '{input_val}'")
        print(f"  输出: '{result}'")
        print(f"  预期: '{expected}'")
        print(f"  长度: {len(result)} 字符")
        print(f"  有效: {is_valid}")
        
        # 详细验证
        checks = []
        if result:
            checks.append(f"✓ 非空" if result else "✗ 空")
            checks.append(f"✓ 长度≤10" if len(result) <= 10 else f"✗ 长度={len(result)}")
            checks.append(f"✓ 仅字母数字" if re.match(r'^[a-z0-9]+$', result) else "✗ 包含非法字符")
            checks.append(f"✓ 非数字开头" if not result[0].isdigit() else "✗ 数字开头")
        
        print(f"  检查: {', '.join(checks)}")
        print(f"  状态: {status}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 有测试失败！")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    success = test_route_prefix()
    exit(0 if success else 1)

