#!/usr/bin/env python

"""
__version__ = "$Revision: 0.7 $"
__date__ = "$Date: 2011/11/24 $"
"""

import urllib
import urllib2
import os
import sys
import zipfile
import re
import time
import optparse
import pyPdf
import cookielib
import threading

web = "mediaindonesia"
domain = "pmlseaepaper.pressmart.com"
webpath = "MediaIndonesia"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-n", "--no-merge", action="store_false", dest="merge", default=True)
    cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
    cmd.add_option("-q", "--password", dest="password")
    cmd.add_option("-u", "--user", dest="user")
    cmd.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
    cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
    (options, args) = cmd.parse_args()

    if not (options.user and options.password):
        print "incorrect username or password"
        sys.exit(1)
    if options.concurrent < 1 or options.concurrent > 10:
        concurrent = 1
    else:
        concurrent = options.concurrent
    filePrefix = options.filePrefix
    zip = options.zip
    dir = os.path.normpath(options.dir) + '/'
    m = options.merge
    user = options.user
    password = options.password

    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(), \
        urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler(debuglevel=options.verbose))   
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:6.0.2) Gecko/20100101 Firefox/6.0.2')] 

    mainPage = "http://%s/%s" % (domain, web)
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

    data = 'strEmail=%s\r\nstrPassword=%s' % (user, password) 
    loginPage = 'http://%s/%s/ajax/EpaperLibrary.AjaxUtilsMethods,EpaperLibrary.ashx?_method=CheckLoginCredentialsNew&_session=rw' % (domain, webpath)
    request = urllib2.Request(loginPage, data)
    page = opener.open(request)
    html = page.read()
    if not 'success' in html:
        print "incorrect username or password"
        sys.exit(1)
       
    fDate = "%s-%s-%s" %(year, month, date)
    Url = "http://%s/%s/PUBLICATIONS/MI/MI/%s/%s/%s/PagePrint/" % (domain, web, year, month, date)
    
    if not os.path.exists(dir + fDate):
        os.makedirs(dir + fDate)
    
    threads = []
    s = threading.Semaphore(concurrent)
    for x in range(0, len(pageCount)):
        outFile = '%s%s/%s_%s_%s.pdf' % (dir, fDate, filePrefix, fDate, pageCount[x][11:14])
        page = "%s.pdf" % (pageCount[x][0:14])
        pageUrl = Url + page
        threads.append(threading.Thread(target=downloader, args=(opener, pageUrl, outFile, s)))
        threads[-1].start()

    for thread in threads:
        thread.join()
        
    if m:
        filePdf = "%s%s_%s.pdf" % (dir, filePrefix, fDate)
        merge(dir + fDate, filePdf)
                
    if zip:
        zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
        makezip(dir + fDate, zipFile)
        
    log("\n-")

def downloader(opener, url, filename, s):
    s.acquire()
    try:
        page = opener.open(url)
        if os.path.exists(filename):
            #content-length
            if page.headers.items()[0][1].isdigit():
                if long(page.headers.items()[0][1]) == os.path.getsize(filename):
                    log("Skip %s" % (filename))
                    return
        log("Download %s" % (filename))         
        pdf = page.read()
        f = open(filename, "w")
        f.write(pdf)
        f.close()
        page.close()
    finally:
        s.release()
    
def merge(dir, filename):
    outPdf = pyPdf.PdfFileWriter()
    log("Create %s" % (filename))
    for pdf in os.listdir(dir):
        inStream = file(dir + '/' + pdf, 'rb')
        inPdf = pyPdf.PdfFileReader(inStream)
        if not inPdf.getIsEncrypted():
            for numPage in range(0, inPdf.numPages):
                outPdf.addPage(inPdf.getPage(numPage))
            outStream = file(filename, 'wb')
            outPdf.write(outStream)
            inStream.close()
            outStream.close()

def makezip(dir, filename):
    log("Create %s" % (filename)) 
    zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
    for pdf in os.listdir(dir):
        zip.write(dir + '/' + pdf)
    zip.close()
        
def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
    
if __name__ == '__main__':

    main()
