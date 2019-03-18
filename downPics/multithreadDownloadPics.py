#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import os
import sys
import urllib.parse
import datetime
import time
import threading
import random


G_SITES = {
	1: "Kink".capitalize(),
	2: "Brazzers".capitalize()
}

G_SITES_SETTINGS = {
	"Kink".capitalize(): {
		"pic-count": "40",
		"ssl-cert": "kink.crt",
		"fengmian": None,
		"padding0": False,
		"start-index": "0",
		"batch": "https://cdnp.kink.com/imagedb/{fanhao}/i/h/830/{index}.jpg",
		"referer": "https://www.kink.com/shoot/{fanhao}?eventType=click&eventPage=/&eventElement=swimlane&elementDetails=latest-shoots&totalTiles=20&tilePosition=2",
		"threads-count": 8
	},
	"Brazzers".capitalize(): {
		"pic-count": "5",
		"ssl-cert": "brazzers.crt",
		"fengmian": "https://static-hw.brazzerscontent.com/scenes/{fanhao}/975x548.jpg",
		"padding0": True,
		"start-index": "1",
		"batch": "https://static-hw.brazzerscontent.com/scenes/{fanhao}/preview/img/{index}.jpg",
		"referer": "https://www.brazzersnetwork.com/scenes/view/id/{fanhao}/",
		"threads-count": 3
	}
}

G_URL_ENTRY_DICT = {}

# mutex = threading.Lock()



class UrlEntries:
	def __init__(self, url):
		self.url = url
		#状态：挂起(S)，运行(R)，完成(F)
		self.state = "S"


	def getUrl(self):
		return self.url


	def setState(self, state):
		self.state = state


	def isRunning(self):
		if self.state == "R":
			return True
		else:
			return False


	def isSuspending(self):
		if self.state == "S":
			return True
		else:
			return False


	def isFinished(self):
		if self.state == "F":
			return True
		else:
			return False



class DownloadPicThread(threading.Thread):
	def __init__(self, tid, site, fanhao, tUrlEntries, certDir, saveDir):
		self.tid = tid
		self.site = site
		self.fanhao = fanhao
		self.tUrlEntries = tUrlEntries
		self.certDir = certDir
		self.saveDir = saveDir
		self.timeout = 10
		self.retry = 3
		super(DownloadPicThread, self).__init__()


	def run(self):
		for key, value in self.tUrlEntries.items():
			self.downloadOne(value)
			#随机休眠，以防访问过于频繁导致网站屏蔽，403Forbidden
			time.sleep(random.randint(500,3000)/1000)


	def downloadOne(self, urlEntry):
		msg = "线程" + str(self.tid) + "：下载图片 " + urlEntry.getUrl() +" ** "
		urlEntry.setState("R")
		timeBegin = datetime.datetime.now()
		#如果已存在同名文件，则直接返回
		saveFullPath = self.saveDir + os.path.basename(urlEntry.getUrl())
		if os.path.isfile(saveFullPath):
			msg += "已存在同名图片"
			urlEntry.setState("F")
			print(msg)
			return -1
		#模拟浏览器的HTTP请求头
		global G_SITES_SETTINGS
		host = urllib.parse.urlparse(urlEntry.getUrl()).hostname
		headers = {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "zh-CN,zh;q=0.9",
			"Cache-Control": "max-age=0",
			"Connection": "keep-alive",
			"Host": host,
			"Upgrade-Insecure-Requests": "1",
			"Referer": G_SITES_SETTINGS[self.site]["referer"].format(fanhao=self.fanhao),
			"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
		}
		try:
			content = G_SITES_SETTINGS.get(self.site)
			if content is not None:
				session = requests.Session()
				session.mount('http://', HTTPAdapter(max_retries=self.retry))
				session.mount('https://', HTTPAdapter(max_retries=self.retry))
				cert = content.get("cert")
				if cert is None:
					response = session.get(urlEntry.getUrl(), headers=headers, timeout=self.timeout)
				else:
					response = session.get(urlEntry.getUrl(), headers=headers, timeout=self.timeout, cert=self.certDir+cert)
				msg += "HTTP返回结果%s # " % (response.status_code)
				if response.status_code == 200:
					with open(saveFullPath, 'wb') as f:
						f.write(response.content)
						f.close()
						msg += "下载成功"
				return response.status_code
		except ReadTimeout:
			msg += "连接超时"
			# print(msg)
		except ConnectionError as e:
			msg += "连接错误" + e.message
			# print(msg)
		except RequestException:
			msg += "响应错误"
			# print(msg)
		else:
			msg += "其他异常"
			# print(msg)
		finally:
			urlEntry.setState("F")
			timeEnd = datetime.datetime.now()
			msg += " 耗时%.4f秒" % ((timeEnd-timeBegin).total_seconds())
			print(msg)



class BatchDownload:
	def __init__(self, site=None, fanhao=None, count=None, threadsCount=None):
		self.pwd = os.path.abspath(os.curdir)
		self.site = site
		self.fanhao = fanhao
		self.count = count
		self.timeout = 10
		self.certDir = self.pwd + os.sep + "ssl-cert" + os.sep
		self.saveDir = self.pwd + os.sep + str(fanhao) + os.sep
		self.threadsCount = threadsCount
		self.runningThreadsCount = 0


	def checkParams(self):
		global G_SITES
		global G_SITES_SETTINGS
		#网站
		if self.site is None:
			while True:
				print("请输入站点序号：", end="", flush=True)
				i = 1
				for (k,v) in G_SITES.items():
					if i<len(G_SITES):
						print("%u.%s " % (k,v), end="", flush=True)
					else:
						print("%u.%s：" % (k,v), end="", flush=True)
					i += 1
				s = input()
				if s.isdigit() and (int(s) in G_SITES.keys()):
					self.site = G_SITES[int(s)]
					break
		#番号
		if self.fanhao is None:
			while True:
				print("请输入番号：", end="", flush=True)
				s = input()
				if s.isdigit():
					self.fanhao = int(s)
					break
		#最大探测下载图片个数
		if self.count is None:
			while True:
				print("请输入最大探测下载图片个数，该网站默认为%s，使用默认请按回车键：" % (G_SITES_SETTINGS[self.site]["pic-count"]), end="", flush=True)
				s = input()
				if s == "":
					self.count = int(G_SITES_SETTINGS[self.site]["pic-count"])
					break
				if s.isdigit():
					self.count = int(s)
					break
		#线程数
		if self.threadsCount is None:
			while True:
				print("请输线程数，该网站默认为%s个线程，使用默认请按回车键：" % (G_SITES_SETTINGS[self.site]["threads-count"]), end="", flush=True)
				s = input()
				if s == "":
					self.threadsCount = int(G_SITES_SETTINGS[self.site]["threads-count"])
					break
				if s.isdigit():
					self.threadsCount = int(s)
					break
		return self


	def initGlobalUrlEntries(self):
		global G_URL_ENTRY_DICT
		G_URL_ENTRY_DICT.clear()
		global G_SITES_SETTINGS
		content = G_SITES_SETTINGS.get(self.site)
		key = 1
		#封面
		fengmian = content.get("fengmian")
		if fengmian is not None:
			url = fengmian.format(fanhao=self.fanhao)
			G_URL_ENTRY_DICT[key] = UrlEntries(url)
			key += 1
		#按序号生成图片URL
		batch = content.get("batch")
		startIndex = int(content.get("start-index"))
		for i in range(startIndex, startIndex+self.count):
			if content.get("padding0"):
				url = batch.format(fanhao=self.fanhao, index="0{i}".format(i=i))
			else:
				url = batch.format(fanhao=self.fanhao, index=i)
			G_URL_ENTRY_DICT[key] = UrlEntries(url)
			key += 1
		return self


	def displayParams(self):
		print("图片网站：%s，番号：%d，最大探测下载图片个数%d，下载线程数%d：" % (self.site, self.fanhao, self.count, self.threadsCount))
		return self


	def downloadInBatch(self):
		print("正在启动图片批量下载……")
		global G_SITES_SETTINGS
		content = G_SITES_SETTINGS.get(self.site)
		if content is None:
			print("网站名称错误！")
			return false
		#在当前工作目录下，创建以番号为名的文件夹
		downloadDir = "%s%s%s" % (self.pwd, os.sep, self.fanhao)
		if not os.path.isdir(downloadDir):
			os.mkdir(downloadDir)
		#生成目标图片URL清单
		self.initGlobalUrlEntries()
		#切换工作目录
		os.chdir(downloadDir)
		
		#按序号批量下载图片
		global G_URL_ENTRY_DICT
		threadsList = []
		for i in range(1, 1+self.threadsCount):
			tUrlEntries = {}
			key = i
			while key<=len(G_URL_ENTRY_DICT):
				tUrlEntries[key] = G_URL_ENTRY_DICT[key]
				key += self.threadsCount
			t = DownloadPicThread(tid=i, site=self.site, fanhao=self.fanhao, tUrlEntries=tUrlEntries, certDir=self.certDir, saveDir=self.saveDir)
			threadsList.append(t)
			t.start()
		#监控所有子线程的下载是否完成
		finishedThreadsCount = 0
		while finishedThreadsCount<len(G_URL_ENTRY_DICT):
			finishedThreadsCount = 0
			for (key, value) in G_URL_ENTRY_DICT.items():
				if value.isFinished():
					finishedThreadsCount += 1
			time.sleep(1)
		#切回原先工作目录
		os.chdir(self.pwd)
		print("图片批量下载作业已完成")



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
	#参数：线程数
	threadsCount = None
	if paramsCount>=3 and sys.argv[3].strip().isdigit():
		threadsCount = int(sys.argv[3].strip())
	BatchDownload(site=dirName.capitalize(), fanhao=fanhao, count=count, threadsCount=threadsCount).checkParams().displayParams().downloadInBatch()
