from openai import OpenAI
import time
from . import config_loader as config
import sys
from . import utils
import json

def check_paper_relevance(research_direction, keywords, requirements, paper_title, paper_abstract, api_key=None):    
    # 记录API调用开始时间
    api_start_time = time.time()
    
    # 从config导入系统提示词
    system_prompt = config.system_prompt
    
    # 构建user_prompt，根据配置决定是否包含关键词和要求
    user_prompt = f"""#研究主题#：{research_direction}
"""
    
    # 根据配置决定是否添加要求
    #if config.include_requirements_in_prompt and requirements:
    user_prompt += f"""#要求#：{requirements}

"""
    
    # 根据配置决定是否添加关键词
    #if config.include_keywords_in_prompt:
    user_prompt += f"""#关键词#：{keywords}

"""
    
    # 始终包含论文标题和摘要
    user_prompt += f"""#论文标题#：{paper_title}

#论文摘要#：{paper_abstract}
"""
    # 使用DeepSeek API进行模型调用
    # 如果没有传入api_key，报错并终止程序
    if api_key is None:
        utils.print_and_log("错误：未提供API密钥！")
        utils.print_and_log("请确保在调用 check_paper_relevance 函数时传入有效的 api_key 参数。")
        sys.exit(1)
        
    client = OpenAI(
        api_key=api_key, 
        base_url=config.api_base_url
        )
    
    response = client.chat.completions.create(
        model=config.model_name,
        messages=[
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            },
        ],
        stream=False,  # 不使用流式响应
        temperature=1.0,
        response_format={
            'type': 'json_object'
        }
    )
    
    # 提取结果并清理
    response_text = response.choices[0].message.content.strip()
    # print(f"  ********************** 模型返回内容: {response_text} **********************")

    # response_text变量只保留"</think>"之后的内容
    if '</think>' in response_text:
        # 找到 </think> 的位置并截取之后的内容
        think_end_index = response_text.find('</think>')
        response_text = response_text[think_end_index + len('</think>'):].strip()
    
    # 解析JSON结果
    result = ''
    reason = ''
    
    try:
        # 解析JSON响应
        json_response = json.loads(response_text)
        
        # 提取相关性判断结果
        if 'relevant' in json_response:
            result = json_response['relevant'].upper()
            if result not in ['Y', 'N']:
                utils.print_and_log(f"  警告：模型返回了意外的relevant值: {result}")
                result = 'N'
        else:
            utils.print_and_log(f"  警告：JSON响应中缺少relevant字段: {response_text}")
            result = 'N'
        
        # 提取原因
        if 'reason' in json_response:
            reason = json_response['reason']
            # 根据结果类型添加前缀
            if result == 'Y':
                reason = f"相关原因：{reason}"
            else:
                reason = f"不相关原因：{reason}"
        else:
            utils.print_and_log(f"  警告：JSON响应中缺少reason字段")
            
    except json.JSONDecodeError as e:
        utils.print_and_log(f"  警告：无法解析模型返回的JSON: {e}")
        utils.print_and_log(f"  原始响应: {response_text}")
        result = 'N'
        reason = "不相关原因：模型响应格式错误"
    
    # DeepSeek API返回的token信息
    tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    cache_hit_tokens = 0
    cache_miss_tokens = 0
    
    if hasattr(response, 'usage'):
        # 使用总token数（prompt_tokens + completion_tokens）
        tokens = response.usage.total_tokens
        prompt_tokens = response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0
        completion_tokens = response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0
        
        # 获取缓存信息（如果有）
        cache_hit_tokens = getattr(response.usage, 'prompt_cache_hit_tokens', 0)
        cache_miss_tokens = getattr(response.usage, 'prompt_cache_miss_tokens', 0)
    else:
        # 如果没有usage信息，使用估算值, 1 个英文字符 ≈ 0.3 个 token，1 个中文字符 ≈ 0.6 个 token
        utils.print_and_log("  警告：API响应中没有token使用信息，使用估算值")
        total_chars = len(system_prompt + user_prompt + response_text)
        tokens = int(total_chars * 0.6)  # 假设平均每个字符占0.6个token
        # 估算输入输出比例（假设输入占80%，输出占20%）
        prompt_tokens = int(tokens * 0.8)
        completion_tokens = tokens - prompt_tokens
        cache_miss_tokens = prompt_tokens  # 估算时假设全部未命中
    
    return result, tokens, reason, prompt_tokens, completion_tokens, cache_hit_tokens, cache_miss_tokens  # 返回相关原因