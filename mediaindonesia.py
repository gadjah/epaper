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
import time

ZIP = 1
MERGE = 1
prefix = "mediaindonesia"

def main():
	proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://anax1a.pressmart.net/%s" % (prefix)
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
	Url = "http://anax1a.pressmart.net/%s/MI/MI/%s/%s/%s/PagePrint/" % (prefix, year, month, date)
	
	if not os.path.exists(fDate):
		os.mkdir(fDate)
	
	for x in pageCount:
		outFile = '%s/%s_%s_%s.pdf' % (fDate, prefix, fDate, x[11:14])
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
		
	if MERGE == 1:
		import pyPdf
		outPdf = pyPdf.PdfFileWriter()
		outFilePdf = "%s/%s_%s.pdf" %(fDate, prefix, fDate)
		log("Create %s" % (outFilePdf))
		for x in pageCount:
			outFile = '%s/%s_%s_%s.pdf' % (fDate, prefix, fDate, x[11:14])
			inStream = file(outFile, 'rb')
			inPdf = pyPdf.PdfFileReader(inStream)
			if not inPdf.getIsEncrypted():
				for numPage in range(0, inPdf.numPages):
					outPdf.addPage(inPdf.getPage(numPage))
				outStream = file(outFilePdf, 'wb')
				outPdf.write(outStream)
				inStream.close()
				outStream.close()
		
	if ZIP == 1:
		zipFile = "%s_%s.zip" % (prefix, fDate)
		log("make %s" %(zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in pageCount:
			outFile = '%s/%s_%s_%s.pdf' % (fDate, prefix, fDate, x[11:14])
			zip.write(outFile)
		zip.close()
		
	log("\n-")
		
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
	
if __name__ == '__main__':
	main()