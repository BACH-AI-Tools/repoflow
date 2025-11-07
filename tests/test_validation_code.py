#!/usr/bin/env python3
"""测试验证码生成"""

from datetime import datetime
from emcp_manager import EMCPManager


def test_validation_code():
    """测试验证码生成"""
    
    # 生成当天验证码
    code = EMCPManager.generate_validation_code()
    
    now = datetime.now()
    expected = now.strftime("%m%Y%d")
    
    print("=" * 70)
    print("验证码生成测试")
    print("=" * 70)
    print(f"\n当前日期: {now.strftime('%Y年%m月%d日')}")
    print(f"生成验证码: {code}")
    print(f"预期格式: MMyyyydd")
    print(f"预期结果: {expected}")
    
    # 验证格式
    if len(code) == 8:
        mm = code[0:2]
        yyyy = code[2:6]
        dd = code[6:8]
        
        print(f"\n解析结果:")
        print(f"  月份(MM): {mm}")
        print(f"  年份(yyyy): {yyyy}")
        print(f"  日期(dd): {dd}")
        
        print(f"\n格式验证:")
        print(f"  长度=8: {'✅' if len(code) == 8 else '❌'}")
        print(f"  月份正确: {'✅' if mm == now.strftime('%m') else '❌'}")
        print(f"  年份正确: {'✅' if yyyy == now.strftime('%Y') else '❌'}")
        print(f"  日期正确: {'✅' if dd == now.strftime('%d') else '❌'}")
        
        if code == expected:
            print(f"\n✅ 测试通过！")
            return True
        else:
            print(f"\n❌ 测试失败！")
            return False
    else:
        print(f"\n❌ 长度错误: {len(code)}")
        return False


if __name__ == '__main__':
    success = test_validation_code()
    
    print("\n" + "=" * 70)
    print("示例:")
    print("  2025年11月06日 → 11202506")
    print("  2025年12月25日 → 12202525")
    print("=" * 70)
    
    exit(0 if success else 1)

