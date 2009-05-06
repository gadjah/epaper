#!/usr/bin/python

"""
__version__ = "$Revision: 0.4 $"
__date__ = "$Date: 2009/05/03 $"
"""

import urllib2
import os
import sys
import re
import zipfile

ZIP = 1
MERGE = 1
prefix = "jawapos"

def main():
	#proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	

	mainPage = "http://versipdf.%s.co.id/" % (prefix)
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
		
	sDate = re.compile('<font class="ftgl"  >\w+, (\d+) (\w+) (\d+)<\/font>').findall(html)
	if not sDate:
		log("date=0")
		sys.exit(1)
	
	date = sDate[0][0]
	month = getMonth(sDate[0][1])
	year = sDate[0][2]
		
	fDate = "%s-%s-%s" %(year, month, date)
	
	if not os.path.exists(fDate):
		os.mkdir(fDate)
	
	for x in pageCount:
		indexFile = pageDict[x[0][-2:]]
		Url = "http://versipdf.%s.co.id/%s%s" % (prefix, indexFile, x[1])
		outFile = '%s/%s_%s_%02d.pdf' % (fDate, prefix, fDate, int(x[2]))
		log(Url)
		pageUrl = opener.open(Url)
		
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
			outFile = '%s/%s_%s_%02d.pdf' % (fDate, prefix, fDate, int(x[2]))
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
	
	if ZIP == 1:
		zipFile = "%s_%s.zip" % (prefix, fDate)
		log("Create %s" %(zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in pageCount:
			outFile = '%s/%s_%s_%02d.pdf' % (fDate, prefix, fDate, int(x[2]))
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