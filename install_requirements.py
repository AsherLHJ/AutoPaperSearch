import subprocess
import sys
import os

def install_requirements():
    """一键安装所有必需的Python库"""
    print("=== 开始安装 SearchPaper 所需的依赖库 ===\n")
    
    # 需要安装的库列表
    required_packages = [
        'openai',  # 用于调用DeepSeek API
    ]
    
    # 升级pip
    print("正在升级pip...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        print("✓ pip升级成功\n")
    except Exception as e:
        print(f"✗ pip升级失败: {e}\n")
    
    # 安装每个包
    for package in required_packages:
        print(f"正在安装 {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} 安装成功\n")
        except Exception as e:
            print(f"✗ {package} 安装失败: {e}\n")
    
    print("=== 依赖库安装完成 ===\n")
    
    # 创建必要的文件夹
    print("正在创建必要的文件夹...")
    folders = ['Data', 'Result', 'Log', 'APIKey']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✓ 创建文件夹: {folder}")
        else:
            print(f"- 文件夹已存在: {folder}")
    
    print("\n=== 安装完成！===")
    print("\n下一步：")
    print("1. 在 APIKey 文件夹中创建 .txt 文件，每行添加一个API密钥")
    print("2. 在 Data 文件夹中放入要处理的 .bib 文件")
    print("3. 修改 config.json 中的研究问题和关键词（或通过程序界面修改）")
    print("4. 运行 python Main.py 开始处理论文")

if __name__ == "__main__":
    install_requirements()
    input("\n按回车键退出...")
