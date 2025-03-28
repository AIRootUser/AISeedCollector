import sys
import json
from siteParser.siteParser import filter_and_collect_links
from columnParser.columnParser import getWebpageContent as get_webpage_content, ask_LLM
from selectorParser.selectorxpathfinder import SelectorXPathFinder

def process_site(base_url, max_depth=2):
    print(f"\n开始处理网站: {base_url}")
    
    # 第一步：获取所有栏目URL
    print("\n1. 正在获取所有栏目URL...")
    column_urls = filter_and_collect_links(base_url, max_depth)
    print(f"找到 {len(column_urls)} 个栏目URL")
    
    # 存储最终结果
    results = []
    
    # 第二步：解析每个栏目的新闻标题
    print("\n2. 正在解析栏目内容...")
    finder = SelectorXPathFinder()
    
    for url in column_urls:
        try:
            print(f"\n处理栏目: {url}")
            html_content = get_webpage_content(url)
            
            # 构建提示词
            prompt = '''
你是一个专业的金融种子添加运营，负责按步骤执行以下事情：
1、阅读用户给过来的html，判断当前页面是否是列表页，是的话，判断是否是投资者相关的页面，标准是，作为一个投资者，是否会从这个页面中获得投资方面有价值的内容。结果可能是“非列表页”“非相关”“相关”中的一个
2、如果是相关的列表页，从其中提取出列表内的标题文本，否则为空文本；如果页面里多个列表，则返回最核心的那个列表的标题
3、找到相关的标题后，根据网页结构抽取出相关标题的css选择器，使得css选择器可以从网页中命中出符合的标题和url,如.mc_e1_list .mc_e1_li .mc_e1_lisbox
4、输出最后的结果，必须以严格的JSON格式返回，返回的JSON对象必须包含以下字段：
   - type: 字符串类型，值必须是"相关"、"非列表页"或"非相关"之一
   - title: 字符串数组类型，存放标题列表，如果不是相关列表页则为空数组
   - cssSelector: 字符串类型，存放CSS选择器，如果不是相关列表页则为空字符串

示例输出：
```json
{"type":"相关","title":["标题1","标题2","标题3"],"cssSelector":".news-list .item-title"}
```
或
```json
{"type":"非列表页","title":[],"cssSelector":""}
```
或
```json
{"type":"非相关","title":[],"cssSelector":""}
```

注意事项：
1.是否属于列表页，是否属于相关的列表页，是基于整个列表页去判断，而不是基于列表页内部的某一条来判断
2.判断投资者相关是比较广义上的，不完全是业绩播报之类的，涉及到招投标、舆情风控、新闻通知等页面，可能会暴露出一些信息，会与公司状况有关，所以这一类页面也都是要作为有价值的种子的，也属于相关。但单纯的比如产品列表页、公司内部制度建设等，不属于投资相关。核心还是看对于股票投资者是否可能会存在影响投资判断的内容。

要判断的网页html是：
''' + str(html_content)
            
            # 获取LLM分析结果
            llm_result = ask_LLM(prompt)
            try:
                # 提取JSON字符串
                json_str = llm_result
                if '```json' in llm_result:
                    json_str = llm_result.split('```json')[1].split('```')[0].strip()
                
                result_dict = json.loads(json_str)
                print(f"LLM分析结果: {result_dict}")
                # 如果是相关的列表页，获取选择器
                if result_dict['type'] == '相关' and result_dict['title']:
                    for title in result_dict['title']:
                        try:
                            selector = finder.find_selector(html_content, title, '')
                            result_dict['cssSelector'] = selector
                            break
                        except Exception as e:
                            print(f"获取选择器失败: {e}")
                            continue
                
                results.append({
                    'url': url,
                    'analysis': result_dict
                })
                
            except json.JSONDecodeError as e:
                print(f"解析JSON失败: {e}")
                continue
                
        except Exception as e:
            print(f"处理栏目失败: {e}")
            continue
    
    return results

def main():
    if len(sys.argv) < 2:
        print("请提供网站URL作为参数")
        sys.exit(1)
    
    base_url = sys.argv[1]
    results = process_site(base_url)
    
    # 输出结果
    print("\n3. 处理完成，输出结果:")
    for result in results:
        print(f"\nURL: {result['url']}")
        print(f"分析结果: {json.dumps(result['analysis'], ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()