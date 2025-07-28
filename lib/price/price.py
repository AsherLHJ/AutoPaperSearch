from datetime import datetime, timedelta
from ..config import config_loader as config

def is_discount_period(check_time=None):
    """判断给定时间是否在优惠时段（北京时间 00:30-08:30）"""
    if check_time is None:
        check_time = datetime.now()
    current_time = check_time.time()
    
    # 优惠时段：00:30-08:30
    start_time = datetime.strptime("00:30", "%H:%M").time()
    end_time = datetime.strptime("08:30", "%H:%M").time()
    
    return start_time <= current_time <= end_time

def calculate_weighted_price(remaining_seconds, tokens_per_second, prompt_ratio=0.8, 
                           cache_miss_ratio=1.0, model_name=None):
    """
    计算考虑跨时段的加权平均价格
    
    参数:
        remaining_seconds: 预计剩余秒数
        tokens_per_second: 每秒处理的token数
        prompt_ratio: 输入token占总token的比例（默认0.8）
        cache_miss_ratio: 缓存未命中的比例（默认1.0，即全部未命中）
        model_name: 模型名称
    
    返回:
        预估的总价格（元）
    """
    if model_name is None:
        model_name = config.model_name
    
    # 获取当前时间
    now = datetime.now()
    
    # 计算时段分布
    time_segments = []
    current_time = now
    remaining = remaining_seconds
    
    while remaining > 0:
        # 判断当前时段
        is_discount = is_discount_period(current_time)
        
        # 计算到下一个时段切换点的秒数
        current_hour_min = current_time.time()
        if is_discount:
            # 在优惠时段，计算到08:30的秒数
            end_time = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
            if current_time >= end_time:
                # 如果已经过了08:30，则下一个切换点是明天的00:30
                end_time = (current_time + timedelta(days=1)).replace(hour=0, minute=30, second=0, microsecond=0)
        else:
            # 在标准时段，计算到00:30的秒数
            end_time = current_time.replace(hour=0, minute=30, second=0, microsecond=0)
            if current_time >= end_time:
                # 如果已经过了00:30，则下一个切换点是08:30
                end_time = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
                if current_time >= end_time:
                    # 如果也过了08:30，则是明天的00:30
                    end_time = (current_time + timedelta(days=1)).replace(hour=0, minute=30, second=0, microsecond=0)
        
        # 计算在当前时段的秒数
        seconds_to_switch = (end_time - current_time).total_seconds()
        seconds_in_period = min(remaining, seconds_to_switch)
        
        time_segments.append({
            'seconds': seconds_in_period,
            'is_discount': is_discount
        })
        
        # 更新剩余时间和当前时间
        remaining -= seconds_in_period
        current_time = end_time
    
    # 根据时段分布计算加权价格
    total_price = 0
    
    for segment in time_segments:
        # 计算该时段的token数
        segment_tokens = segment['seconds'] * tokens_per_second
        prompt_tokens = segment_tokens * prompt_ratio
        completion_tokens = segment_tokens * (1 - prompt_ratio)
        
        # 计算缓存命中和未命中
        cache_miss_tokens = prompt_tokens * cache_miss_ratio
        cache_hit_tokens = prompt_tokens * (1 - cache_miss_ratio)
        
        # 获取该时段的价格
        if model_name == 'deepseek-chat':
            prices = config.deepseek_chat_discount_prices if segment['is_discount'] else config.deepseek_chat_standard_prices
        elif model_name == 'deepseek-reasoner':
            prices = config.deepseek_reasoner_discount_prices if segment['is_discount'] else config.deepseek_reasoner_standard_prices
        else:
            prices = config.deepseek_chat_discount_prices if segment['is_discount'] else config.deepseek_chat_standard_prices
        
        # 计算该时段的价格
        segment_price = (
            (cache_hit_tokens / 1_000_000) * prices['input_cache_hit'] +
            (cache_miss_tokens / 1_000_000) * prices['input_cache_miss'] +
            (completion_tokens / 1_000_000) * prices['output']
        )
        
        total_price += segment_price
    
    return total_price

def calculate_token_price(prompt_tokens, completion_tokens, 
                         prompt_cache_hit_tokens=0, prompt_cache_miss_tokens=0,
                         model_name=None):
    """
    计算token使用价格
    
    参数:
        prompt_tokens: 输入token总数
        completion_tokens: 输出token数
        prompt_cache_hit_tokens: 缓存命中的输入token数
        prompt_cache_miss_tokens: 缓存未命中的输入token数
        model_name: 模型名称，默认使用config中的配置
    
    返回:
        总价格（元）
    """
    if model_name is None:
        model_name = config.model_name
    
    # 获取当前时段的价格
    is_discount = is_discount_period()
    
    # 如果没有提供缓存信息，则假设所有输入都是缓存未命中
    if prompt_cache_hit_tokens == 0 and prompt_cache_miss_tokens == 0:
        prompt_cache_miss_tokens = prompt_tokens
    
    # 根据模型和时段获取价格
    if model_name == 'deepseek-chat':
        if is_discount:
            prices = config.deepseek_chat_discount_prices
        else:
            prices = config.deepseek_chat_standard_prices
    elif model_name == 'deepseek-reasoner':
        if is_discount:
            prices = config.deepseek_reasoner_discount_prices
        else:
            prices = config.deepseek_reasoner_standard_prices
    else:
        # 默认使用deepseek-chat的价格
        if is_discount:
            prices = config.deepseek_chat_discount_prices
        else:
            prices = config.deepseek_chat_standard_prices
    
    # 计算价格（价格是每百万tokens的价格）
    input_cache_hit_price = (prompt_cache_hit_tokens / 1_000_000) * prices['input_cache_hit']
    input_cache_miss_price = (prompt_cache_miss_tokens / 1_000_000) * prices['input_cache_miss']
    output_price = (completion_tokens / 1_000_000) * prices['output']
    
    total_price = input_cache_hit_price + input_cache_miss_price + output_price
    
    return total_price

def format_price(price):
    """格式化价格显示"""
    if price < 0.01:
        return f"¥{price:.4f}"
    elif price < 1:
        return f"¥{price:.3f}"
    else:
        return f"¥{price:.2f}"
