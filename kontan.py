#!/usr/bin/env python

"""
__version__ = "$Revision: 0.7 $"
__date__ = "$Date: 2010/02/24 $"
"""

from PIL import Image
import urllib2
import cStringIO
import os
import sys
import zipfile
import re
import time
import datetime
import cookielib
import hashlib
import optparse
import threading

web = "kontan"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-g", "--guid", dest="guid", default="887B60F2-76AC-4FD0-983F-260943FA5E6A")
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
    opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)')] 
    mainPage = "http://%s.realviewusa.com/?xml=%s.xml" % (web, web)
    log(mainPage)
    request = urllib2.Request(mainPage)
    cookie.set_cookie_if_ok(cookielib.Cookie(
        version=0, 
        name='RVKernel.User.UserGUID', 
        value='%s' % (options.guid), 
        port=None, port_specified=False, 
        domain='.%s.realviewusa.com' % (web), 
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
    xml = re.compile("""contentCode = DoGetContent\(([^,]+),([^,]+),([^\)]+)\)""").findall(html)    
    for item in xml:
        indexPage = "http://%s.realviewusa.com/?xml=%s.xml" % (web, item[1].strip('\'"'))
        if indexPage != mainPage:
            log(indexPage)
            page = opener.open(indexPage)
            html = page.read()

        stringPage = re.sub(web.title() + " |\S+ Daily|Bagian |'|\"", "", item[2]) 
        if stringPage:
            stringPage = re.sub("\s", "_", stringPage).lower() + "_"
        iid = re.compile('iid:([^,]+)').findall(html)
        if not iid:
            log("iid=0")
            sys.exit(1)
        
        dDate = re.compile("i:'([^']+)'").findall(html)
        if not dDate:
            log("date=0")
            sys.exit(1)     
        if '-' in dDate[0]:
            fDate = "%s-%s-%s" % (dDate[0][-4:], str(getMonth(dDate[0][-8:-5])), dDate[0][0:2])
        else:
            fDate = "%s-%s-%s" % (dDate[0].split()[2], getMonth(dDate[0].split()[1]), getMonth(dDate[0].split()[0]))
        indexPage = "http://%s.realviewusa.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (web, iid[0])
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
        Url = "http://content.%s.realviewusa.com/djvu%s" % (web, Dir)
    
        if not os.path.exists(dir + fDate):
            os.makedirs(dir + fDate)
        year = datetime.datetime.utcnow().year
        month = datetime.datetime.utcnow().month
        day = datetime.datetime.utcnow().day
        hour = datetime.datetime.utcnow().hour
        sd = '/djvu' + stringDir[0].lower()  
        threads = []
        s = threading.Semaphore(concurrent)
        for x in range(1, int(pageCount[0]) + 1):
            outFile = '%s%s/%s_%s%s_%07d.jpg' % (dir, fDate, filePrefix, stringPage, fDate, x)
            j = "/webimages/page%07d_large.jpg" % (x)
            n = "/webimages/page%07d_large.png" % (x)
            jHash = "%s%s%s%s%s%s%s" % (options.guid, sd, j, year, month, day, hour)
            nHash = "%s%s%s%s%s%s%s" % (options.guid, sd, n, year, month, day, hour)
            imageJPG = Url + j  + '?h=' + hashlib.md5(jHash).hexdigest()
            imagePNG = Url + n  + '?h=' + hashlib.md5(nHash).hexdigest()
            threads.append(threading.Thread(target=downloader, args=(opener, outFile, s, imageJPG, imagePNG)))
            threads[-1].start()
            
        for thread in threads:
            thread.join()
            
        if zip:
            zipFile = "%s%s_%s%s.zip" % (dir, filePrefix, stringPage, fDate)
            makezip(dir, fDate, filePrefix, stringPage, zipFile, xrange(1, int(pageCount[0]) + 1))

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
                imageJPG.paste(imagePNG, A)
                imageJPG.save(filename)
                imageStringJPG.close()
                imageStringPNG.close()
        else:
            log("Skip %s" % (filename))
    finally:
        s.release()
        
def makezip(dir, fDate, filePrefix, stringPage, filename, pageCount):
    log("Create %s" % (filename)) 
    zip = zipfile.ZipFile(filename, mode="w", compression=zipfile.ZIP_DEFLATED) 
    for item in pageCount:
        outFile = '%s%s/%s_%s%s_%07d.jpg' % (dir, fDate, filePrefix, stringPage, fDate, item)
        zip.write(outFile)
    zip.close()
        
def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
    
def getMonth(month):
    dict = {'Jan': "01", 'Feb': "02", 'Mar': "03", 'Apr': "04", 'May': "05", 'Jun': "06", 
            'Jul': "07", 'Aug': "08", 'Sep': "09", 'Oct': "10", 'Nov': "11", 'Dec': "12", 
            'January': "01", 'February': "02", 'March': "03", 'April': "04", 'May': "05", 
            'June': "06", 'July': "07", 'August': "08", 'September': "09", 'October': "10",
            'November': "11", 'December': "12"}
    return dict[month]
    
if __name__ == '__main__':
    main()
