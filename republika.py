#!/usr/bin/env python

"""
__version__ = "$Revision: 0.6  $"
__date__ = "$Date: 2009/05/28 $"
"""

import urllib2
import os
import sys
import zipfile
import re
import time
import optparse
import pyPdf
import threading

web = "republika"

def main():
	cmd = optparse.OptionParser()
	cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
	cmd.add_option("-d", "--dir", dest="dir", default=web)
	cmd.add_option("-n", "--no-merge", action="store_false", dest="merge", default=True)
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
	m = options.merge

	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://%s.pressmart.com/default.aspx" % (web)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	
	pageCount = re.compile("pagethumb/([^']+)").findall(html)
	if not pageCount:
		log("pageCount=0")
		sys.exit(1)
	
	date = pageCount[0][0:2]
	month = pageCount[0][3:5]
	year = pageCount[0][6:10]
		
	fDate = "%s-%s-%s" %(year, month, date)
	Url = "http://%s.pressmart.com/RP/RP/%s/%s/%s/PagePrint/" % (web, year, month, date)
	
	if not os.path.exists(dir + fDate):
		os.makedirs(dir + fDate)

	threads = []
	s = threading.Semaphore(concurrent)
	for x in range(0, len(pageCount)):
		outFile = '%s%s/%s_%s_%s.pdf' % (dir, fDate, filePrefix, fDate, pageCount[x][11:14])
		page = "%s.pdf" % (pageCount[x][0:14])
		pageUrl = Url + page
		threads.append(threading.Thread(target=downloader, args=(opener, pageUrl, outFile, s)))
		threads[-1].start()

	for thread in threads:
		thread.join()
		
	if m:
		filePdf = "%s%s_%s.pdf" % (dir, filePrefix, fDate)
		merge(dir + fDate, filePdf)
		
	if zip:
		zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
		makezip(dir + fDate, zipFile)
		
	log("\n-")

def downloader(opener, url, filename, s):
	s.acquire()
	try:
		page = opener.open(url)
		if os.path.exists(filename):
			#content-length
			if page.headers.items()[0][1].isdigit():
				if long(page.headers.items()[0][1]) == os.path.getsize(filename):
					log("Skip %s" % (filename))
					return
		log("Download %s" % (filename))			
		pdf = page.read()
		f = open(filename, "w")
		f.write(pdf)
		f.close()
		page.close()
	finally:
		s.release()
	
def merge(dir, filename):
	outPdf = pyPdf.PdfFileWriter()
	log("Create %s" % (filename))
	for pdf in os.listdir(dir):
		inStream = file(dir + '/' + pdf, 'rb')
		inPdf = pyPdf.PdfFileReader(inStream)
		if not inPdf.getIsEncrypted():
			for numPage in range(0, inPdf.numPages):
				outPdf.addPage(inPdf.getPage(numPage))
			outStream = file(filename, 'wb')
			outPdf.write(outStream)
			inStream.close()
			outStream.close()

def makezip(dir, filename):
	log("Create %s" % (filename)) 
	zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
	for pdf in os.listdir(dir):
		zip.write(dir + '/' + pdf)
	zip.close()
	
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
	
if __name__ == '__main__':
	main()