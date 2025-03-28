import re, requests
from logger2 import logger


class EntryPathFinder():

	def __init__(self):

		pass

	def find_shortest_matches(self, data, keyword, href):

		pattern_1 = f"{re.escape(keyword)}.*?{re.escape(href)}"
		matches_1 = re.findall(pattern_1, data)

		pattern_2 = f"{re.escape(href)}.*?{re.escape(keyword)}"
		matches_2 = re.findall(pattern_2, data)

		matches = matches_1 + matches_2

		# 找到所有匹配结果中最短的子字符串
		min_length = min(len(match) for match in matches)
		shortest_matches = [match for match in matches if len(match) == min_length]

		return shortest_matches

	def if_regex_iterable_valid(self, regex_iterable, expanded_string, keyword, href):

		matched = re.match(regex_iterable, expanded_string).group(1)
		return keyword in matched and href in matched

	def get_regex_iterable(self, text, target_str, keyword, href):

		regex_iterable_valid = False
		while not regex_iterable_valid:
			expanded_string = self.expand_str(text, target_str)
			regex_iterable = expanded_string.replace(target_str, '([\s\S]*?)')
			regex_iterable_valid = self.if_regex_iterable_valid(regex_iterable, expanded_string, keyword, href)
			target_str = expanded_string
		return regex_iterable


	def expand_str(self, text, some_str):

		"""
		从文本 y 中提取包含字符串 x 的部分，并逐步扩展 x 的首尾字符。
		第一次扩展时，无论首尾是什么字符，都加到 x 的首尾。
		从第二次开始，只有当扩展的字符不是空值或换行符时，才继续扩展。
		"""

		# 找到 x 在 y 中的起始和结束索引
		start_idx = text.index(some_str)
		end_idx = start_idx + len(some_str)

		# 初始化扩展后的字符串
		expanded_string = some_str

		# 向左扩展
		left_idx = start_idx - 1
		first_expansion = True  # 标记是否为第一次扩展

		while left_idx >= 0:
			char = text[left_idx]
			if first_expansion or (char and char not in [' ', '	', '\n', '<', '>']):
				expanded_string = char + expanded_string
			else:
				expanded_string = char + expanded_string
				break
			left_idx -= 1
			first_expansion = False

		# 向右扩展
		right_idx = end_idx
		first_expansion = True  # 重置标记

		while right_idx < len(text):
			char = text[right_idx]
			if first_expansion or (char and char not in [' ', '	', '\n', '<', '>']):
				expanded_string += char
			else:
				expanded_string += char
				break
			right_idx += 1
			first_expansion = False

		return expanded_string

	def find_entrypath(self, text, keyword, href):

		target_str = self.find_shortest_matches(text, keyword, href)[0]
		regex_iterable = self.get_regex_iterable(text, target_str, keyword, href)
		return regex_iterable


	def test(self):

		url = 'http://fgj.hangzhou.gov.cn/col/col1229265366/index.html'
		response = requests.get(url)
		response.encoding = 'utf-8'
		text = response.text
		keyword = '关于进一步优化调整我市房地产相关政策的通知'
		keyword = '关于进一步优化调整我'
		href = '/art/2024/10/9/art_1229265366_1846208.html'

		target_str = self.find_shortest_matches(text, keyword, href)[0]
		regex_iterable = self.get_regex_iterable(text, target_str, keyword, href)
		logger.info(regex_iterable)

if __name__ == '__main__':

	entry_path_finder = EntryPathFinder()
	entry_path_finder.test()