# -*- coding: utf-8
import sys,os,types,pycurl,StringIO,random,re,copy,urllib
 
 

class downHtml:

    def __init__(self):
        self.REFERER=False
        self.USERAGENT="Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36"
        self.CONNECTTIMEOUT=150
        self.TIMEOUT=360
        self.HEADER=False
        self.COOKIE=False
        self.title=False
        self.POST=False
        self.DATA=False
        self.HTTPAUTH=False   
        self.HEADERCONTENT=False
        self.FILETYPE='text/html'  
        self.DAILI={}
        self.downed={}
        self.DownLoad=False
        self.bh=StringIO.StringIO()
 
    def headerw(self,buf):
        self.bh.truncate()
        self.bh.write(str(buf))
    def replace(self,ReString,ArrList,StrCode=False):
    
        if len(ReString)==0:
            return ''
        ReString=ReString.strip()
        if len(ArrList)==0:
            return ReString
        
        if len(ArrList)==2:
            if 'str' in str(type(ArrList[0])) and 'str' in str(type(ArrList[1])):
    
                r=re.compile(ArrList[0],re.I|re.S|re.M)
                return r.sub(ArrList[1],ReString)
                
        for i in ArrList:
    
            r=re.compile(i[0],re.I|re.S|re.M)
            ReString=r.sub(i[1],ReString)
    
        return ReString
    
    def curl(self,url,errnum=0):
        self.header=False
        
 
 
        c = pycurl.Curl()
        self.bh.truncate()
        c.setopt(pycurl.URL, url)    
     
 
        if self.DAILI.has_key('ADD') and self.DAILI.has_key('PWD'):
            c.setopt(pycurl.PROXY,self.DAILI['ADD'])
            c.setopt(pycurl.PROXYUSERPWD,self.DAILI['PWD'])
        c.setopt(pycurl.HEADERFUNCTION, self.headerw)
        c.setopt(pycurl.HTTPHEADER, ["Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"])
        if self.DownLoad:
            b=file(self.DownLoad, 'wb')
            
        else:
            b = StringIO.StringIO()
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        
        if self.HTTPAUTH:
            c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
            c.setopt(pycurl.USERPWD, self.HTTPAUTH)  
     
        c.setopt(pycurl.SSL_VERIFYPEER, 0)   
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        
        c.setopt(pycurl.ENCODING, "gzip,deflate,sdch")
        c.setopt(pycurl.NOSIGNAL, 1)
     
        c.setopt(pycurl.USERAGENT, self.USERAGENT)
        if self.REFERER:
            c.setopt(pycurl.REFERER, self.REFERER)   
        c.setopt(pycurl.CONNECTTIMEOUT, self.CONNECTTIMEOUT)
        c.setopt(pycurl.TIMEOUT, self.TIMEOUT)
        #c.setopt(pycurl.SOCKET_TIMEOUT, 9)
        #c.setopt(pycurl.E_OPERATION_TIMEOUTED, 3600)
        c.setopt(pycurl.NOSIGNAL, 1)
 
        if self.COOKIE:        
            c.setopt(pycurl.COOKIEFILE, self.COOKIE)
            c.setopt(pycurl.COOKIEJAR, self.COOKIE)
        if self.POST:        
            if self.DATA:
                Data=self.DATA
            else: 
                Links=url.split('?',1)
                if len(Links)==2:
                    Data=Links[1]
                else:
                    Data=''
            c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.POSTFIELDS, Data)
            self.POST=0
        c.perform()
        if self.DownLoad:
            c.close()
            b.close()
            self.DownLoad=False
            return True
        self.HEADERCONTENT=self.bh.getvalue()
        try:
           
            head=c.getinfo(c.HTTP_CODE) 
            self.header=head
            C_TYPE=c.getinfo(c.CONTENT_TYPE)
            self.C_TYPE=C_TYPE
            
            value=b.getvalue()
            #print value
            c.close()
            if head>=400:
                return False
        
        except pycurl.error, e:

            head=c.getinfo(c.HTTP_CODE)
            self.header=head
 
            try:
                c.close()
            except:
                pass
            if errnum<1 and head>0 and head<400:
               nexterrnum=errnum+1
 
               return self.curl(url,nexterrnum) 
            print 'ERROR:',head,url
            return False
    
        self.Html=value
        
        return value

        
        return value
if __name__=='__main__':
    '''
        spider=downHtml()
        
        spider.COOKIE='./c.txt'
        
        spider.HTTPAUTH='foucheng:Guopete6#'
        try:
            os.remove(spider.COOKIE)
        except:
            pass
        print spider.curl('http://qtool-gp.lss.emc.com/')
        
        spider.POST=1
        spider.DATA='value=-480&a=2&'
        spider.curl('http://qtool-gp.lss.emc.com/wfm/saveoption/utc_offset/')
  
        print spider.curl('http://qtool-gp.lss.emc.com/viewsr/55901026/')
    '''
    '''
    spider=downHtml()
    spider.HTTPAUTH='bob:bob'
    spider.POST=1 
    spider.DATA='options='+urllib.quote('{"prod_name":"DCA 1.1"}')
    print spider.curl('https://172.18.73.253:8443/elcid_ws/support/PSI/PSISummary?_type=json')
    '''