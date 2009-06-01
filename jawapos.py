#!/usr/bin/env python

"""
__version__ = "$Revision: 0.6 $"
__date__ = "$Date: 2009/05/28 $"
"""

import urllib2
import os
import sys
import re
import zipfile
import time
import optparse
import pyPdf
import threading

web = "jawapos"

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

	mainPage = "http://versipdf.%s.co.id/" % (web)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	
	pageCount = re.compile("(loadGbr\w+)\(\d+,'(\d+)',this\) >(\d+)<\/td>").findall(html)
	#('loadGbrXX', 'id', 'pageid')
	if not pageCount:
		log("pageCount=0")
		sys.exit(1)
		
	pageLink = re.compile('<a id="(\w+)" target="_blank" href="([^&]+_det&file_det=)').findall(html)
	#('linkXX', 'index.php?detail=xx_det&file_det=')
	if not pageLink:
		log("pageLink=0")
		sys.exit(1)
		
	pageDict = {}
	for item in pageLink:
		pageDict[item[0][-2:]] = item[1]

	sDate = re.compile('\S+ (\S+) (\S+) (\S+) \S+ GMT').findall(page.headers.getheader('date'))
	if not sDate:				
		sDate.append((time.strftime('%d', time.localtime()), time.strftime('%b', time.localtime()), time.strftime('%Y', time.localtime())))
	fDate = "%s-%s-%s" %(sDate[0][2], getMonth(sDate[0][1]), sDate[0][0]) 
			
	if not os.path.exists(dir + fDate):
		os.makedirs(dir + fDate)

	threads = []
	s = threading.Semaphore(concurrent)
	for x in pageCount:
		indexFile = pageDict[x[0][-2:]]
		url = "http://versipdf.%s.co.id/%s%s" % (web, indexFile, x[1])
		outFile = '%s%s/%s_%s_%02d.pdf' % (dir, fDate, filePrefix, fDate, int(x[2]))
		threads.append(threading.Thread(target=downloader, args=(opener, url, outFile, s)))
		threads[-1].start()

	for thread in threads:
		thread.join()
		
	if m:
		outFilePdf = "%s%s_%s.pdf" %(dir, filePrefix, fDate)
		merge(dir + fDate, outFilePdf)
		
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

def merge(dir, filename):
	outPdf = pyPdf.PdfFileWriter()
	log("Create %s" % (filename))
	for pdf in os.listdir(dir):
		inStream = file(dir + '/' + pdf, 'rb')
		inPdf = pyPdf.PdfFileReader(inStream)
		totalPage = 0
		if inPdf.getIsEncrypted():
			if inPdf.decrypt(''):
				totalPage = inPdf.numPages
		else:
			totalPage = inPdf.numPages
			
		if totalPage:
			for numPage in range(0, totalPage):
				outPdf.addPage(inPdf.getPage(numPage))
			outStream = file(filename, 'wb')
			outPdf.write(outStream)
			inStream.close()
			outStream.close()

def downloader(opener, url, filename, s):
	s.acquire()
	try:
		log(url)
		page = opener.open(url)
		if os.path.exists(filename):
			if page.headers.getheader('Content-Length'):
				if long(page.headers.getheader('Content-Length')) == os.path.getsize(filename):
					log("Skip %s" %(filename))
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
