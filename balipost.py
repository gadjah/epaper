#!/usr/bin/python

import urllib2
import os
import sys
import zipfile
import re
import time
import optparse

web = "balipost"

def main():
	cmd = optparse.OptionParser()
	cmd.add_option("-d", "--dir", dest="dir", default=web)
	cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
	cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
	(options, args) = cmd.parse_args()
	
	filePrefix = options.filePrefix
	zip = options.zip
	dir = os.path.normpath(options.dir) + '/'
	
	#proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://epaper.%s.com/epaper.php" % (web)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	
	docId = re.compile('documentId=([^&]+)').findall(html)
	if not docId:
		log("docId=0")
		sys.exit(1)
		
	sDate = re.compile('docName=bp(\d+)').findall(html)
	if not sDate:
		log("Date=0")
		sys.exit(1)
		
	date = sDate[0][0:2]
	month = sDate[0][2:4]
	year = sDate[0][4:]

	indexPage = "http://document.issuu.com/%s/document.xml" % (docId[0])
	log(indexPage)
	page = opener.open(indexPage)
	html = page.read()
	
	pageCount = re.compile('pageCount="(\d+)"').findall(html)
	if not pageCount:
		log("pageCount=0")
		sys.exit(1)
	
		
	fDate = "%s-%s-%s" %(year, month, date)
	Url = "http://image.issuu.com/%s/jpg/page_" % (docId[0])
	
	if not os.path.exists(dir + fDate):
		os.makedirs(dir + fDate)
		
	for x in range(1, int(pageCount[0]) + 1):
		outFile = '%s%s/%s_%s_%02d.jpg' % (dir, fDate, filePrefix, fDate, x)
		page = "%s.jpg" %(str(x))
		pageUrl = Url + page
		log(pageUrl)
		
		try:
			pageUrl = opener.open(pageUrl)		
		except urllib2.HTTPError:
			break
		
		if os.path.exists(outFile):
			#content-length
			if pageUrl.headers.items()[1][1].isdigit():
				if long(pageUrl.headers.items()[1][1]) == os.path.getsize(outFile):
					log("Skip %s" % (outFile))
					pageUrl.close()
					continue
		
		log("Download %s" %(outFile))			
		pdf = pageUrl.read()
		
		f = open(outFile, "w")
		f.write(pdf)
		f.close()
		pageUrl.close()
		
	if zip:
		zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate) 
		log("Create %s" %(zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in range(1, int(pageCount[0]) + 1):
			outFile = '%s%s/%s_%s_%02d.jpg' % (dir, fDate, filePrefix, fDate, x)
			zip.write(outFile)
		zip.close()
		
	log("\n-")
		
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
	
if __name__ == '__main__':
	main()