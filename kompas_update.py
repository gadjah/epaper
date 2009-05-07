#!/usr/bin/python

"""
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2009/05/04 $"
"""

from PIL import Image
import urllib2
import StringIO
import os
import sys
import zipfile
import re
import time

ZIP = 1
prefix = "kompas"

def main():
	#proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
	opener = urllib2.build_opener()
	opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]	
	mainPage = "http://%s.realviewusa.com/?xml=%s.xml" % (prefix, prefix)
	log(mainPage)
	page = opener.open(mainPage)
	html = page.read()
	
	listXML = re.compile('<span class="teaserText"><a href="([^"]+)">([^<]+)</a></span>').findall(html)
	if not listXML:
		log("xml=0")
		sys.exit(1)
		
	for xml in listXML:
		if xml[0] != mainPage:
			log(xml[0])
			page = opener.open(xml[0])
			html = page.read()

		stringPage = re.sub("Kompas Daily|Bagian ", "", xml[1]) 
		if stringPage:
			stringPage = re.sub("\s", "_", stringPage).lower() + "_"
			
		iid = re.compile('iid:([^,]+)').findall(html)
		if not iid:
			log("iid=0")
			sys.exit(1)
	
		indexPage = "http://%s.realviewusa.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (prefix, iid[0])
		log(indexPage)
		page = opener.open(indexPage)
		html = page.read()
	
		allIssue = re.compile('<BackIssue id="(\d+?)" sysname="[^"]+" name="[^"]+" path="([^"]+)" issuedate="([^"]+)" thumbnail="[^"]+"/>').findall(html)
		if not allIssue:
			log("issue=0")
			sys.exit(1)
		
		for item in allIssue:
			log(item[0])
			if iid[0] != item[0]:
				indexPage = "http://%s.realviewusa.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (prefix, item[0])
				log(indexPage)
				page = opener.open(indexPage)
				html = page.read()

			dDate = re.compile('(\w{3})\s+?(\d{1,2})\s+?(\d{4})').findall(item[2])
			if not dDate:
				log("date=0")
				sys.exit(1)		
		
			fDate = "%s-%s-%02d" %(dDate[0][2], getMonth(dDate[0][0]), int(dDate[0][1]))
			pageCount = re.compile('pagecount="(\d+)"').findall(html)
		
			if not pageCount:
				log("pageCount=0")
				sys.exit(1)	
		
			stringDir = item[1].replace(' ', '%20')
			Url = "http://content.%s.realviewusa.com/djvu%s" % (prefix, stringDir)
	
			if not os.path.exists(fDate):
				os.mkdir(fDate)
	
			for x in range(1, int(pageCount[0]) + 1):
				s = "%07d" % (x)
				outFile = '%s/%s_%s%s_%s.jpg' % (fDate, prefix, stringPage, fDate, s)
			
				if not os.path.exists(outFile):
					log("Download %s" %(s))
					jpg = "page%s_large.jpg" % (s)
					png = "page%s_large.png" % (s)
		
					jpgUrl = Url + "/webimages/" + jpg
					log(jpgUrl)
			
					try:
						jpg = opener.open(jpgUrl)
						djpg = jpg.read()
						imageStringJpg = StringIO.StringIO(djpg)
						imageStringJpg.seek(0)
					except urllib2.HTTPError, e:
						imageStringJpg = ''
						log("Error %s" % (e))
				
					pngUrl = Url + "/webimages/" + png
					log(pngUrl)
			
					try:
						png = opener.open(pngUrl)
						dpng  = png.read()
						imageStringPng = StringIO.StringIO(dpng)
						imageStringPng.seek(0)
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
				else:
					log("Skip %s" % (outFile))
	
			if ZIP == 1:
				zipFile = "%s_%s.zip" % (prefix, fDate)
				log("Create %s" % (zipFile)) 
				zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True)
				for x in range(1, int(pageCount[0]) + 1):
					s = "%07d" % (x)
					outFile = '%s/%s_%s%s_%s.jpg' % (fDate, prefix, stringPage, fDate, s)
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