import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re


def filter_and_collect_links(base_url, max_depth=2):
    """
    获取页面及其子页面的所有链接，按给定规则过滤并聚合。
    """
    # 获取base_url的域名部分
    base_domain = urlparse(base_url).netloc

    # 用于存储过滤后的链接
    all_filtered_links = set()

    # 用于存储需要抓取的URL
    to_scrape = [base_url]
    visited = set()  # 用于避免重复请求同一个URL

    while to_scrape and max_depth > 0:
        current_url = to_scrape.pop(0)

        # 如果该URL已经访问过，则跳过
        if current_url in visited:
            continue
        visited.add(current_url)

        # 获取当前URL的所有链接
        links = get_links_from_page(current_url)

        for link in links:
            parsed_url = urlparse(link)
            # 确保链接属于同一个域名
            if base_domain in parsed_url.netloc:
                # 过滤掉带有查询参数、含有指定关键词的链接
                if (
                        'login' in parsed_url.path or 'auth' in parsed_url.path or 'detail' in parsed_url.path or 'item' in parsed_url.path):
                    continue
                if '?' in parsed_url.query or '&' in parsed_url.query:
                    continue
                if re.search(r'/login|/auth|/register|/signup|/details|/item', parsed_url.path):
                    continue
                # 过滤掉末尾为纯数字的链接
                if is_pure_number_uri(link):
                    continue
                # 标准化链接，去重相同内容的链接
                normalized_link = normalize_url(link)
                all_filtered_links.add(normalized_link)
                # 将新发现的链接加入待爬取队列
                to_scrape.append(link)

        # 限制深度，防止无限循环
        max_depth -= 1

    return list(all_filtered_links)


def normalize_url(url):
    """
    标准化 URL，确保使用统一的协议（https），去除www。
    不在末尾添加斜杠，仅用于去重时标准化。
    """
    parsed_url = urlparse(url)

    # 强制使用 https 协议
    netloc = parsed_url.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]  # 去除www
    normalized_url = parsed_url._replace(scheme="https", netloc=netloc).geturl()

    return normalized_url


def get_links_from_page(base_url):
    """
    获取单个页面的所有链接，并过滤掉不符合规则的链接。
    """
    # 发送GET请求获取网页内容
    response = requests.get(base_url)

    # 判断请求是否成功
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        return []

    # 解析网页内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 获取网页中所有的链接
    links = set()  # 使用集合去重
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        # 将相对URL转换为绝对URL
        full_url = urljoin(base_url, href)
        links.add(full_url)

    return links


def is_pure_number_uri(url):
    """
    判断 URL 的末尾是否为纯数字的路径。
    """
    # 提取 URL 路径的最后一部分
    path = urlparse(url).path
    last_part = path.split('/')[-1]
    # 检查最后部分是否为纯数字
    return last_part.isdigit()