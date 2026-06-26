import sys
import os

print("测试 KamaClaude 命令...")

# 检查是否可以导入
try:
    import kamaclaude
    print("✓ kamaclaude 模块导入成功")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 检查 main.py 是否存在
main_file = os.path.join(os.path.dirname(kamaclaude.__file__), "main.py")
if os.path.exists(main_file):
    print(f"✓ {main_file} 存在")
else:
    print(f"✗ {main_file} 不存在")

print("\n现在可以在终端中运行:")
print("  kamaclaude")
print("或者:")
print("  kama")
