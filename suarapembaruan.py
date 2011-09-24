#!/usr/bin/env python

"""
__version__ = "$Revision: 0.6 $"
__date__ = "$Date: 2009/05/28 $"
"""

from PIL import Image
import urllib2
import cStringIO
import os
import sys
import zipfile
import re
import time
import optparse
import cookielib
import threading

web = "suarapembaruan"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
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

    cookie = cookielib.CookieJar()  
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), 
        urllib2.HTTPHandler(debuglevel=options.verbose))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:6.0.2) Gecko/20100101 Firefox/6.0.2')] 
    mainPage = "http://epaper.%s.com" % (web)
    log(mainPage)
    page = opener.open(mainPage)
    html = page.read()
        
    iid = re.compile('iid:([^,]+)').findall(html)
    if not iid:
        log("iid=0")
        sys.exit(1)
        
    pid = re.compile('pid:(\d+)').findall(html)[0]
    xmlConfig= re.compile("""xml_config:'([^']+)'""").findall(html)[0]
    indexFile = re.compile("""index_file = '([^']+)'""").findall(html)[0]
    
    dDate = re.compile("i:'([^']+)'").findall(html)
    if not dDate:
        log("date=0")
        sys.exit(1) 
        
    fDate = "%s-%s-%s" %(dDate[0][-4:], str(getMonth(dDate[0][-8:-5])), dDate[0][0:2])
    indexPage = "http://epaper.%s.com/global/loadconfig.aspx?pid=%s&fetch=2&i=&iguid=&xml=%s&iid=%s&index=%s&rnd=0.8661077903742714" % (web, pid, xmlConfig, iid[0], indexFile) 
    log(indexPage)
    page = opener.open(indexPage)
    html = page.read()
    pageCount = re.compile('pagecount="(\d+)"').findall(html)

    if not pageCount:
        log("pageCount=0")
        sys.exit(1) 
        
    stringDir = re.compile('path="([^"]+)"').findall(html)
        
    if not stringDir:
        log("Dir=0")
        sys.exit(1)
            
    Dir = re.sub("\s", '%20', stringDir[0])
    Url = "http://epaper.%s.com/djvu%s" % (web, Dir)
    
    if not os.path.exists(dir + fDate):
        os.makedirs(dir + fDate)
        
    threads = []
    s = threading.Semaphore(concurrent)
    for x in range(1, int(pageCount[0]) + 1):
        outFile = '%s%s/%s_%s_%07d.jpg' % (dir, fDate, filePrefix, fDate, x)
        imageJPG = Url + "/webimages/page%07d_large.jpg" % (x)
        imagePNG = Url + "/webimages/page%07d_large.png" % (x)
        threads.append(threading.Thread(target=downloader, args=(opener, outFile, s, imageJPG, imagePNG)))
        threads[-1].start()
            
    for thread in threads:
        thread.join()
            
    if zip:
        zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
        makezip(dir, fDate, filePrefix, zipFile, xrange(1, int(pageCount[0]) + 1))

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
                log("Error %s" % (e))
            
            try:
                page = opener.open(png)
                dPNG = page.read()
                imageStringPNG = cStringIO.StringIO(dPNG)
                imageStringPNG.seek(0)
                page.close()
            except urllib2.HTTPError, e:
                imageStringPNG = ""
                log("Error %s" % (e))
                
            if imageStringJPG and imageStringPNG:
                imageJPG = Image.open(imageStringJPG)
                imagePNG = Image.open(imageStringPNG)
                A = imagePNG.convert('RGBA').split()[-1]
                imageComposite = Image.composite(imagePNG, imageJPG, A)
                imageComposite.save(filename, quality=100)
                imageStringJPG.close()
                imageStringPNG.close()
        else:
            log("Skip %s" % (filename))
    finally:
        s.release()
        
def makezip(dir, fDate, filePrefix, filename, pageCount):
    log("Create %s" % (filename)) 
    zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
    for item in pageCount:
        outFile = '%s%s/%s_%s_%07d.jpg' % (dir, fDate, filePrefix, fDate, item)
        zip.write(outFile)
    zip.close()
        
def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
    
def getMonth(month):
    dict = {'Jan': "01", 'Feb': "02", 'Mar': "03", 'Apr': "04", 'May': "05", 'Jun': "06", 'Jul': "07", 'Aug': "08", 'Sep': "09", 'Oct': "10", 'Nov': "11", 'Dec': "12"}
    return dict[month]
    
if __name__ == '__main__':
    main()
