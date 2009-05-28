#!/usr/bin/python

"""
__version__ = "$Revision: 0.5 $"
__date__ = "$Date: 2009/05/19 $"
"""

from PIL import Image
import urllib2
import StringIO
import os
import sys
import zipfile
import re
import time
import optparse

web = "suarapembaruan"

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

	mainPage = "http://epaper.%s.com" % (web)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	iid = re.compile('iid:([^,]+)').findall(html)
	if not iid:
		log("iid=0")
		sys.exit(1)
		
	dDate = re.compile("i:'([^']+)'").findall(html)
	if not dDate:
		log("date=0")
		sys.exit(1)		
		
	fDate = "%s-%s-%s" %(dDate[0][-4:], str(getMonth(dDate[0][-8:-5])), dDate[0][0:2])
	
	indexPage = "http://epaper.%s.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (web, iid[0])
	log(indexPage)

	page = opener.open(indexPage)
	html = page.read()
	pageCount = re.compile('pagecount="(\d+)"').findall(html)
	if not pageCount:
		log("pageCount=0")
		sys.exit(1)
		
	path = re.compile('path="([^"]+)"').findall(html)[0].replace(' ', '%20')
	
	if not path:
		log("path=None")
		sys.exit(1)
		
	Url = "http://content.epaper.%s.com/djvu/%s" % (web, path)
	
	if not os.path.exists(dir + fDate):
		os.makedirs(dir + fDate)
	
	for x in range(1, int(pageCount[0]) + 1):
		s = ("000000" + str(x))[-7:]
		outFile = '%s%s/%s_%s_%s.jpg' % (dir, fDate, filePrefix, fDate, s)
		if not os.path.exists(outFile):
			log("Download %s" %(s))
			jpg = "page%s_large.jpg" %(s)
			png = "page%s_large.png" %(s)
		
			jpgUrl = Url + "/webimages/" + jpg
			log(jpgUrl)
			
			try:
				jpg = opener.open(jpgUrl)
				djpg = jpg.read()
				imageStringJpg = StringIO.StringIO(djpg)
			except urllib2.HTTPError, e:
				imageStringJpg = ''
				log("Error %s" % (e))
				
			pngUrl = Url + "/webimages/" + png
			log(pngUrl)
			
			try:
				png = opener.open(pngUrl)
				dpng  = png.read()
				imageStringPng = StringIO.StringIO(dpng)
			except urllib2.HTTPError, e:
				imageStringPng = ''
				log("Error %s" % (e))
			
			if imageStringPng and imageStringJpg:
				imageJpg = Image.open(imageStringJpg)
				imagePng = Image.open(imageStringPng)
				R, G, B, A = imagePng.convert('RGBA').split()
				image = Image.composite(imagePng, imageJpg, A)
				image.save(outFile)
				imageStringJpg.close()
				imageStringPng.close()
				jpg.close()
				png.close()
				log(outFile)
		else:
			log("Skip %s" % (outFile))
	
	if zip:
		zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
		log("Create %s" %(zipFile)) 
		zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True) 
		for x in range(1, int(pageCount[0]) + 1):
			s = ("000000" + str(x))[-7:]
			outFile = '%s%s/%s_%s_%s.jpg' % (dir, fDate, filePrefix, fDate, s)
			try:
				zip.write(outFile)
			except OSError, e:
				log(e)			
		zip.close()
		
	log("\n-")
		
def log(str):
	print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
	
def getMonth(month):
	dict = {'Jan': "01", 'Feb': "02", 'Mar': "03", 'Apr': "04", 'May': "05", 'Jun': "06", 'Jul': "07", 'Aug': "08", 'Sep': "09", 'Oct': "10", 'Nov': "11", 'Dec': "12"}
	return dict[month]
	
if __name__ == '__main__':
	main()