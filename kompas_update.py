#!/usr/bin/python

"""
__version__ = "$Revision: 0.6 $"
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
import optparse
import cookielib
import hashlib
import datetime

web = "kompas"

def main():
    cmd = optparse.OptionParser()
    cmd.add_option("-d", "--dir", dest="dir", default=web)
    cmd.add_option("-g", "--guid", dest="guid", default="BC6B3C21-64AD-42EE-9DFB-8F693395B92D")
    cmd.add_option("-p", "--prefix", dest="filePrefix", default=web)
    cmd.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
    cmd.add_option("-z", "--zip", action="store_true", dest="zip", default=False)
    (options, args) = cmd.parse_args()
    
    filePrefix = options.filePrefix
    zip = options.zip
    dir = os.path.normpath(options.dir) + '/'
    
    #proxy = urllib2.ProxyHandler({'http': 'www-proxy.com:8080'})
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
    
    listXML = re.compile('<span class="teaserText"><a href="([^"]+)">([^<]+)</a></span>').findall(html)
    if not listXML:
        log("xml=0")
        sys.exit(1)
        
    for xml in listXML:
        if xml[0] != mainPage:
            log(xml[0])
            page = opener.open(xml[0])
            html = page.read()

        stringPage = re.sub("\S+ Daily|Bagian ", "", xml[1]) 
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
    
        allIssue = re.compile('<BackIssue id="(\d+?)" sysname="[^"]+" name="[^"]+" path="([^"]+)" issuedate="([^"]+)" thumbnail="[^"]+"/>').findall(html)
        if not allIssue:
            log("issue=0")
            sys.exit(1)
        
        for item in allIssue:
            log(item[0])
            if iid[0] != item[0]:
                indexPage = "http://%s.realviewusa.com/global/loadconfig.aspx?fetch=2&i=&iguid=&xml&iid=%s&index=&rnd=0.1" % (web, item[0])
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
            Url = "http://content.%s.realviewusa.com/djvu%s" % (web, stringDir)
   
            if not os.path.exists(dir + fDate):
                os.makedirs(dir + fDate)

            year = datetime.datetime.utcnow().year
            month = datetime.datetime.utcnow().month
            day = datetime.datetime.utcnow().day
            hour = datetime.datetime.utcnow().hour
            sd = '/djvu' + stringDir.lower()  

            for x in range(1, int(pageCount[0]) + 1):
                s = "%07d" % (x)
                outFile = '%s%s/%s_%s%s_%s.jpg' % (dir, fDate, filePrefix, stringPage, fDate, s)
                if not os.path.exists(outFile):
                    log("Download %s" %(s))
                    j = "/webimages/page%07d_large.jpg" % (x)
                    n = "/webimages/page%07d_large.png" % (x)
                    jHash = "%s%s%s%s%s%s%s" % (options.guid, sd, j, year, month, day, hour)
                    nHash = "%s%s%s%s%s%s%s" % (options.guid, sd, n, year, month, day, hour)
                    jpgUrl = Url + j  + '?h=' + hashlib.md5(jHash).hexdigest()
                    pngUrl = Url + n  + '?h=' + hashlib.md5(nHash).hexdigest()
        
                    log(jpgUrl)
                    try:
                        jpg = opener.open(jpgUrl)
                        djpg = jpg.read()
                        imageStringJpg = cStringIO.StringIO(djpg)
                        imageStringJpg.seek(0)
                    except urllib2.HTTPError, e:
                        imageStringJpg = ''
                        log("Error %s" % (e))
                
                    log(pngUrl)
                    try:
                        png = opener.open(pngUrl)
                        dpng  = png.read()
                        imageStringPng = cStringIO.StringIO(dpng)
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
                        log(outFile)
                else:
                    log("Skip %s" % (outFile))
    
            if zip:
                zipFile = "%s%s_%s%s.zip" % (dir, filePrefix, stringPage, fDate)
                log("Create %s" % (zipFile)) 
                zip = zipfile.ZipFile(zipFile, mode="w", compression=8, allowZip64=True)
                for x in range(1, int(pageCount[0]) + 1):
                    s = "%07d" % (x)
                    outFile = '%s%s/%s_%s%s_%s.jpg' % (dir, fDate, filePrefix, stringPage, fDate, s)
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
