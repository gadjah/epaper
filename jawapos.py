#!/usr/bin/python

"""
__version__ = "$Revision: 0.5 $"
__date__ = "$Date: 2009/05/19 $"
"""

import urllib2
import os
import sys
import re
import zipfile
import time
import optparse

web = "jawapos"

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

	sDate = []
	
	for x in pageCount:
		indexFile = pageDict[x[0][-2:]]
		Url = "http://versipdf.%s.co.id/%s%s" % (web, indexFile, x[1])
		log(Url)
		pageUrl = opener.open(Url)
		
		if not sDate:
			if pageUrl.headers.items()[8][0] == 'date':
				sDate = re.compile('\S+ (\S+) (\S+) (\S+) \S+ GMT').findall(pageUrl.headers.items()[8][1])
			else:
				sDate.append((time.strftime('%d', time.localtime()), time.strftime('%b', time.localtime()), time.strftime('%Y', time.localtime())))
			fDate = "%s-%s-%s" %(sDate[0][2], getMonth(sDate[0][1]), sDate[0][0]) 
			
			if not os.path.exists(dir + fDate):
				os.makedirs(dir + fDate)
			
		outFile = '%s%s/%s_%s_%02d.pdf' % (dir, fDate, filePrefix, fDate, int(x[2]))
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
		outFilePdf = "%s%s/%s_%s.pdf" %(dir, fDate, prefixFile, fDate)
		log("Create %s" % (outFilePdf))
		for x in pageCount:
			outFile = '%s%s/%s_%s_%02d.pdf' % (dir, fDate, filePrefix, fDate, int(x[2]))
			inStream = file(outFile, 'rb')
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
				outStream = file(outFilePdf, 'wb')
				outPdf.write(outStream)
				inStream.close()
				outStream.close()
	
	if zip:
		zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
		log("Create %s" %(zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in pageCount:
			outFile = '%s%s/%s_%s_%02d.pdf' % (dir, fDate, filePrefix, fDate, int(x[2]))
			zip.write(outFile)
		zip.close()
		
	log("\n-")
		
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
	
def getMonth(month):
	dict = {'January': "01", 'February': "02", 'Marc': "03", 'April': "04", 'May': "05", 'June': "06", 'July': "07", 'August': "08", 'September': "09", 'October': "10", 'November': "11", 'December': "12"}
	return dict[month]

if __name__ == '__main__':
	main()