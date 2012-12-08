#!/usr/bin/env python

"""
__version__ = "$Revision: 0.7 $"
__date__ = "$Date: 2012/02/24 $"
"""

import urllib2
import urllib
import os
import sys
import zipfile
import re
import time
import optparse
import cookielib
import threading

web = "pikiran-rakyat"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
    cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
    cmd.add_option("-u", "--user", dest="user")
    cmd.add_option("-q", "--password", dest="password")
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
    user = options.user
    password = options.password

    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(), urllib2.HTTPCookieProcessor(cookie))   
    opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')] 
    
    mainPage = "http://epaper.%s.com" % (web)
    log(mainPage)
    page = opener.open(mainPage)
    html = page.read()
    
    hidden = re.compile('<input type="hidden" name="([^"]+)" value="([^"]+)" />').findall(html)
    login = {}
    login["username"] = user
    login["passwd"] = password
    login["Submit"] = "Login"
    login["remember"] = "yes"
    
    for item in hidden:
        login[item[0]] = item[1]
        
    loginPage = "http://epaper.%s.com/index.php/component/user/" % (web)
    data = urllib.urlencode(login)
    page = opener.open(loginPage, data)
    html = page.read()

    #pageCount = re.compile('/images/flippingbook/PR/(\d+)/(\w+)/(\d+)/\d+_zoom_(\d+).jpg').findall(html)
    pageCount = re.compile('/images/flippingbook/PR/(\d+)/([^\/]+)/(\d+)/\d+_zoom_(\d+).jpg').findall(html)
    if not pageCount:
        log("pageCount=0")
        sys.exit(1)
    
    date = pageCount[0][2][0:2]
    #month = getMonth(pageCount[0][1].capitalize())
    month = getMonth((pageCount[0][1]).split()[0].capitalize())
    year = pageCount[0][0]
        
    fDate = "%s-%s-%s" %(year, month, date)
    Url = "http://epaper.%s.com/images/flippingbook/PR/" % (web)
    
    if not os.path.exists(dir + fDate):
        os.makedirs(dir + fDate)
    
    threads = []
    s = threading.Semaphore(concurrent)
    for x in pageCount:
        #x = '(2009', 'Mei', '030509', '01')
        outFile = '%s%s/%s_%s_%s.jpg' % (dir, fDate, filePrefix, fDate, x[3])
        page = "%s/%s/%s/%s_zoom_%s.jpg" % (x[0], x[1], x[2], x[2], x[3])
        pageUrl = Url + urllib.quote(page)
        threads.append(threading.Thread(target=downloader, args=(opener, pageUrl, outFile, s)))
        threads[-1].start()
        
    for thread in threads:
        thread.join()

    if zip:
        zipFile = "%s%s_%s.zip" % (dir, filePrefix, fDate)
        makezip(dir + fDate, zipFile)       
    log("\n-")

def downloader(opener, url, filename, s):
    s.acquire()
    try:
        page = opener.open(url)
        if os.path.exists(filename):
            if page.headers.getheader('Content-Length'):
                if long(page.headers.getheader('Content-Length')) == os.path.getsize(filename):
                    log("Skip %s" % (filename))
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
        
def makezip(dir, filename):
    log("Create %s" % (filename)) 
    zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
    for image in os.listdir(dir):
        zip.write(dir + '/' + image)
    zip.close()

def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
    
def getMonth(month):
    dict = {'Januari': "01", 'Februari': "02", 'Maret': "03", 'April': "04", 'Mei': "05", 'Juni': "06", 'Juli': "07", 'Agustus': "08", 'September': "09", 'Oktober': "10", 'November': "11", 'Desember': "12"}
    return dict[month]

if __name__ == '__main__':
    main()
