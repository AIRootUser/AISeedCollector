from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Comment
import re
import requests
import json
import sys
import time
from functools import wraps
from config.config import Config

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} 耗时: {end - start:.4f} 秒")
        return result
    return wrapper

@timeit
def getWebpageContent(url):
    config = Config()
    with sync_playwright() as p:
        # 启动浏览器（headless模式）
        browser = p.chromium.launch(headless=config.get_parser_config('headless'))
        page = browser.new_page()
        
        # 导航到目标URL并等待页面加载
        page.goto(url, wait_until=config.get_parser_config('wait_until'))
        
        # 获取页面HTML内容
        html_content = page.content()
        
        # 关闭浏览器
        browser.close()
    
    # 使用BeautifulSoup处理HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除不需要的元素（图片、视频等）
    for element in soup.find_all(['img', 'video', 'audio', 'iframe', 'svg', 'canvas', 'figure']):
        element.decompose()
    
    # 移除script和style标签
    for element in soup.find_all(['script', 'style']):
        element.decompose()
    
    # 移除注释
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    
    # 处理文本节点，压缩空白字符
    for element in soup.find_all(string=True):
        if element.parent.name not in ['pre', 'code']:  # 保留pre和code标签内的格式
            new_text = re.sub(r'\s+', ' ', element.string).strip()
            element.replace_with(new_text)
    
    # 返回处理后的HTML文本
    return str(soup)

@timeit
def ask_LLM(query):
    config = Config()
    data = {
        'messages': [{'role': 'user', 'content': query}],
        'model': config.get_llm_config('model')
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.get_llm_config("api_key")}'
    }
    url = config.get_llm_config('api_url')
    response = requests.post(url=url, headers=headers, data=json.dumps(data))

    result = response.content
    result = json.loads(result)['choices'][0]['message']['content']
    print("LLM原始返回结果:", result)

    return result

if __name__ == "__main__":
    url = input("请输入要抓取的网页URL: ")
    try:
        htmlresult = getWebpageContent(url)
        config = Config()
        prompt = config.get_prompt('column_analysis') + str(htmlresult)
        result = ask_LLM(prompt)
        print(result)

    except Exception as e:
        print(f"发生错误: {e}")