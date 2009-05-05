#!/usr/bin/python

"""
__version__ = "$Revision: 0.3 $"
__date__ = "$Date: 2009/05/03 $"
"""

import urllib2
import os
import sys
import zipfile
import re

ZIP = 1	
prefix = "pikiran-rakyat"

def main():
	#proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://epaper.%s.com" % (prefix)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	
	pageCount = re.compile('/images/flippingbook/PR/(\d+)/(\w+)/(\d+)/\d+_zoom_(\d+).jpg').findall(html)
	if not pageCount:
		log("pageCount=0")
		sys.exit(1)
	
	date = pageCount[0][2][0:2]
	month = getMonth(pageCount[0][1])
	year = pageCount[0][0]
		
	fDate = "%s-%s-%s" %(year, month, date)
	Url = "http://epaper.%s.com/images/flippingbook/PR/" % (prefix)
	
	if not os.path.exists(fDate):
		os.mkdir(fDate)
	
	for x in pageCount:
		#x = '(2009', 'Mei', '030509', '01')
		outFile = '%s/%s_%s_%s.jpg' % (fDate, prefix, fDate, x[3])
		page = "%s/%s/%s/%s_zoom_%s.jpg" % (x[0], x[1], x[2], x[2], x[3])
		pageUrl = Url + page
		log(pageUrl)
		pageUrl = opener.open(pageUrl)

		if os.path.exists(outFile):
			#content-length
			if pageUrl.headers.items()[0][1].isdigit():
				if long(pageUrl.headers.items()[0][1]) == os.path.getsize(outFile):
					log("Skip %s" %(outFile))
					pageUrl.close()
					continue
					
		log("Download %s" %(outFile))			
		jpg = pageUrl.read()
		f = open(outFile, "w")
		f.write(jpg)
		f.close()
		pageUrl.close()

	if ZIP == 1:
		zipFile = "%s_%s.zip" % (prefix, fDate)
		log("Create %s" % (zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in pageCount:
			outFile = '%s/%s_%s_%s.jpg' % (fDate, prefix, fDate, x[3])
			zip.write(outFile)
		zip.close()
		
	log("\n-")
		
def log(str):
	print ">>> %s" %(str)
	
def getMonth(month):
	dict = {'Januari': "01", 'Februari': "02", 'Maret': "03", 'April': "04", 'Mei': "05", 'Juni': "06", 'Juli': "07", 'Agustus': "08", 'September': "09", 'Oktober': "10", 'November': "11", 'Desember': "12"}
	return dict[month]

if __name__ == '__main__':
	main()