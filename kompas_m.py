#!/usr/bin/env python

"""
__version__ = "$Revision: 0.7 $"
__date__ = "$Date: 2010/02/24 $"
"""

from PIL import Image
import os
import sys
import re
import time
import hashlib
import zipfile
import urllib2
import datetime
import optparse
import cStringIO
import cookielib
import multiprocessing

web = "kompas"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-c", "--concurrent", dest="concurrent", type="int", default=1)
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-g", "--guid", dest="guid", default="BC6B3C21-64AD-42EE-9DFB-8F693395B92D")
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
    computerID = ''
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
        port=None, 
        port_specified=False, 
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
    for ck in cookie:
        if ck.name == 'computerid':
            computerID = ck.value
    html = page.read()
    xml = re.compile('<span class="teaserText"><a href="([^"]+)">([^<]+)</a></span>').findall(html)
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
        
        dDate = re.compile("i:'([^']+)'").findall(html)
        if not dDate:
            log("date=0")
            sys.exit(1)     
        
        fDate = "%s-%s-%s" %(dDate[0][-4:], str(getMonth(dDate[0][-8:-5])), dDate[0][0:2])
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
        processes = []
        s = multiprocessing.Semaphore(concurrent)
        s = multiprocessing.Semaphore(concurrent)
        for x in range(1, int(pageCount[0]) + 1):
            outFile = '%s%s/%s_%s%s_%07d.jpg' % (dir, fDate, filePrefix, stringPage, fDate, x)  
            j = "/webimages/page%07d_large.jpg" % (x)
            n = "/webimages/page%07d_large.png" % (x)
            jHash = "%s%s%s%s%s%s%s" % (computerID, sd, j, year, month, day, hour)
            nHash = "%s%s%s%s%s%s%s" % (computerID, sd, n, year, month, day, hour)
            imageJPG = Url + j  + '?h=' + hashlib.md5(jHash).hexdigest()
            imagePNG = Url + n  + '?h=' + hashlib.md5(nHash).hexdigest()
            processes.append(multiprocessing.Process(target=downloader, args=(opener, outFile, s, imageJPG, imagePNG)))
            processes[-1].start()
            
        for process in processes:
            process.join()
            
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
                imageComposite.save(filename)
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
        try:
            zip.write(outFile)
        except OSError, e:
            log("Error %s, %s" % (e, filename))
    zip.close()
        
def log(str):
    print "%s >>> %s" % (time.strftime("%x - %X", time.localtime()), str)
    
def getMonth(month):
    dict = {'Jan': "01", 'Feb': "02", 'Mar': "03", 'Apr': "04", 'May': "05", 'Jun': "06", 'Jul': "07", 'Aug': "08", 'Sep': "09", 'Oct': "10", 'Nov': "11", 'Dec': "12"}
    return dict[month]
    
if __name__ == '__main__':
    main()
