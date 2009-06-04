#!/usr/bin/env python

"""
__version__ = "$Revision: 0.6 $"
__date__ = "$Date: 2009/05/28 $"

"""

import urllib2
import os
import sys
import zipfile
import re
import time
import optparse
import threading

web = "bisnis-jakarta"

def main():
	cmd = optparse.OptionParser()
	cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
	cmd.add_option("-d", "--dir", dest="dir", default=web)
	cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
	cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
	(options, args) = cmd.parse_args()
	
	if options.concurrent < 1 or options.concurrent > 10:
		concurrent = 1
	else:
		concurrent = options.concurrent
	filePrefix = options.filePrefix
	zip = options.zip
	dir = os.path.normpath(options.dir) + '/'
	
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://www.%s.com/" % (web)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	
	framePage = re.compile('src\s?="([^"]+)"').findall(html)
	if not framePage:
		log("Error..")
		sys.exit(1)
		
	log(framePage[0])
	page = opener.open(framePage[0])
	html = page.read()

	docId = re.compile('documentId:\s"([^"]+)"').findall(html)
	if not docId:
		log("docId=0")
		sys.exit(1)
		
	sDate = re.compile('\S+ (\S+) (\S+) (\S+) \S+ GMT').findall(page.headers.getheader('date'))
	if not sDate:
		log("Date=0")
		sys.exit(1)
	fDate = "%s-%s-%s" %(sDate[0][2], getMonth(sDate[0][1]), sDate[0][0]) 
	indexPage = "http://document.issuu.com/%s/document.xml" % (docId[0])
	log(indexPage)
	page = opener.open(indexPage)
	html = page.read()
	
	pageCount = re.compile('pageCount="(\d+)"').findall(html)
	if not pageCount:
		log("pageCount=0")
		sys.exit(1)

	Url = "http://image.issuu.com/%s/jpg/page_" % (docId[0])
	
	if not os.path.exists(dir + fDate):
		os.makedirs(dir + fDate)
		
	threads = []
	s = threading.Semaphore(concurrent)
	for x in range(1, int(pageCount[0]) + 1):
		outFile = '%s%s/%s_%s_%02d.jpg' % (dir, fDate, filePrefix, fDate, x)
		page = "%s.jpg" %(str(x))
		pageUrl = Url + page
		threads.append(threading.Thread(target=downloader, args=(opener, pageUrl, outFile, s)))
		threads[-1].start()
		
	for thread in threads:
		thread.join()
		
	if zip:
		zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
		makezip(dir + fDate, zipFile)
		
	log("\n-")
		
def makezip(dir, filename):
	log("Create %s" % (filename)) 
	zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
	for pdf in os.listdir(dir):
		zip.write(dir + '/' + pdf)
	zip.close()

def downloader(opener, url, filename, s):
	s.acquire()
	try:
		page = opener.open(url)		
		if os.path.exists(filename):
			if page.headers.getheader('Content-Length'):
				if long(page.headers.getheader('Content-Length')) == os.path.getsize(filename):
					log("Skip %s" % (filename))
					page.close()
					return
		log("Download %s" % (filename))			
		pdf = page.read()
		f = open(filename, "w")
		f.write(pdf)
		f.close()
		page.close()
	finally:
		s.release()
		
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)

def getMonth(month):
	dict = {'Jan': "01", 'Feb': "02", 'Mar': "03", 'Apr': "04", 'May': "05", 'Jun': "06", 'Jul': "07", 'Aug': "08", 'Sep': "09", 'Oct': "10", 'Nov': "11", 'Dec': "12"}
	return dict[month]
	
if __name__ == '__main__':
	main()