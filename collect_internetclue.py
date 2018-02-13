import wx
import time
import datetime
import ctypes
import pymysql
from selenium import webdriver
from PIL import Image
import sys
import os
import hashlib

class Example(wx.Frame):
	def __init__(self, parent, title):
		super(Example, self).__init__(parent, title=title, size=(250, 150))
		self.bmp = None
		
		pan = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		btn1 = wx.Button(pan,label = u'현재 화면 캡쳐 및 저장',size=(200,30))
		vbox.Add(btn1)

		btn2 = wx.Button(pan,label = '현재 페이지 캡쳐 및 저장', size=(200,30))
		vbox.Add(btn2)

		btn3 = wx.Button(pan,label = '전체 페이지 캡쳐 및 저장', size=(200,30))
		vbox.Add(btn3)

		pan.SetSizer(vbox)

		btn1.Bind(wx.EVT_BUTTON, self.onbtn1)
		btn2.Bind(wx.EVT_BUTTON, self.onbtn2)
		btn3.Bind(wx.EVT_BUTTON, self.onbtn3)

		self.Centre()
		self.Show()

	def onbtn1(self,event): # print time.ctime() # 현재시간
		conn = pymysql.connect(host='flagish.kr', user='sohye', passwd='test', db='webshot', charset='utf8')
		curs = conn.cursor()
		dc = wx.ScreenDC() # dc= wx.ClientDC(self)
		mem = wx.MemoryDC()
		user32 = ctypes.windll.user32

		now = datetime.datetime.now()

		TIME = now.strftime('%Y-%m-%d %H:%M:%S')
		FILENAME = "display_"+now.strftime('%Y%m%d%H%M%S')+".png"
		
		x = user32.GetSystemMetrics(0)
		y = user32.GetSystemMetrics(1)

		if dc.IsOk(): 
			bmp2 = wx.Bitmap(x,y)
			mem.SelectObject(bmp2)
			mem.Blit(0,0,x,y,dc,0,0)

			mem.SelectObject(wx.NullBitmap)
			self.bmp = bmp2
			self.bmp.SaveFile(FILENAME,wx.BITMAP_TYPE_PNG)
		

		MD5 = hashlib.md5(FILENAME.encode('utf-8')).hexdigest()
		sql = "INSERT INTO screenshot_info (TIME, FILENAME, MD5) VALUES (%s, %s, %s)"
		curs.execute(sql,(TIME, FILENAME, MD5))
		conn.commit()
		conn.close()
		

	def onbtn2(self,event):
		conn = pymysql.connect(host='flagish.kr', user='sohye', passwd='test', db='webshot', charset='utf8')
		curs = conn.cursor()

		driver = webdriver.Chrome("C:\chromedriver_win32\chromedriver.exe")
		print("Enter the url that you want to capture.")
		url = input()
		driver.get('http://'+url)

		now = datetime.datetime.now()
		TIME = now.strftime('%Y-%m-%d %H:%M:%S')
		FILENAME = "screenshot_"+now.strftime('%Y%m%d%H%M%S')+".png"

		driver.close()
		
		MD5 = hashlib.md5(FILENAME.encode('utf-8')).hexdigest()
		sql = "INSERT INTO screenshot_info (TIME, FILENAME, MD5) VALUES (%s, %s, %s)"
		curs.execute(sql,(TIME, FILENAME, MD5))
		conn.commit()
		conn.close()

	def fullpage_screenshot(driver, file):

		total_width = driver.execute_script("return document.body.offsetWidth")
		total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
		viewport_width = driver.execute_script("return document.body.clientWidth")
		viewport_height = driver.execute_script("return window.innerHeight")
		print("Total: ({0}, {1}), Viewport: ({2},{3})".format(total_width, total_height,viewport_width,viewport_height))
		rectangles = []

		i = 0
		while i < total_height:
			ii = 0
			top_height = i + viewport_height

			if top_height > total_height:
				top_height = total_height

			while ii < total_width:
				top_width = ii + viewport_width

				if top_width > total_width:
					top_width = total_width

				print("Appending rectangle ({0},{1},{2},{3})".format(ii, i, top_width, top_height))
				rectangles.append((ii, i, top_width,top_height))

				ii = ii + viewport_width

			i = i + viewport_height

		stitched_image = Image.new('RGB', (total_width, total_height))
		previous = None
		part = 0

		for rectangle in rectangles:
			if not previous is None:
				driver.execute_script("window.scrollTo({0}, {1})".format(rectangle[0], rectangle[1]))
				time.sleep(0.2)
				driver.execute_script("list = document.getElementsByClassName('header'); list[0].setAttribute('style', 'position: absolute; top: 0px;');")
				time.sleep(0.2)
				print("Scrolled To ({0},{1})".format(rectangle[0], rectangle[1]))
			file_name = "part_{0}.png".format(part)
			print("Capturing {0} ...".format(file_name))

			driver.get_screenshot_as_file(file_name)
			screenshot = Image.open(file_name)

			if rectangle[1] + viewport_height > total_height:
				offset = (rectangle[0], total_height - viewport_height)
			else:
				offset = (rectangle[0], rectangle[1])

			print("Adding to stitched image with offset ({0}, {1})".format(offset[0],offset[1]))
			stitched_image.paste(screenshot, offset)

			del screenshot
			os.remove(file_name)
			part = part + 1
			previous = rectangle

		stitched_image.save(file)
		printf("Finish")
		return True		

	def onbtn3(self,event):
		conn = pymysql.connect(host='flagish.kr', user='sohye', passwd='test', db='webshot', charset='utf8')
		curs = conn.cursor()
		driver = webdriver.Chrome("C:\chromedriver_win32\chromedriver.exe")

		now = datetime.datetime.now()
		TIME = now.strftime('%Y-%m-%d %H:%M:%S')
		FILENAME = "full_screenshot_"+now.strftime('%Y%m%d%H%M%S')+".png"

		print("Input DOMAIN that you want to capture.")
		url = input()
		driver.get('http://'+url)

		Example.fullpage_screenshot(driver, FILENAME)

		MD5 = hashlib.md5(FILENAME.encode('utf-8')).hexdigest()

		sql = "INSERT INTO screenshot_info (TIME, FILENAME, MD5) VALUES (%s, %s, %s)"
		curs.execute(sql,(TIME, FILENAME, MD5))
		conn.commit()
		conn.close()


if __name__ == '__main__': 
	app = wx.App()
	Example(None, '채증 프로그램')
	app.MainLoop()
