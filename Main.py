from lib import ReadPaper
from lib.paper_processor import process_papers
from lib.load_api_keys import load_api_keys_from_files
from lib import utils
import config

if __name__ == "__main__":
    # 自动加载API密钥
    utils.print_and_log("正在加载API密钥...")
    load_api_keys_from_files()
    
    # 检查是否有可用的API密钥
    if not config.API_KEYS:
        utils.print_and_log("错误：没有可用的API密钥！")
        utils.print_and_log("请在APIKey文件夹中创建txt文件并添加API密钥。")
        exit(1)
    
    # 首先读取所有论文数据
    ReadPaper.read_bib_files()
    
    # 然后处理论文的相关性，传入要求参数
    process_papers(config.ResearchQuestion, config.Keywords, config.Requirements, -1)
