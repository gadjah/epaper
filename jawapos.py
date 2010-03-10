#!/usr/bin/env python

"""
__version__ = "$Revision: 0.6 $"
__date__ = "$Date: 2009/05/28 $"
"""

import urllib2
import os
import sys
import re
import zipfile
import time
import optparse
import threading
import cookielib

web = "jawapos"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-s", "--sessid", dest="sessid", default="ts7o6c4binmhajgkt5hqbhhk63")
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
    opener.addheaders = [('User-Agent', 'Opera/9.25 (Windows NT 6.0; U; en)')]  
    mainPage = "http://virtual.%s.co.id/" % (web)
    log(mainPage)
    request = urllib2.Request(mainPage + 'virtual.php')
    cookie.set_cookie_if_ok(cookielib.Cookie(
        version=0, 
        name='PHPSESSID', 
        value='%s' % (options.sessid), 
        port=None, 
        port_specified=False, 
        domain='.virtual.%s.co.id' % (web), 
        domain_specified=True, 
        domain_initial_dot=True, 
        path='/', 
        path_specified=True, 
        secure=False, 
        expires=None, 
        discard=False, 
        comment=None, 
        comment_url=None, 
        rest={}, 
        rfc2109=False), 
    request) 
    page = opener.open(request)
    html = page.read()
    pageCount = re.compile("globalLastPage = (\d+)").findall(html)
    if not pageCount:
        log("pageCount=0")
        sys.exit(1)
    #yyyymmddd  
    sDate = re.compile('globalDate = "(\d+)"').findall(html) 
    fDate = "%s-%s-%s" %(sDate[0][0:4], sDate[0][4:6], sDate[0][-2:]) 
            
    if not os.path.exists(dir + fDate):
        os.makedirs(dir + fDate)

    threads = []
    s = threading.Semaphore(concurrent)
    for x in range(1, int(pageCount[0]) + 1):
        url = mainPage + "image.php?type=large&page=%s&date=%s" % (x, sDate[0])
        outFile = '%s%s/%s_%s_%02d.jpg' % (dir, fDate, filePrefix, fDate, x)
        threads.append(threading.Thread(target=downloader, args=(opener, url, outFile, s)))
        threads[-1].start()

    for thread in threads:
        thread.join()
        
    if zip:
        zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
        makezip(dir + fDate, zipFile)
        
    log("\n-")

def makezip(dir, filename):
    log("Create %s" % (filename)) 
    zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
    for jpg in os.listdir(dir):
        zip.write(dir + '/' + jpg)
    zip.close()


def downloader(opener, url, filename, s):
    s.acquire()
    try:
        log(url)
        page = opener.open(url)
        if os.path.exists(filename):
            if page.headers.getheader('Content-Length'):
                if long(page.headers.getheader('Content-Length')) == os.path.getsize(filename):
                    log("Skip %s" %(filename))
                    page.close()
                    return
                    
        log("Download %s" % (filename))         
        jpg = page.read()
        f = open(filename, "w")
        f.write(jpg)
        f.close()
        page.close()
    finally:
        s.release()

def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
    
if __name__ == '__main__':
    main()
