from bs4 import BeautifulSoup
import re, requests
from urllib.parse import urljoin
from lxml import etree
from .logger2 import logger

class SelectorXPathFinder():

	def __init__(self):

		self.selectors = []

	def traverse_and_calculate(self, element, soup):

		"""递归遍历元素并生成选择器"""
		
		first_time = True
		while 'html' not in self.selectors: #要改，改成判断是否能取到所有文章，不多不少
			id_ = element.get("id")
			class_ = element.get("class", [])
			tag_name = element.name
			
			if first_time:
				self.calculate_tag_selector(element)

			else:

				if id_ and self.valid_id(id_):
					self.calculate_id_selector(id_)
					break

				elif class_ and self.valid_class(class_):
					class_ = ".".join(self.valid_class(class_))
					self.calculate_class_selector(class_)
					if len(soup.select(f'.{class_}')) == 1:
						break

				else:
					self.calculate_tag_selector(element)

			first_time = False
			element = element.parent

	def calculate_id_selector(self, id_):

		"""生成 ID 选择器"""
		if ':' not in id_:
			self.selectors.append(f"#{id_}")

	def calculate_class_selector(self, class_name):

		"""生成类选择器"""
		if ':' not in class_name:
			self.selectors.append(f".{class_name}")

	def calculate_tag_selector(self, element):

		"""生成标签选择器"""
		self.selectors.append(element.name)

	def generate_selector_string(self):

		"""生成选择器字符串"""
		selector_string = " ".join(reversed(self.selectors))
		self.selectors.clear()
		return selector_string

	def calculate_selector(self, element, soup):

		"""计算选择器路径"""
		self.traverse_and_calculate(element, soup)
		return self.generate_selector_string()

	def valid_id(self, id_str):

		if any(char.isdigit() for char in id_str):
			return False

		return True

	def valid_class(self, classes_list):

		classes_list_new = classes_list
		for each in classes_list_new:
			if any(char.isdigit() for char in each):
				classes_list.remove(each)

		return classes_list

	def find_selector(self, text, keyword, href):

		soup = BeautifulSoup(text, 'html.parser')
		css_selector = f'*[href="{href}"]:-soup-contains("{keyword}")'
		element = soup.select(css_selector)[0]
		selector_str = self.calculate_selector(element, soup)

		return selector_str
	
	def test(self):

		url = 'https://f.sdnews.com.cn/ssgsxx/'
		response = requests.get(url)
		response.encoding = 'utf-8'
		soup = BeautifulSoup(response.text, 'html.parser')

		keyword = '济南国资三度转让赛克赛斯股权，交易价格无变化'
		href = '../ssgsxx/202407/t20240701_4406106.htm'
		css_selector = f'*[href="{href}"]:-soup-contains("{keyword}")'
		element = soup.select(css_selector)[0]

		selector_str = self.calculate_selector(element, soup)
		print(selector_str)


if __name__ == '__main__':

	selector_xpath_finder = SelectorXPathFinder()
	selector_xpath_finder.test()


	"""
	def if_enough(self, soup, url):

		selector_str = self.generate_selector_string()
		selected = soup.select(selector_str)
		hrefs_list = [each.get('href') for each in selected]
		if '' in hrefs_list:
			return False
		urls_list = [urljoin(url, each) for each in hrefs_list]
		print(urls_list)
	"""