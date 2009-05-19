#!/usr/bin/python

"""
__version__ = "$Revision: 0.5 $"
__date__ = "$Date: 2009/05/19 $"
"""

import urllib2
import os
import sys
import zipfile
import re
import time
import optparse

web = "mediaindonesia"

def main():
	cmd = optparse.OptionParser()
	cmd.add_option("-d", "--dir", dest="dir", default=web)
	cmd.add_option("-n", "--no-merge", action="store_false", dest="merge", default=True)
	cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
	cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
	(options, args) = cmd.parse_args()
	
	filePrefix = options.filePrefix
	zip = options.zip
	dir = os.path.normpath(options.dir) + '/'
	merge = options.merge

	#proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://anax1a.pressmart.net/%s" % (web)
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
	Url = "http://anax1a.pressmart.net/%s/MI/MI/%s/%s/%s/PagePrint/" % (web, year, month, date)
	
	if not os.path.exists(dir + fDate):
		os.makedirs(dir + fDate)
	
	for x in pageCount:
		outFile = '%s%s/%s_%s_%s.pdf' % (dir, fDate, filePrefix, fDate, x[11:14])
		page = "%s.pdf" %(x[0:14])
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
		pdf = pageUrl.read()
		f = open(outFile, "w")
		f.write(pdf)
		f.close()
		pageUrl.close()
		
	if merge:
		import pyPdf
		outPdf = pyPdf.PdfFileWriter()
		outFilePdf = "%s%s/%s_%s.pdf" %(dir, fDate, filePrefix, fDate)
		log("Create %s" % (outFilePdf))
		for x in pageCount:
			outFile = '%s%s/%s_%s_%s.pdf' % (dir, fDate, filePrefix, fDate, x[11:14])
			inStream = file(outFile, 'rb')
			inPdf = pyPdf.PdfFileReader(inStream)
			if not inPdf.getIsEncrypted():
				for numPage in range(0, inPdf.numPages):
					outPdf.addPage(inPdf.getPage(numPage))
				outStream = file(outFilePdf, 'wb')
				outPdf.write(outStream)
				inStream.close()
				outStream.close()
		
	if zip:
		zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
		log("make %s" %(zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in pageCount:
			outFile = '%s%s/%s_%s_%s.pdf' % (dir, fDate, filePrefix, fDate, x[11:14])
			zip.write(outFile)
		zip.close()
		
	log("\n-")
		
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
	
if __name__ == '__main__':
	main()