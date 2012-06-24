#!/usr/bin/env python

"""
__version__ = "$Revision: 0.8 $"
__date__ = "$Date: 2012/06/24 $"
"""

from PIL import Image
from datetime import datetime
import os
import sys
import re
import time
import hashlib
import zipfile
import urllib2
import optparse
import cStringIO
import cookielib
import threading

web = "kompas"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
    cmd.add_option("-s", "--date", dest="sdate", default="", help="YYYY-MM-DD")
    cmd.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
    cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
    (options, args) = cmd.parse_args()

    if options.concurrent < 1 or options.concurrent > 10:
        concurrent = 1
    else:
        concurrent = options.concurrent
    filePrefix = options.filePrefix
    zip = options.zip
    dir = os.path.normpath(options.dir) + '/'
    computerID = ''
    sdate = None

    if options.sdate:
        try: 
            sdate = datetime.strptime(options.sdate,
                   '%Y-%m-%d')
        except ValueError:
            log("Date does not match format YYYY-MM-DD")
            sys.exit(1) 

    cookie = cookielib.CookieJar() 
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), 
        urllib2.HTTPHandler(debuglevel=options.verbose))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:6.0.2) Gecko/20100101 Firefox/6.0.2')] 
    mainPage = "http://%s.realviewusa.com/?xml=%s.xml" % (web, web)
    log(mainPage)
    page = opener.open(mainPage)

    for ck in cookie:
        if ck.name == 'computerid':
            computerID = ck.value

    html = page.read()
    xml = re.compile('<span class="teaserText"><a href="([^"]+)">([^<]+)</a></span>').findall(html)
    #?!/
    del(xml[1:])
    for item in xml:
        if item[0] != mainPage:
            log(item[0])
            page = opener.open(item[0])
            html = page.read()

        stringPage = re.sub("\S+ Daily|Bagian ", "", item[1]) 
        if stringPage:
            stringPage = re.sub("\s", "_", stringPage).lower() + "_"
            
        iid = re.compile('iid:([^,]+)').findall(html)
        if not iid:
            log("iid=0")
            sys.exit(1)

        indexPage = "http://%s.realviewusa.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (web, iid[0])
        log(indexPage)
        page = opener.open(indexPage)
        html = page.read()
        
        ss = re.findall('<BackIssue id="([^"]+)" sysname="([^"]+)" name="([^"]+)" path="([^"]+)" issuedate="([^"]+)', html)
        if sdate:
            iid = [] 
            for s in ss:
                if datetime.strptime(re.sub("\s{2,}", " ", s[4]), "%b %d %Y %H:%MAM").strftime("%Y-%m-%d") == sdate.strftime("%Y-%m-%d"): 
                    iid.append(s[0])
                    break
            if not iid:
                log("Date does not match")
                sys.exit(1)
            indexPage = "http://%s.realviewusa.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (web, iid[0])
            page = opener.open(indexPage)
            html = page.read()
        else:
            s = ss[0]
        fdate =  datetime.strptime(s[4][7:11]+s[4][0:3]+("00" + s[4][4:6].strip())[-2:], "%Y%b%d").strftime("%Y-%m-%d")
        stringDir = s[3]

        pageCount = re.compile('pagecount="(\d+)"').findall(html)
        if not pageCount:
            log("pageCount=0")
            sys.exit(1) 

        Dir = re.sub("\s", '%20', stringDir)
        Url = "http://content.%s.realviewusa.com/djvu%s" % (web, Dir)
        if not os.path.exists(dir + fdate):
            os.makedirs(dir + fdate)
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        day = datetime.utcnow().day
        hour = datetime.utcnow().hour
        sd = '/djvu' + stringDir.lower()  
        threads = []
        s = threading.Semaphore(concurrent)
        for x in range(1, int(pageCount[0]) + 1):
            outFile = '%s%s/%s_%s%s_%07d.jpg' % (dir, fdate, filePrefix, stringPage, fdate, x)  
            j = "/webimages/page%07d_large.jpg" % (x)
            n = "/webimages/page%07d_large.png" % (x)
            jHash = "%s%s%s%s%s%s%s" % (computerID, sd, j, year, month, day, hour)
            nHash = "%s%s%s%s%s%s%s" % (computerID, sd, n, year, month, day, hour)
            imageJPG = Url + j  + '?h=' + hashlib.md5(jHash).hexdigest()
            imagePNG = Url + n  + '?h=' + hashlib.md5(nHash).hexdigest()
            threads.append(threading.Thread(target=downloader, args=(opener, outFile, s, imageJPG, imagePNG)))
            threads[-1].start()
            
        for thread in threads:
            thread.join()
            
        if zip:
            zipFile = "%s%s_%s%s.zip" % (dir, filePrefix, stringPage, fdate)
            makezip(dir, fdate, filePrefix, stringPage, zipFile, xrange(1, int(pageCount[0]) + 1))

    log("\n-")
    
def downloader(opener, filename, s, jpg=None, png=None):
    s.acquire()
    try:
        if not os.path.exists(filename):
            log("Download %s" % (filename))
            try:
                page = opener.open(jpg)
                dJPG = page.read()
                imageStringJPG = cStringIO.StringIO(dJPG)
                imageStringJPG.seek(0)
                page.close()
            except urllib2.HTTPError, e:
                imageStringJPG = ""
                log("Error %s, %s" % (e, jpg.split('/')[-1]))
            
            try:
                page = opener.open(png)
                dPNG = page.read()
                imageStringPNG = cStringIO.StringIO(dPNG)
                imageStringPNG.seek(0)
                page.close()
            except urllib2.HTTPError, e:
                imageStringPNG = ""
                log("Error %s, %s" % (e, png.split('/')[-1]))
                
            if imageStringJPG and imageStringPNG:
                imageJPG = Image.open(imageStringJPG)
                imagePNG = Image.open(imageStringPNG)
                A = imagePNG.convert('RGBA').split()[-1]
                imageComposite = Image.composite(imagePNG, imageJPG, A)
                imageComposite.save(filename, quality=100)
                imageStringJPG.close()
                imageStringPNG.close()
        else:
            #log("Skip %s" % (filename))
            pass
    finally:
        s.release()
        
def makezip(dir, fdate, filePrefix, stringPage, filename, pageCount):
    log("Create %s" % (filename)) 
    zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
    for item in pageCount:
        outFile = '%s%s/%s_%s%s_%07d.jpg' % (dir, fdate, filePrefix, stringPage, fdate, item)
        try:
            zip.write(outFile)
        except OSError, e:
            log("Error %s, %s" % (e, filename))
    zip.close()

def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)


    
if __name__ == '__main__':
    main()
