from bs4 import BeautifulSoup
import requests
import json
import lxml
import os
import re
class _Box:#单条微博容器
    def __init__(self,text:str,time:str,imgs:list):
        self.text = text
        self.time = time
        self.imgs = imgs
class TiaoZi:
    _heads = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb\
        Kit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }
    def __init__(self, url:str, proxyport:int):
        if not os.path.exists('result'):
            os.mkdir('result')
        self._url1st = url
        self._url = url
        self._path = 'result\\'
        self._pageslist = []
        self._result = []
        self._html = ''
        self._dic = {}
        self._proxies = {'https': f'http://localhost:{str(proxyport)}'}
    def _gethtml(self):#获取单页
        requests.packages.urllib3.disable_warnings()
        response = requests.get(url=self._url, headers=TiaoZi._heads, proxies=self._proxies, verify=False)
        self._html = ''
        self._html = response.text
    def _getnextpag(self):#获取下一页
        bs = BeautifulSoup(self._html, "lxml")
        a = bs.find_all(attrs={'class':'next'})[0]
        next = '' if a.attrs['href']=='?next=' else (self._url1st + a.attrs['href'])
        return next
    def _findAlltags(self):#获取单页中每条微博地址
        bs = BeautifulSoup(self._html, 'lxml')
        a = bs.find_all(attrs={'class': 'wb-item'})
        list2 =[]
        for i in a:
            c = i.find_all(attrs={'class': 'wb-from'})[0]
            try:
                sttr = 'https://peachring.com/'+c.a.attrs['href']
                list2.append(sttr)
            except:
                pass
        self._pageslist.clear()
        self._pageslist = list2.copy()
    def _singlepageprocessor(self,url):#提取单条微博内容，时间，大图
        requests.packages.urllib3.disable_warnings()
        response = requests.get(url=url, headers=TiaoZi._heads, proxies=self._proxies, verify=False)
        bs = BeautifulSoup(response.text,'lxml')
        tag = bs.select('body > div.box > div.wb-main.minWidth > div > div.fr.wb-user-list > div > div.wb-item > div.wb-text')[0]
        text = tag.text
        tag2 = bs.select('body > div.box > div.wb-main.minWidth > div > div.fr.wb-user-list > div > div.wb-item > div.wb-from > span.time')[0]
        time = tag2.string
        bigimgs = []
        try:
            imgtar = bs.select('body > div.box > div.wb-main.minWidth > div > div.fr.wb-user-list > div > div.wb-item > div.wb-big-pic > ul')[0]
            for item in imgtar.find_all('li'):
                imgurl = item.img.attrs['src']
                bigimgs.append(imgurl)
        except:
            pass
        box = _Box(text,time,bigimgs)
        return box
    def _getPagesinf(self):#获取每页的各条微博内容列表
        self._result.clear()
        for item in self._pageslist:
            self._result.append(self._singlepageprocessor(item))
    def _tojson(self):#生成含文件名和单条微博内容的json
        self._dic.clear()
        list_rs = []
        for item in self._result:
            list1:list = item.imgs
            list2 = [x for x in range(len(list1))]
            dic1 = dict(zip(list2,list1))
            dic = {'text':item.text,'time':item.time,'imgs':dic1}
            jsonresl = json.dumps(dic)
            list_rs.append(jsonresl)
        list_name = [x[34:].replace('/','-')+'.json' for x in self._pageslist]
        dic = dict(zip(list_name,list_rs))
        self._dic = dic.copy()
    def run(self):
        while True:
            if self._url:
                try:
                    self._gethtml()#
                    self._findAlltags()#
                    self._getPagesinf()#
                except Exception as e:
                    dic = {'err':1,'_url':self._url,'_url1st':self._url1st, 'pro':self._proxies}
                    with open('lw.cfg','w') as f:
                        f.write(json.dumps(dic))
                    raise e
                self._tojson()
                for k,v in self._dic.items():
                    with open(self._path+k,'w') as f:
                        f.write(v)
                try:
                    self._url = self._getnextpag()
                except Exception as e:
                    dic= {'err':2,'_url':self._url, '_url1st':self._url1st, 'pro':self._proxies}
                    with open('lw.cfg','w') as f:#写入错误信息文件
                        f.write(json.dumps(dic))
                    raise e
            else:
                break
    def rework(self):#错误停止后再次运行
        string = ''
        with open('lw.cfg','w') as f:
            string = f.read()
        dic = json.loads(string)
        if dic['err']==1:
            self._url1st = dic['_url1st']
            self._url = dic['_url']
            self._proxies = dic['pro']
            self.run()
        if dic['err']==2:
            self._url1st = dic['_url1st']
            self._url = dic['_url']
            self._proxies = dic['pro']
            self._gethtml()  #
            self._url = self._getnextpag()
            self.run()
class DownL:
    _heads = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWeb\
           Kit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }
    def __init__(self):
        if not os.path.exists('pic'):#盛放图片的目录
            os.mkdir('pic')
        list1= os.listdir('result')
        self._flist = list1.copy()
    def _imgdown(self,imgurl:str,dir:str):
        response = requests.get(url=imgurl,headers=DownL._heads)
        name = imgurl.split('/')[-1]#图片名为图片本身名字
        with open(f'{dir}\\{name}','wb') as f:
            f.write(response.content)
    def _json2list(self,name:str):#将单挑微博内容json转为图片链接列表
        ldic = {}
        with open(name,'r') as f:
            ldic:dict = json.loads(f.read())['imgs']
        list1 = [v for k,v in ldic.items()]
        return list1
    def write2f(self):#图片链接写入文件后迅雷下载
        f = open('links.txt','a')
        for item in self._flist:
            path = f'result\\{item}'
            list1 = self._json2list(path)
            for n in list1:
                f.write(n+'\n')
        f.close()
    def run(self):#json文件‘#’前缀为成功，‘@’前缀为失败(太容易失败了)
        for item in self._flist:
            path = f'result\\{item}'
            list1 = self._json2list(path)
            for n in list1:
                try:
                    self._imgdown(n,'pic')
                except Exception as e:
                    os.rename(path, f'result\\@{item}')
                    raise e
            os.rename(path,f'result\\#{item}')
if __name__ == '__main__':
    t = TiaoZi('https://peachring.com/weibo/user/3972954596/',proxyport=7890)#clash本地代理端口
    t.run()#测试
    o = DownL()
    o.write2f()

