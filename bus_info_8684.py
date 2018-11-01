import json
import os
import re

import requests
from lxml import etree


class Bus_spider:
    def __init__(self, url):
        """
        初始化参数
        :param url:需要爬取的公交路线的网址url
        """
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        }

    def parse_navigation(self):
        """
        # 解析内容，获取数字或者字母开头的导航链接
        :param url: 初始获得的链接
        :return: 一个列表，数字或者字母开头的导航链接
        """
        r = requests.get(url=self.url, headers=self.headers)
        r_html = etree.HTML(r.text)
        num_href_list = r_html.xpath('//div[@class="bus_kt_r1"]/a/@href')  # 查找以数字开头的所有链接
        char_href_list = r_html.xpath('//div[@class="bus_kt_r2"]/a/@href')  # 查找以字母开头的所有链接
        # print(char_href_list)
        return num_href_list + char_href_list

    def parse_bus_num(self):
        """
        遍历列表，依次发送请求，解析内容，获取公交路线的路数
        :param nav_list: 一个列表，数字或者字母开头的导航链接
        :return: 一个列表，所有公交路线的路数
        """
        bus_num_list = []
        for link in self.nav_list:
            r = requests.get(url=self.url + link, headers=self.headers)
            r_html = etree.HTML(r.text)
            bus_num = r_html.xpath('//div[@id="con_site_1"]/a/@href')
            # print(bus_num)
            bus_num_list.extend(bus_num)
        return bus_num_list

    def parse_bus_line(self):
        """
        遍历列表，依次发送请求，解析内容，获取公交详细信息
        :return: 一个字典形式的列表，每一个字典都是一路公交的信息
        """
        bus_line_list = []
        bus_line_circle = []
        for link in self.bus_num_list:
            bus_line_dict = {}
            r = requests.get(url=self.url + link, headers=self.headers)
            r_html = etree.HTML(r.text)
            time = r_html.xpath('//p[@class="bus_i_t4"]/text()')[0]
            price = r_html.xpath('//p[@class="bus_i_t4"]/text()')[1]
            company = r_html.xpath('//p[@class="bus_i_t4"]/a/text()')
            datetime = r_html.xpath('//p[@class="bus_i_t4"]/text()')[3]
            try:
                bus_up_name = r_html.xpath('//div[@class="bus_line_txt"]/strong/text()')[0]
                bus_down_name = r_html.xpath('//div[@class="bus_line_txt"]/strong/text()')[1]
                bus_up_num = self.get_digit(r_html.xpath('////div[@class="bus_line_top "]/span/text()')[0])
                bus_down_num = self.get_digit(r_html.xpath('////div[@class="bus_line_top "]/span/text()')[1])
                bus_up_line = r_html.xpath('//div[@class="bus_site_layer"]/div/a/text()')[:bus_up_num]
                bus_down_line = r_html.xpath('//div[@class="bus_site_layer"]/div/a/text()')[bus_down_num:]
            except Exception as e:
                bus_up_name = r_html.xpath('//div[@class="bus_line_txt"]/strong/text()')[0]
                bus_up_num = self.get_digit(r_html.xpath('////div[@class="bus_line_top "]/span/text()')[0])
                bus_up_line = r_html.xpath('//div[@class="bus_site_layer"]/div/a/text()')
                bus_down_name = bus_up_name
                bus_down_num = 0
                bus_down_line = []
                bus_line_circle.append(bus_up_name)  # 输出错误类型，其实可以查看哪些是环形路线
            bus_line_dict['time'] = time  # 运行时间
            bus_line_dict['price'] = price  # 票价
            bus_line_dict['company'] = company  # 所属公司
            bus_line_dict['datetime'] = datetime  # 更新时间
            bus_line_dict['up_name'] = bus_up_name  # 上行名字
            bus_line_dict['up_num'] = bus_up_num  # 上行路数
            bus_line_dict['up_line'] = bus_up_line  # 上行路线
            bus_line_dict['down_name'] = bus_down_name  # 下行名字
            bus_line_dict['down_num'] = bus_down_num  # 下行路数
            bus_line_dict['down_line'] = bus_down_line  # 下行路线
            bus_line_list.append(bus_line_dict)  # 添加到列表中
        return bus_line_list, bus_line_circle

    def get_digit(self, str):
        """
        获取某一个字符串里的数字
        :param str: 需要获取的字符串
        :return: int,提取出来的数字
        """
        return int(re.findall('\d+', str)[0])

    def mkdir(self):
        """
        创建文件来保存数据，以公交线路命名的json文件
        """
        file_dir = 'bus_info'
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        for data in self.bus_line_list:
            data_json = json.dumps(data)
            file_name = re.findall('(.*?)\(.*?\)', data['up_name'])[0]
            file_path = file_dir + '/' + file_name + '.json'
            with open(file_path, 'a') as f:
                f.write(data_json)
        for i in self.bus_line_circle:
            with open(file_dir + '/' + '环形路线.txt', 'a', encoding='utf8') as f:
                f.write(str(i + '\n'))

    def run(self):
        """
        运行程序
        """
        self.nav_list = self.parse_navigation()  # 爬取第一页所有导航链接
        self.bus_num_list = self.parse_bus_num()  # 爬取每个链接下的公交路线号码
        self.bus_line_list, self.bus_line_circle = self.parse_bus_line()  # 爬取每个公交路线号码的路线
        self.mkdir()


bus = Bus_spider('http://hangzhou.8684.cn/')
bus.run()
