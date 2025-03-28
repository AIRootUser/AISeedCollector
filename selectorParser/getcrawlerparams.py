# -*- coding:utf-8 -*-

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from logger2 import logger
import json,re,time, playwright
from jsonpathfinder import JsonPathFinder
from selectorxpathfinder import SelectorXPathFinder
from entrypathfinder import EntryPathFinder
import warnings

class GetCrawlerParams():

    def __init__(self):

        self.json_path_finder = JsonPathFinder()
        self.selector_xpath_finder = SelectorXPathFinder()
        self.entry_path_finder = EntryPathFinder()
        self.data_type_list = []

        self.url = ''
        self.keyword = ''

    #获取节点在其同级兄弟节点中的序号（从1开始）
    def get_sibling_index(self, node):
        
        siblings = list(node.parent.children)
        siblings_new = [each for each in siblings if '<' in str(each)]
        for index, sibling in enumerate(siblings_new, start=1):
            if sibling == node:
                return index

    #找到节点的绝对路径
    def get_full_css_selector(self, element):

        element_names_list = []

        first_time = True
        while element.name.lower() != 'html':

            #第一个节点名要带上:nth-child(n)，这是为了过滤同级噪音节点。
            if first_time:
                element_index = str(self.get_sibling_index(element))
                element_names_list.append(element.name.lower() + f':nth-child({element_index})')

            else:
                id_ = element.get("id")
                if id_ and self.selector_xpath_finder.valid_id(id_):
                    element_names_list.append(element.name.lower() + '#' + id_)
                    break

                else:
                    element_names_list.append(element.name.lower())
            element = element.parent
            first_time = False

        element_names_list.reverse()
        return '>'.join(element_names_list)

    #找到所有绝对路径相同的节点
    def find_nodes_with_same_path(self, html_content, keyword):
        
        soup = BeautifulSoup(html_content, 'html.parser')
        css_selector = f'*[href]:-soup-contains("{self.keyword}")'
        target_node = soup.select(css_selector)[0]
        target_selector = self.get_full_css_selector(target_node)
        matching_nodes = soup.select(target_selector)
        
        return matching_nodes

    #给监听到的内容分类
    def get_data_type(self, text):

        try:
            data = json.loads(text)
            data_type = type(data)
            if data_type in [dict, list]:
                return {'type': 'json', 'data': data} #是直接可解析的json
        except json.decoder.JSONDecodeError:
            pass

        try:
            text = re.match('.*?\((.*)\)', text).group(1)
            data = json.loads(text)
            data_type = type(data)
            if data_type in [dict, list]:
                return {'type': 'json', 'data': data} #是处理后可解析的json
        except json.decoder.JSONDecodeError:
            pass

        except AttributeError: #说明是html或者其他
            pass

        return {'type': 'html', 'data': text}

    #解析监听到的内容
    def on_response(self, response):

        warnings.filterwarnings("ignore", category=DeprecationWarning)

        try:

            text = response.text()
            if self.keyword in text:
                data_type = self.get_data_type(text)
                data_type['seed_url'] = response.url
                self.data_type_list.append(data_type)

            #如果text是unicode，需要先encode为中文
            text_2 = text.encode('utf-8').decode('unicode_escape')
            if self.keyword in text_2:
                data_type = self.get_data_type(text)
                data_type['seed_url'] = response.url
                self.data_type_list.append(data_type)

        except UnicodeDecodeError:
            pass
            #logger.info('UnicodeDecodeError')
        except playwright._impl._errors.Error as e:
            pass
            #if 'Response body is unavailable for redirect responses' in str(e):
            #    logger.info(f"Skipping response due to redirect: {response.url}")

    #开启监听
    def monitor(self):

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.on('response', self.on_response)
            page.goto(self.url)

            #此时的页面可能是渲染出来的，不一定是静态页面。
            #xpath = f"//*[@href and contains(text(), '{self.keyword}')]" #然而有的页面是没有href的，如https://www.baoding.gov.cn/baoding-out/
            xpath = f'//*[@href and contains(., "{self.keyword}")]'

            element = page.query_selector(xpath)
            while not element:
                time.sleep(1)
                element = page.query_selector(xpath)

            href = element.get_attribute('href')

            #这部分，获得渲染出来的与入参keyword路径相同的多对href和keyword，据此后续可以做很多事，例如返回多个种子从而抓得更全，例如对于jsonpath种子可以定位到各种id……
            monitor_result = {}
            element_dicts_list = []
            html_content = page.content()
            elements_list = self.find_nodes_with_same_path(html_content, self.keyword)
            for each in elements_list:
                each_text = each.get_text()
                each_href = each.get('href')

                #if each_href == href:
                if each_href == href and self.keyword in each_text: #需要self.keyword in each_text，否则http://www.egsea.com/news/recommend.html的滑动大图，each_text可能会是浅色的正文部分
                    monitor_result['href'] = each_href
                    monitor_result['keyword'] = each_text

                else:
                    element_dicts_list.append({'href': each_href, 'text': each_text})

                #if each_text != self.keyword and each_href != href:
                #    element_dicts_list.append({'href': each_href, 'text': each_text})

            #logger.info(element_dicts_list)
            #monitor_result = {'href': href, 'element_dicts_list': element_dicts_list}

            monitor_result['element_dicts_list'] = element_dicts_list
            return monitor_result
            #browser.close()

    def get_params(self, this_url, this_keyword):

        self.url = this_url
        self.keyword = this_keyword
        crawler_params_dicts_list = []

        monitor_result = self.monitor()
        #monitor_result['keyword'] = this_keyword
        #logger.info(monitor_result)
        instance_href = monitor_result.get('href')

        #如果标题所在的节点为href所在节点的子孙节点，则获得的instance_keywords_str会包含换行符，必须从中找到没有换行符的instance_keyword
        instance_keyword = None
        instance_keywords_str = monitor_result.get('keyword')
        instance_keywords_list = instance_keywords_str.split('\n')
        for each in instance_keywords_list:
            if this_keyword in each:
                instance_keyword = each
                break

        #element_dicts_list = monitor_result.get('element_dicts_list')

        for each in self.data_type_list:
            data = each.get('data')
            data_type = each.get('type')
            seed_url = each.get('seed_url')

            if data_type == 'json':

                jsonpath_dict = self.json_path_finder.find_jsonpath(data, monitor_result, this_url)
                crawler_params_dicts_list.append({'type': 'json', 'seed_url': seed_url, 'iterable_jsonpath': jsonpath_dict.get('iterablepath'), 'keyword_jsonpath': jsonpath_dict.get('titlepath'), 'href_jsonpath': jsonpath_dict.get('hrefpath'), 'url_pattern': jsonpath_dict.get('url_pattern')})

            elif data_type == 'html':
                try:
                    href_selector = self.selector_xpath_finder.find_selector(data, instance_keyword, instance_href)
                    crawler_params_dicts_list.append({'type': 'html', 'seed_url': seed_url, 'href_xpath': '', 'href_selector': href_selector})
                except IndexError:
                    pass

            if not crawler_params_dicts_list:
                entrypath_iterable = self.entry_path_finder.find_entrypath(data, instance_keyword, instance_href)
                crawler_params_dicts_list.append({'type': 'entrypath', 'seed_url': seed_url, 'entrypath_iterable': entrypath_iterable})

        self.data_type_list.clear()
        return crawler_params_dicts_list

    def test(self):

        test_data_list = [{'url': 'https://gov.sdnews.com.cn/qwfb/', 'keyword': '《关于进一步促进服务消费高质量发展的若干措施》'}, {'url': 'https://stock.hexun.com/7x24h/index.html', 'keyword': '北交所上市公司一诺威大宗交易折价'}, {'url': 'http://www.jjckb.cn/redianzhuizong.html', 'keyword': '谣言引发弘信电子股价大跌'}, {'url': 'https://f.sdnews.com.cn/ssgsxx/', 'keyword': '济南国资三度转让赛克赛斯股权，交易价格无变化'}, {'url': 'http://fgj.hangzhou.gov.cn/col/col1229265366/index.html', 'keyword': '杭州市住保房管局关于印发杭州市旧房装修、厨卫改造所用物品材料购置补贴实'}, {'url': 'https://www.nfra.gov.cn/cn/view/pages/index/index.html', 'keyword': '国家金融监督管理总局就《信访工作办法（征求意见稿）》公开征求意见'}, {'url': 'http://www.yichang.gov.cn/zfxxgk/list.html?depid=846&catid=436', 'keyword': '【常务会议】齐心协力抓发展 用心用情惠民生'}, {'url': 'https://www.stcn.com/article/list/kx.html', 'keyword': '浙江省交通集团技术研究总院登记成立 含AI业务'}, {'url': 'https://www.catl.com/news/', 'keyword': '全球能源循环计划启动'}, {'url': 'http://www.egsea.com/news/recommend.html', 'keyword': 'A股现首位越南籍高管'}, {'url': 'http://www.egsea.com/news/recommend.html', 'keyword': '“国家队”，出手！集体飙升'}]
        #test_data_list = [{'url': 'http://www.egsea.com/news/recommend.html', 'keyword': '“国家队”，出手！集体飙升'}]
        
        for test_data in test_data_list:
            crawler_params_dicts_list = self.get_params(test_data.get('url'), test_data.get('keyword'))
            logger.info(crawler_params_dicts_list)

if __name__ == '__main__':

    get_crawler_params = GetCrawlerParams()
    get_crawler_params.test()