import threading
import time
from datetime import datetime, timedelta
from ..process import data
from ..price import price
from ..config import config_loader as config

def print_and_log(message="", thread_id=None):
    """
    同时打印到控制台和日志文件（如果启用）
    """
    if thread_id is not None:
        message = f"[Thread-{thread_id}] {message}"
    
    with data.file_write_lock:
        print(message)
        if config.save_full_log and data.full_log_file:
            data.full_log_file.write(message + "\n")
            data.full_log_file.flush()  # 确保即时写入

def progress_monitor():
    """
    每秒输出一次进度信息的监控线程
    """
    while not data.progress_stop_event.is_set():
        time.sleep(1)  # 每秒更新一次
        
        with data.progress_lock:
            if data.processed_papers == 0:
                continue
                
            # 计算当前进度
            current_progress = (data.processed_papers / data.total_papers_to_process) * 100
            
            # 计算已运行时长
            elapsed_time = time.time() - data.start_time
            hours_elapsed = int(elapsed_time // 3600)
            minutes_elapsed = int((elapsed_time % 3600) // 60)
            seconds_elapsed = int(elapsed_time % 60)
            
            # 计算平均单篇文章耗时（基于最近10篇）
            if data.processing_times:
                avg_time_per_paper = sum(data.processing_times) / len(data.processing_times)
            else:
                avg_time_per_paper = elapsed_time / data.processed_papers
            
            # 计算实际的平均处理速度（考虑并发）
            # 实际平均速度 = 已处理文章数 / 已运行时间
            actual_papers_per_second = data.processed_papers / elapsed_time if elapsed_time > 0 else 0
            # 反推出考虑并发后的实际单篇耗时
            actual_time_per_paper = 1 / actual_papers_per_second if actual_papers_per_second > 0 else avg_time_per_paper
            
            # 计算预计剩余时间（考虑并行处理）
            remaining_papers = data.total_papers_to_process - data.processed_papers
            # 考虑并行处理的效率：剩余时间 = 剩余文章数 * 平均处理时间 / 活跃线程数
            if data.active_threads > 0:
                estimated_remaining_time = (remaining_papers * avg_time_per_paper) / data.active_threads
            else:
                # 如果没有活跃线程信息，使用实际的处理速率
                papers_per_second = data.processed_papers / elapsed_time if elapsed_time > 0 else 1
                estimated_remaining_time = remaining_papers / papers_per_second if papers_per_second > 0 else 0
            
            hours_remaining = int(estimated_remaining_time // 3600)
            minutes_remaining = int((estimated_remaining_time % 3600) // 60)
            seconds_remaining = int(estimated_remaining_time % 60)
            
            # 计算预计完成时间
            estimated_completion_time = datetime.now() + timedelta(seconds=estimated_remaining_time)
            formatted_completion_time = estimated_completion_time.strftime("%Y_%m_%d %H:%M:%S")
            
            # 计算Token相关信息
            current_total_tokens = data.token_used
            avg_tokens_per_paper = current_total_tokens / data.processed_papers if data.processed_papers > 0 else 0
            estimated_total_tokens = avg_tokens_per_paper * data.total_papers_to_process
            
            # 计算详细的Token使用情况
            avg_prompt_tokens = data.prompt_tokens_used / data.processed_papers if data.processed_papers > 0 else 0
            avg_completion_tokens = data.completion_tokens_used / data.processed_papers if data.processed_papers > 0 else 0
            
            # 计算价格
            # 单篇平均价格（基于已处理的实际数据）
            avg_price_per_paper = price.calculate_token_price(
                avg_prompt_tokens, 
                avg_completion_tokens,
                data.prompt_cache_hit_tokens_used / data.processed_papers if data.processed_papers > 0 else 0,
                data.prompt_cache_miss_tokens_used / data.processed_papers if data.processed_papers > 0 else 0
            )
            
            # 当前总价格（基于已使用的实际token）
            current_total_price = price.calculate_token_price(
                data.prompt_tokens_used,
                data.completion_tokens_used,
                data.prompt_cache_hit_tokens_used,
                data.prompt_cache_miss_tokens_used
            )
            
            # 预估总价格（考虑跨时段）
            if remaining_papers > 0 and estimated_remaining_time > 0:
                # 计算每秒处理的token数
                tokens_per_second = current_total_tokens / elapsed_time if elapsed_time > 0 else 0
                
                # 计算输入token比例和缓存未命中比例
                prompt_ratio = data.prompt_tokens_used / current_total_tokens if current_total_tokens > 0 else 0.8
                cache_miss_ratio = data.prompt_cache_miss_tokens_used / data.prompt_tokens_used if data.prompt_tokens_used > 0 else 1.0
                
                # 计算剩余部分的预估价格（考虑跨时段）
                remaining_price = price.calculate_weighted_price(
                    estimated_remaining_time,
                    tokens_per_second,
                    prompt_ratio,
                    cache_miss_ratio
                )
                
                estimated_total_price = current_total_price + remaining_price
            else:
                # 如果没有剩余，使用简单估算
                estimated_total_price = avg_price_per_paper * data.total_papers_to_process
            
            # 导入语言模块
            from language import language
            from ..config import config_loader as config
            lang = language.get_text(config.LANGUAGE)
            
            # 构建进度信息
            progress_message = f"""
==========
{lang['current_progress'].format(progress=current_progress, processed=data.processed_papers, total=data.total_papers_to_process)}
{lang['threads_used'].format(count=data.active_threads)}
-----
{lang['time_estimation']}
{lang['avg_time_per_paper'].format(time=actual_time_per_paper, threads=data.active_threads)}
{lang['elapsed_time'].format(hours=hours_elapsed, minutes=minutes_elapsed, seconds=seconds_elapsed)}
{lang['remaining_time'].format(hours=hours_remaining, minutes=minutes_remaining, seconds=seconds_remaining)}
{lang['completion_time'].format(time=formatted_completion_time)}
-----
{lang['token_usage']}
{lang['avg_tokens'].format(input=int(avg_prompt_tokens), output=int(avg_completion_tokens))}
{lang['total_tokens'].format(total=current_total_tokens, input=data.prompt_tokens_used, output=data.completion_tokens_used)}
{lang['estimated_total_tokens'].format(count=int(estimated_total_tokens))}
-----
{lang['price_estimation']}
{lang['cost_per_paper'].format(cost=price.format_price(avg_price_per_paper))}
{lang['consumed_cost'].format(cost=price.format_price(current_total_price))}
{lang['estimated_total_cost'].format(cost=price.format_price(estimated_total_price))}
++++++++++++++++++++
"""
            print_and_log(progress_message)

def reset_progress_tracking():
    """重置进度跟踪变量"""
    data.processed_papers = 0
    data.processing_times.clear()
    data.start_time = time.time()
    # 重置token统计
    data.token_used = 0
    data.prompt_tokens_used = 0
    data.completion_tokens_used = 0
    data.prompt_cache_hit_tokens_used = 0
    data.prompt_cache_miss_tokens_used = 0

def update_progress(single_elapsed_time):
    """更新进度信息"""
    with data.progress_lock:
        data.processed_papers += 1
        data.processing_times.append(single_elapsed_time)
