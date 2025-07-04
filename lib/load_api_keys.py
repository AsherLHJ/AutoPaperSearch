import os
import config_loader as config
from . import utils

def load_api_keys_from_files():
    """
    从APIKey目录下读取所有txt文件中的API密钥，并更新config.API_KEYS
    每个txt文件中的API keys格式为每行一个key
    """
    # 使用config中定义的APIKEY_FOLDER路径
    api_key_folder = config.APIKEY_FOLDER
    
    # 清空现有的API_KEYS列表
    config.API_KEYS.clear()
    
    # 检查APIKey文件夹是否存在
    if not os.path.exists(api_key_folder):
        utils.print_and_log(f"警告：APIKey文件夹不存在: {api_key_folder}")
        utils.print_and_log("正在创建APIKey文件夹...")
        os.makedirs(api_key_folder)
        return
    
    # 统计读取的key数量
    total_keys_loaded = 0
    
    # 遍历APIKey文件夹中的所有txt文件
    txt_files = [f for f in os.listdir(api_key_folder) if f.endswith('.txt')]
    
    if not txt_files:
        utils.print_and_log(f"警告：APIKey文件夹中没有找到txt文件: {api_key_folder}")
        return
    
    for filename in txt_files:
        file_path = os.path.join(api_key_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # 读取文件中的每一行
                for line in file:
                    # 去除空白字符
                    key = line.strip()
                    # 只添加非空的key
                    if key and key.startswith('sk-'):
                        config.API_KEYS.append(key)
                        total_keys_loaded += 1
        except Exception as e:
            utils.print_and_log(f"读取文件 {filename} 时出错: {str(e)}")
    
    # 打印加载结果
    utils.print_and_log(f"成功从 {len(txt_files)} 个文件中加载了 {total_keys_loaded} 个API密钥")
    
    # 如果没有加载到任何key，给出警告
    if total_keys_loaded == 0:
        utils.print_and_log("警告：没有加载到任何有效的API密钥！")
        utils.print_and_log("请确保APIKey文件夹中的txt文件包含有效的API密钥（以'sk-'开头）")

def print_loaded_keys():
    """
    打印当前加载的API密钥数量（不显示具体内容）
    """
    if config.API_KEYS:
        utils.print_and_log(f"当前已加载 {len(config.API_KEYS)} 个API密钥")
    else:
        utils.print_and_log("当前没有加载任何API密钥")
