# -*- coding:utf-8 -*-

import json, re
from logger2 import logger
from jsonpath_ng import jsonpath, parse
from urllib.parse import urlparse
from urllib.parse import parse_qs
from urllib.parse import urljoin

class JsonPathFinder():

	def __init__(self):

		pass

	def find_titlepath(self, some_json, some_str):

		json_path = '$'

		if not some_str in json.dumps(some_json, ensure_ascii=False):
			return None
		
		else:
			while True:

				if type(some_json) == dict:
					keys_list = some_json.keys()

					for some_key in keys_list:
						if some_str == some_json.get(some_key): #找到标题字段
							json_path += '.' + some_key
							return json_path

					for some_key in keys_list:
						some_value = json.dumps(some_json.get(some_key), ensure_ascii=False)
						if some_str in some_value: #找到包含标题的字段
							json_path += '.' + some_key
							some_json = json.loads(some_value)
							break
					
				elif type(some_json) == list:
					keys_list = some_json
					for some_key in keys_list:
						some_value = json.dumps(some_key, ensure_ascii=False)
						if some_str in some_value:
							json_path += '[{}]'.format(keys_list.index(some_key))
							some_json = json.loads(some_value)
							break

				else:
					return json_path

	def find_iterable_and_titlepath(self, target_titlepath, other_titlepaths):

		target_titlepath_pattern = re.sub(r'\[\d+\]', '', target_titlepath)
		other_titlepaths_new = []
		for each in other_titlepaths:
			if re.sub(r'\[\d+\]', '', each) == target_titlepath_pattern: #找到跟target_title的json路径相等的所有title
				other_titlepaths_new.append(each)

		index_number = len(re.findall(r'\[\d+\]', target_titlepath))
		for i in range(index_number, 0, -1):
			target_titleptah_part = re.findall('.*?\[\d+\]'*i, target_titlepath)[0]
			target_titleptah_part_a = re.match('(.*)\[\d+\]', target_titleptah_part).group(1)
			target_titleptah_part_b = re.match('.*?\[\d+\]'*i+'(.*)', target_titlepath).group(1)

			other_titlepaths = []
			for another_titlepath in other_titlepaths_new:
				another_titlepath_part = re.findall('.*?\[\d+\]'*i, another_titlepath)[0]
				another_titlepath_part_a = re.match('(.*)\[\d+\]', another_titlepath_part).group(1)
				another_titlepath_part_b = re.match('.*?\[\d+\]'*i+'(.*)', another_titlepath).group(1)
				if another_titlepath_part_a == target_titleptah_part_a and another_titlepath_part_b == target_titleptah_part_b:
					other_titlepaths.append(another_titlepath)

			if other_titlepaths:
				return {'iterablepath': target_titleptah_part_a, 'titlepath': '$'+target_titleptah_part_b}

	def find_valid_titles_hrefs_data(self, iterablepath, titlepath, data, monitor_result):

		#根据上面找到的json路径与target_title相等的所有title，找出对应的href（此是渲染出来的href），以及data_list

		valid_titles_hrefs = []
		jsonpath_expr = parse(iterablepath)
		data_list = jsonpath_expr.find(data)[0].value
		jsonpath_expr = parse(titlepath)

		data_list_new = []
		element_dicts_list = monitor_result.get('element_dicts_list')
		element_dicts_list.append({'text': monitor_result.get('keyword'), 'href': monitor_result.get('href')})
		for a in data_list:
			title = jsonpath_expr.find(a)[0].value
			for b in element_dicts_list:
				#if b.get('text') in title:
				if b.get('text') == title:
					valid_titles_hrefs.append({'title': b.get('text'), 'href': b.get('href')})
					data_list_new.append(a) #保证data_list_new 和 valid_titles_hrefs 包含的都是同样的文章
					break

		#valid_titles_hrefs.append({'title': monitor_result.get('keyword'), 'href': monitor_result.get('href')})
		return {'valid_titles_hrefs': valid_titles_hrefs, 'data_list': data_list_new}

	def get_all_leaf_values(self, json_obj, parent_key=None):
		"""
		递归函数，用于从 JSON 对象中获取所有最底层的键值对的值和键名。
		如果遇到列表，判断列表中的元素是否是字典或列表：
		- 如果是字典或列表，则继续递归。
		- 如果不是，则直接跳过。
		:param json_obj: JSON 对象（可以是字典或列表）
		:param parent_key: 父级键名（用于嵌套结构）
		:return: 包含所有最底层键值对的列表，格式为 [{"key": key, "value": value}]
		"""
		leaf_values = []

		if isinstance(json_obj, dict):
			# 如果是字典，递归遍历每个键值对
			for key, value in json_obj.items():
				if isinstance(value, (dict, list)):
					# 如果值是字典或列表，递归处理
					leaf_values.extend(self.get_all_leaf_values(value, parent_key=key))
				else:
					# 如果值不是字典或列表，说明是叶子节点，直接添加到结果列表中
					if value:
						leaf_values.append({"key": key, "value": str(value)})
		elif isinstance(json_obj, list):
			# 如果是列表，判断列表中的每个元素
			for item in json_obj:
				if isinstance(item, (dict, list)):
					# 如果元素是字典或列表，递归处理
					leaf_values.extend(self.get_all_leaf_values(item, parent_key=parent_key))
				# 如果元素不是字典或列表，直接跳过
		return leaf_values


		
		# 根据标记结果过滤列表
		result = [item for i, item in enumerate(input_list) if keep[i]]
		return result

	def remove_substring_dicts(self, input_list):
		"""
		从列表中移除那些字典的 'value' 值是其他字典 'value' 值的子字符串的字典。
		:param input_list: 输入的字典列表，每个字典都是 {"key": key, "value": value}，且 key 和 value 都是字符串
		:return: 处理后的列表
		"""
		# 创建一个标记列表，用于记录每个字典是否需要保留
		keep = [True] * len(input_list)
		
		# 遍历列表中的每个字典
		for i, dict_i in enumerate(input_list):
			value_i = dict_i["value"]  # 获取当前字典的 'value'
			for j, dict_j in enumerate(input_list):
				if i != j:
					value_j = dict_j["value"]  # 获取其他字典的 'value'
					if value_i in value_j and value_i != value_j:
						# 如果当前字典的 'value' 是其他字典 'value' 的子字符串，则标记为不保留
						keep[i] = False
						break
		
		# 根据标记结果过滤列表
		result = [item for i, item in enumerate(input_list) if keep[i]]
		return result

	def remove_duplicate_values(self, input_list):

		# 从列表中移除具有相同 'value' 的重复字典，只保留一个
		"""
		从列表中移除具有相同 'value' 的重复字典，只保留一个。
		:param input_list: 输入的字典列表，每个字典的形式为 {'key': some_key, 'value': some_value}
		:return: 处理后的列表
		"""

		seen_values = set()  # 用于记录已经见过的 'value'
		output_list = []  # 用于存储结果的列表

		for item in input_list:
			value = item.get('value')
			if value not in seen_values:
				seen_values.add(value)
				output_list.append(item)

		return output_list
	
	def parse_url(url):
		"""
		详细解析一个复杂的 URL，返回其所有组成部分。
		:param url: 要解析的 URL 字符串
		:return: 解析结果的字典
		"""
		# 使用 urlparse 解析 URL
		parsed_url = urlparse(url)
		
		# 解析查询字符串为字典
		query_params = parse_qs(parsed_url.query)
		
		# 将解析结果整理为字典
		url_parsed = {
			"scheme": parsed_url.scheme,  # 协议部分
			"netloc": parsed_url.netloc,  # 网络位置部分
			"path": parsed_url.path,      # 路径部分, 这个拆分后每层有用
			"params": parsed_url.params,  # 路径参数部分，这个解析后value有用
			"query": query_params,        # 查询字符串部分，解析为字典，这个解析后value有用
			"fragment": parsed_url.fragment  # 锚点部分
		}
		
		return url_parsed

	def find_hrefpath(self, data_list, titles_hrefs, titlepath, this_url):
		
		hrefpaths_list = []
		jsonpath_expr = parse(titlepath)

		a_href = titles_hrefs[0].get('href')
		a_title = titles_hrefs[0].get('title')
		possible_elements = []
		data = None

		for b in data_list:
			b_title = jsonpath_expr.find(b)[0].value
			if b_title == a_title: #b title是接口中的title，a title是渲染出的title
				data = b
				b_flattened = self.get_all_leaf_values(b)
				for c in b_flattened:
					#if c.get('value') in a_href:#是否改成 if c.get('value') in urljoin(this_url, a_href)更好？
					if c.get('value') in urljoin(this_url, a_href):
						possible_elements.append(c)
				break
			
		possible_elements_new = self.remove_substring_dicts(possible_elements)
		possible_elements = self.remove_duplicate_values(possible_elements_new)

		if len(possible_elements) == 1:
			element_value = possible_elements[0].get('value')
			full_href = urljoin(this_url, a_href)

			if a_href == element_value: #完全对的上的
				href_info = {'url_pattern': 'url', 'hrefpath': self.find_titlepath(data, element_value)}
				return href_info

			elif urljoin(full_href, element_value) == full_href: #/abc/def.html的这种
				url_pattern = re.match('(.*)'+element_value, full_href).group(1)
				url_pattern += 'url'
				href_info = {'url_pattern': url_pattern, 'hrefpath': self.find_titlepath(data, element_value)}
				return href_info

			else:
				#如果value在urlparse后的成份内，则替换
				href_info = {'url_pattern': full_href.replace(element_value, 'url'), 'hrefpath': self.find_titlepath(data, element_value)}
				return href_info

		if len(possible_elements_new) > 1:
			pass

	def find_jsonpath(self, data, monitor_result, this_url):

		target_titlepath = self.find_titlepath(data, monitor_result.get('keyword'))
		other_titlepaths = [self.find_titlepath(data, text) for text in [element.get('text') for element in monitor_result.get('element_dicts_list')] if self.find_titlepath(data, text)]

		iterable_and_titlepath = self.find_iterable_and_titlepath(target_titlepath, other_titlepaths)
		iterablepath = iterable_and_titlepath.get('iterablepath')
		titlepath = iterable_and_titlepath.get('titlepath')

		
		titles_hrefs_data = self.find_valid_titles_hrefs_data(iterablepath, titlepath, data, monitor_result)
		titles_hrefs = titles_hrefs_data.get('valid_titles_hrefs')
		#logger.info(titles_hrefs)
		data_list = titles_hrefs_data.get('data_list')

		hrefpath = self.find_hrefpath(data_list, titles_hrefs, titlepath, this_url)

		return {'iterablepath': iterablepath, 'titlepath': titlepath, 'hrefpath': hrefpath.get('hrefpath'), 'url_pattern': hrefpath.get('url_pattern')}

	def test(self):

		titles_hrefs = [{"title": "【常务会议】聚力支点建设 提升城市能级", "href": "./show.html?aid=1&id=238266&depid=847"}, {"title": "【常务会议】以实干实绩奋力谱写中国式现代化宜昌篇章", "href": "./show.html?aid=1&id=237784&depid=847"}, {"title": "【常务会议】加快发展林业碳汇 助推生态优势转化","href": "./show.html?aid=1&id=1238524&depid=847"}]
		data_list = [{"n_id": {"aid":[{"article_id":"238524"}]}, "a":"1238524","title": {"atitle":[{"article_title":"【常务会议】加快发展林业碳汇 助推生态优势转化"}]}, "vc_number": "011100269/2025-00020", "vc_department": "宜昌市人民政府办公室", "m_cateid": "436", "vc_classes": "", "vc_inputtime": "2025-03-04", "createtime": "2025-03-04 08:04:12", "class_name": "林业", "fujian": ""}, {"n_id": {"aid":[{"article_id":"238266"}]}, "title": {"atitle":[{"article_title":"【常务会议】聚力支点建设 提升城市能级"}]}, "vc_number": "011100269/2025-00019", "vc_department": "宜昌市人民政府办公室", "m_cateid": "436", "vc_classes": "", "vc_inputtime": "2025-02-17", "createtime": "2025-02-17 08:36:28", "class_name": "经济建设", "fujian": ""}, {"n_id": {"aid":[{"article_id":"237784"}]}, "title": {"atitle":[{"article_title":"【常务会议】以实干实绩奋力谱写中国式现代化宜昌篇章"}]}, "vc_number": "011100269/2025-00014", "vc_department": "宜昌市人民政府办公室", "m_cateid": "436", "vc_classes": "", "vc_inputtime": "2025-01-27", "createtime": "2025-01-30 18:45:57", "class_name": "经济建设", "fujian": ""}]
		this_url = 'http://www.yichang.gov.cn/zfxxgk/list.html?depid=846&catid=436#page=1' 
		titlepath = '$.title.atitle[0].article_title'

		self.find_hrefpath(data_list, titles_hrefs, titlepath)		 

if __name__ == '__main__':

	json_path_finder = JsonPathFinder()
	json_path_finder.test()


#不用的代码

"""
	def find_hrefpath(self, data_list, titles_hrefs, titlepath, this_url):
		
		hrefpaths_list = []
		jsonpath_expr = parse(titlepath)

		for a in titles_hrefs:
			a_href = a.get('href')
			possible_elements = []
			data = None
			for b in data_list:

				b_title = jsonpath_expr.find(b)[0].value
				if b_title == a.get('title'): #b title是接口中的title，a title是渲染出的title
					data = b
					b_flattened = self.get_all_leaf_values(b)
					for c in b_flattened:
						if c.get('value') in a_href:#是否改成 if c.get('value') in urljoin(this_url, a_href)更好？
							possible_elements.append(c)
					break
			
			possible_elements_new = self.remove_substring_dicts(possible_elements)
			logger.info(possible_elements_new)
			#到这里出错，上证报出现了[{'key': 'url', 'value': '/article/detail/1595499.html'}, {'key': 'web_url', 'value': '/article/detail/1595499.html'}]这样的两个value相等的情况，要改，留下一个所有文章数据都有的，如果两个都是所有文章都有的，那么随便留下一个

			if len(possible_elements_new) == 1:
				element_value = possible_elements_new[0].get('value')

				full_href = urljoin(this_url, a_href)

				if a_href == element_value: 
					href_info = {'url_pattern': 'url', 'hrefpath': self.find_titlepath(data, element_value)}
					if not href_info in hrefpaths_list:
						hrefpaths_list.append(href_info)

				elif urljoin(full_href, element_value) == full_href:
					url_pattern = re.match('(.*)'+element_value, full_href).group(1)
					url_pattern += 'url'
					href_info = {'url_pattern': url_pattern, 'hrefpath': self.find_titlepath(data, element_value)}
					if not href_info in hrefpaths_list:
						hrefpaths_list.append(href_info)

				else:
					#如果value在urlparse后的成份内，则替换
					pass

			if len(possible_elements_new) > 1:

		if len(hrefpaths_list) == 1:
			return hrefpaths_list[0]
"""