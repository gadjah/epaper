#!/usr/bin/python

import urllib2
import os
import sys
import zipfile
import re

ZIP = 1

def main():
    proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')]   

    mainPage = "http://epaper.balipost.com/epaper.php"
    log(mainPage)
    page = opener.open(mainPage)
    html = page.read()
   
    docId = regex = re.compile('documentId=([^&]+)').findall(html)
    if not docId:
        log("docId=0")
        sys.exit(1)
       
    pageCount = re.compile('<td align="center" >(.+?)<\/td>').findall(html)
    if not pageCount:
        log("pageCount=0")
        sys.exit(1)
   
    sDate = re.compile('docName=bp(\d+)').findall(html)
    if not sDate:
        log("Date=0")
        sys.exit(1)
       
    date = sDate[0][0:2]
    month = sDate[0][2:4]
    year = sDate[0][4:]
       
    fDate = "%s-%s-%s" %(year, month, date)
    Url = "http://image.issuu.com/%s/jpg/page_" % (docId[0])   
    if not os.path.exists(fDate):
        os.mkdir(fDate)
   
    counter = 0
   
    for x in pageCount:
        counter+=1
        outFile = '%s/balipost_%s_%s.jpg' % (fDate, fDate, counter)
        page = "%s.jpg" %(str(counter))
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
                    log("Skip %s" %(outFile))
                    pageUrl.close()
                    continue
       
        log("Download %s" %(outFile))           
        pdf = pageUrl.read()
       
        f = open(outFile, "w")
        f.write(pdf)
        f.close()
        pageUrl.close()
       
    if ZIP == 1:
        zipFile = 'balipost_' + fDate + '.zip'
        log("make %s" %(zipFile))
        zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True)
        for x in range(1, counter):
            outFile = '%s/balipost_%s_%s.jpg' % (fDate, fDate, str(x))
            zip.write(outFile)
        zip.close()
       
    log("\n-")
       
def log(str):
    print ">>> %s" %(str)
   
if __name__ == '__main__':
    main()

