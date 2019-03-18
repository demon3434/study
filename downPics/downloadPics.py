#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import os
import urllib.parse
import datetime
# import requests.packages.urllib3.util.ssl_

class PicBatchDownloader:
	def __init__(self, site=None, fanhao=None, count=None):
		self.SITES = {
			1: "Kink".capitalize(),
			2: "Brazzers".capitalize()
		}
		self.SITES_SETTINGS = {
			"Kink".capitalize(): {
				"pic-count": "40",
				"ssl-cert": "kink.crt",
				"fengmian": None,
				"padding0": False,
				"start-index": "0",
				"batch": "https://cdnp.kink.com/imagedb/{fanhao}/i/h/830/{index}.jpg"
			},
			"Brazzers".capitalize(): {
				"pic-count": "5",
				"ssl-cert": "brazzers.crt",
				"fengmian": "https://static-ll.brazzerscontent.com/scenes/{fanhao}/975x548.jpg",
				"padding0": True,
				"start-index": "1",
				"batch": "https://static-hw.brazzerscontent.com/scenes/{fanhao}/preview/img/{index}.jpg"
			}
		}
		self.pwd = os.path.abspath(os.curdir)
		if self.pwd.endswith(os.sep):
			self.pwd = self.pwd[:-1]
		if site in self.SITES.values():
			self.site = site
		else:
			self.site = None
		self.fanhao = fanhao
		self.count = count
		self.timeout = 10
		self.certDir = self.pwd + os.sep + "ssl-cert" + os.sep


	def checkParams(self):
		#网站
		if self.site is None:
			while True:
				print("请输入站点序号：", end="")
				i = 1
				for (k,v) in self.SITES.items():
					if i<len(self.SITES):
						print("%u.%s " % (k,v), end="")
					else:
						print("%u.%s：" % (k,v), end="")
					i += 1
				s = input()
				if s.isdigit() and (int(s) in self.SITES.keys()):
					self.site = self.SITES[int(s)]
					break
		#番号
		if self.fanhao is None:
			while True:
				print("请输入番号：", end="")
				s = input()
				if s.isdigit():
					self.fanhao = int(s)
					break
		#最大探测下载图片个数
		if self.count is None:
			while True:
				print("请输入最大探测下载图片个数，该网站默认为%s，使用默认请按回车键：" % (self.SITES_SETTINGS[self.site]["pic-count"]), end="")
				s = input()
				if s == "":
					self.count = int(self.SITES_SETTINGS[self.site]["pic-count"])
					break
				if s.isdigit():
					self.count = int(s)
					break
		return self


	def displayParams(self):
		print("图片网站：%s，番号：%d，最大探测下载图片个数%d：" % (self.site, self.fanhao, self.count))
		return self


	def downloadOne(self, url, filename=None):
		print("当前图片 "+url+" ** ", end="")
		timeBegin = datetime.datetime.now()
		#filename是绝对路径，包含完整的目录和文件名信息
		if filename is None:
			filename = self.pwd + os.sep + str(self.fanhao) + os.sep + os.path.basename(url)
		#如果已存在同名文件，则直接返回
		if os.path.isfile(filename):
			print("已存在同名图片")
			return -1
		#模拟浏览器的HTTP请求头
		host = urllib.parse.urlparse(url).hostname
		headers = {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "zh-CN,zh;q=0.9",
			"Cache-Control": "max-age=0",
			"Connection": "keep-alive",
			"Host": host,
			"Upgrade-Insecure-Requests": "1",
			"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
		}
		# requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'
		try:
			content = self.SITES_SETTINGS.get(self.site)
			if content is not None:
				cert = content.get("cert")
				if cert is None:
					response = requests.get(url, headers=headers, timeout=self.timeout)
				else:
					response = requests.get(url, headers=headers, timeout=self.timeout, cert=self.certDir+cert)
				print("HTTP返回结果%s # " % (response.status_code), end="")
				if response.status_code == 200:
					with open(filename, 'wb') as f:
						f.write(response.content)
						f.close()
						print("下载成功", end="")
				return response.status_code
		except ReadTimeout:
		    print("连接超时")
		except ConnectionError as e:
		    print("连接错误", e)
		except RequestException:
		    print("响应错误")
		else:
			print("其他异常")
		finally:
			timeEnd = datetime.datetime.now()
			print(" 耗时%.4f秒" % ((timeEnd-timeBegin).total_seconds()))
			pass


	def downloadInBatch(self):
		print("正在启动图片批量下载……")
		content = self.SITES_SETTINGS.get(self.site)
		if content is None:
			print("网站名称错误！")
			return false
		#在当前工作目录下，创建以番号为名的文件夹
		downloadDir = "%s%s%s" % (self.pwd, os.sep, self.fanhao)
		if not os.path.isdir(downloadDir):
			os.mkdir(downloadDir)
		#切换工作目录
		os.chdir(downloadDir)
		#下载封面
		fengmian = content.get("fengmian")
		if fengmian is not None:
			url = fengmian.format(fanhao=self.fanhao)
			self.downloadOne(url, None)
		#按序号批量下载图片
		batch = content.get("batch")
		startIndex = int(content.get("start-index"))
		for i in range(startIndex, startIndex+self.count):
			if content.get("padding0"):
				url = batch.format(fanhao=self.fanhao, index="0{i}".format(i=i))
			else:
				url = batch.format(fanhao=self.fanhao, index=i)
			self.downloadOne(url, None)
		#切回原先工作目录
		os.chdir(self.pwd)
		print("图片批量下载作业已完成")




# PicBatchDownloader("Brazzers", 2436834, 5).downloadInBatch()
# PicBatchDownloader("Kink", 43245, 40).downloadInBatch()
if __name__ == '__main__':
	paramsCount = len(sys.argv) - 1
	#参数：网站
	pwd = os.getcwd()
	if pwd.endswith(os.sep):
		pwd = pwd[:-1]
	dirName = pwd.split(os.sep)[-1]
	#参数：番号
	fanhao = None
	if paramsCount>=1 and sys.argv[1].strip().isdigit():
		fanhao = int(sys.argv[1].strip())
	#参数：最大探测下载图片个数
	count = None
	if paramsCount>=2 and sys.argv[2].strip().isdigit():
		count = int(sys.argv[2].strip())
	PicBatchDownloader(site=dirName.capitalize(), fanhao=fanhao, count=count).checkParams().displayParams().downloadInBatch()