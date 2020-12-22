#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import requests
import time
import json
import os
import copy
import _thread
from bs4 import BeautifulSoup
#cookie，可以在我的订单页面，搜索list的网络请求，获取cookie值
thor = '963EF88D596B26B745B83C896C3657D2CCFCCD83C7DDCB70C88E2FD5550D9414323C39BEC576AD833B07AFAED0AB0EA56CE061C3E33F82DC188192C6EEF7A097AB4E1BD0AF34EB76F55D4CFFE94CCCFEEA53059C7A72ED7F4449577DABCDE00CCAACB8B6A59E5F90A6A290553BAE354546E313752D2502514D6DE33829ECB0B0BEB12FDAAB789060E79C5A981AE9B94F0A36CE57E8DF8C3A15CAB0E065B9923D'

#日志模板，有颜色和状态
LOG_TEMPLE_BLUE='\033[1;34m{}\033[0m '
LOG_TEMPLE_RED='\033[1;31m{}\033[0m '
LOG_TEMPLE_SUCCESS='\033[1;32mSUCCESS\033[0m '
LOG_TEMPLE_FAILED='\033[1;31mFAILED\033[0m '

class JD:
    headers = {
        'referer': '',
        # 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36',
    }

    #初始化配置
    def __init__(self):
        self.index = 'https://www.jd.com/'

        #京东服务器时间地址(毫秒)
        self.clock_url = 'https://a.jd.com//ajax/queryServerData.html'
        #用户信息获取地址
        self.user_url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action?&callback=jsonpUserinfo&_=' + \
            str(int(time.time() * 1000)) 
        #加购物车
        self.buy_url = 'https://cart.jd.com/gate.action?pid={}&pcount=1&ptype=1'   
        #修改购物车商品数量为1
        self.change_num = 'https://cart.jd.com/changeNum.action?pid={}&pcount=1&ptype=1'
        #下单
        self.pay_url = 'https://cart.jd.com/gotoOrder.action'  
        #订单提交
        self.pay_success = 'https://trade.jd.com/shopping/order/submitOrder.action'  
        #商品id
        self.goods_id = ''  
        #会话
        self.session = requests.session()

        #3080搜索链接
        # self.rep_url = 'https://search.jd.com/search?keyword=3080&wq=3080&ev=24_95631%5E&shop=1&click=1'
        # self.rep_url = 'https://search.jd.com/Search?keyword=amd%205900x&enc=utf-8&wq=amd%205900x'
        # self.rep_url = 'https://search.jd.com/Search?keyword=amd%205900x&enc=utf-8&wq=amd%205900x'
        # self.rep_url = 'https://search.jd.com/Search?keyword=%E8%8C%85%E5%8F%B0%E9%A3%9E%E5%A4%A9&enc=utf-8&pvid=e14315eb4a9f46f5ac39fb9cd61120a6'
        self.rep_url = 'https://search.jd.com/search?keyword=3080%20tuf%20oc&qrst=1&suggest=2.def.0.base&wq=3080%20tuf%20oc&shop=1&ev=exbrand_%E5%8D%8E%E7%A1%95%EF%BC%88ASUS%EF%BC%89%5E296_136030%5Eexprice_0-6299%5E'
        #耕升3080追风
        self.g_url = 'https://item.jd.com/100015062658.html'
        #商品详情地址
        self.item_info_url = 'https://item-soa.jd.com/getWareBusiness?skuId={}'
        #预约地址
        self.appoint_url = ''
        self.config = {}

        #cookie
        self.thor = thor
        #重试次数限制
        self.retry_limit = 100
        #重试间隔
        self.gap = 0.1
        #重试计数
        self.retry_count = 0
        #本地时间与京东时间差
        self.time_diff = 0.1
        
    def initTime(self):
        ret = requests.get(self.clock_url).text
        js = json.loads(ret)
        self.time_diff = js.get('serverTime')/1000 - time.time() + 0.001

    #登录，然后抢预约成功的商品
    def buy(self): 
        #1通过session获取用户信息
        response = self.session.get(
            url=self.user_url, headers=JD.headers).text.strip('jsonpUserinfo()\n')
        #1.1调用内置的loads方法获取json格式的用信息
        self.user_info = json.loads(response)
        if self.user_info.get('nickName'):
            #遍历预约成功的商品，挨个抢购
            for key in self.config:
                item = copy.copy(self)
                #下单时间（使用本机时间，记得和京东服务器同步时间）
                timeArray = time.strptime(self.config[key]['order_time'], "%Y-%m-%d %H:%M")
                order_time_st = int(time.mktime(timeArray))
                item.order_time_st = order_time_st
                self.config[key]['order_time_st'] = order_time_st
                item.goods_url = self.config[key]['goods_url']
                item.order_time = self.config[key]['order_time']
                _thread.start_new_thread( self.run, (item, ))
                pass
            _thread.start_new_thread(self.log,())
            pass

            
    #日志方法
    def log(self):
        clock = round(time.time())
        i = 0
        while True:
            time.sleep(0.1)
            r = round(time.time())
            if r > clock:
                i += 1
                clock = r
                print('\x1b[H\x1b[2J')
                log = []
                log.append(LOG_TEMPLE_BLUE.format('账号') + self.user_info.get('nickName') + '\n\n')

                for key in self.config:
                    if time.time() <= self.config[key]['order_time_st']:
                        log.append('\t\t' + LOG_TEMPLE_RED.format(key) + '\n')
                        log.append(LOG_TEMPLE_BLUE.format('抢购时间')  + self.config[key]['order_time'] + '\n')
                        log.append(LOG_TEMPLE_BLUE.format('剩余时间')  + str(round(self.config[key]['order_time_st'] - r, 2)) + '秒\n\n')

                print(''.join(log))
                if i > 3600:
                    print('开始扫描是否有新增3080商品...')
                    self.rep()
                    self.appoint()
                    i = 0           
            pass
        

    def run(self, item):
        while True:
            time.sleep(item.gap)
            if time.time() + self.time_diff <= item.order_time_st:
                continue
            try:
                if item.retry_limit < 1 :
                    return
                
                o = item.shopping(item)
                
                if o:
                    return
                item.retry_limit = item.retry_limit - 1
                #重试计数
                item.retry_count = item.retry_count + 1
            except BaseException:
                continue
        

    def shopping(self, item):
        #获取商品id，从url的/开始位置截取到.位置
        item.goods_id = item.goods_url[
            item.goods_url.rindex('/') + 1:item.goods_url.rindex('.')]
        JD.headers['referer'] = item.goods_url
        # url格式化，把商品id填入buy_url
        buy_url = item.buy_url.format(item.goods_id)
        #get请求，添加购物车
        item.session.get(url=buy_url, headers=JD.headers)  
        #修正购物车商品数量（第二次重试后修正购物车数量）
        if item.retry_count > 0 :
            print('第',item.retry_count,'次重试，抢购商品为：',item.goods_id,'修正购物车商品数量。')
            change_num_url = item.change_num.format(item.goods_id)
            item.session.get(url=change_num_url, headers=JD.headers)
        #get请求
        item.session.get(url=item.pay_url, headers=JD.headers) 
        #post请求，提交订单
        response = item.session.post(
            url=item.pay_success, headers=JD.headers)
        order_id = json.loads(response.text).get('orderId')
        if order_id:
            print('抢购成功订单号:', order_id)
            return True

    def rep(self):
        JD.headers['referer'] = 'https://cart.jd.com/cart.action'
        #cookie 实例化
        c = requests.cookies.RequestsCookieJar()
        #定义cookie
        c.set('thor', self.thor)  
        self.session.cookies.update(c)
        response = self.session.get(
            url=self.user_url, headers=JD.headers).text.strip('jsonpUserinfo()\n')
        self.user_info = json.loads(response)
        # print(self.user_info)
        #{'householdAppliance': 0, 'imgUrl': '//passport.jd.com/new/misc/skin/df/i/no-img_mid_.jpg', 'lastLoginTime': '', 'nickName': 'jd_草。民', 'plusStatus': '3', 'realName': '41525697-244597', 'userLevel': 4, 'userScoreVO': {'accountScore': 210, 'activityScore': 97, 'consumptionScore': 22732, 'default': False, 'financeScore': 96, 'pin': '41525697-244597', 'riskScore': 5, 'totalScore': 23335}}
        if not self.user_info.get('nickName'):
            raise Exception("账号验证错误请检查thor")

        p = self.session.get(url=self.rep_url, headers=JD.headers) 
        bf = BeautifulSoup(p.text, features='html5lib')
        texts = bf.find_all('div', class_ = 'p-name p-name-type-2') 
        for text in texts:
            # print(text)
            time.sleep(0.2)
            rtx = {}
            ##将标题的换行替换成空字符串，如下面的标题就是替换好的
            rtx['title'] = text.em.text.replace('\n','')
            if rtx['title'] in self.config:
                continue
            rtx['goods_url'] = 'https:' + text.a['href']

            ##rtx 输入格式{'title': '华硕 ASUS TUF-RTX3080-O10G-GAMING  1440-1815MHz  吃鸡电竞游戏专业独立显卡 可支持4K显示器', 'goods_url': 'https://item.jd.com/100015236850.html'}
            # print(rtx)
            ##获取商品skuId,如：100015236850
            jid = rtx['goods_url'] [rtx['goods_url'].rindex('/') + 1:rtx['goods_url'].rindex('.')]
            # print('jid内容'+jid)
            #请求商品详情地址
            p = self.session.get(url=self.item_info_url.format(jid), headers=JD.headers)
            """
            #{"extendWarrantyInfo":{"descUrl":"https://baozhang.jd.com/static/serviceDesc","detailUrl":"http://static.360buyimg.com/finance/mobile/insurance/warrantyServiceDesc/html/warrantyExtension.html?mainSkuId={mainSkuId}&brandId={brandId}&thirdCategoryId={cid3}&bindSkuId={bindSku}","serviceItems":[]},"warmTips":[{"imageUrl":"","text":"不支持7天无理由退货"}],"rankUnited":{},"hasPlusBalance":true,"promiseFxgInfo":{"fxgCode":"0"},"hasWarranty":false,"is7ToReturn":"不支持7天无理由退货","soldOversea":{"isSoldOversea":true,"isYanbaoShield":true,"soldOverseaService":{"soldOverseaIcon":"http://m.360buyimg.com/cc/jfs/t4984/195/1172610074/2110/e12abb06/58ede3e4Nfc650507.png","soldOverseaText":"售全球","soldOverseaDesc":"支持收货地址为海外或港澳台地区"},"soldOverseaStr":"3"},"isInstallNow":false,"yuyueInfo":{"btnText":"立即预约","buyTime":"2020-12-23 11:00-2020-12-23 14:00","cdPrefix":"预约剩余","countdown":92141,"hidePrice":0,"hideText":"","num":20744,"plusText":"","plusType":0,"sellWhilePresell":"0","showDraw":false,"showPlusTime":false,"showPromoPrice":0,"state":2,"supportOther":0,"type":"1","url":"//yushou.jd.com/toYuyue.action?sku=100015236850&key=fbe1c475d44cff027c3dd87f58f39b1b","userType":"2","yuyue":true,"yuyueRuleText":["1.部分商品预约成功后才有抢购资格，预约成功后，请关注抢购时间及时抢购，货源有限，先抢先得！","2.部分商品在预约期间抢购时间未定，我们会在商品开抢前通过Push通知提醒您，请在设置中选择允许通知，以免错过抢购时间。","3.对于预约成功享优惠的商品，抢购开始后，点击\"立即抢购\"将商品加入购物车，可在购物车查看优惠，若抢购时间结束，优惠自动失效。","4.查看预约商品请至\"京东APP\"-\"我的\"-\"我的预约\"进行查看。","5.如果提供赠品，赠品赠送顺序按照预约商品购买成功时间来计算，而不是预约成功时间。","6.如您对活动有任何疑问，请联系客服咨询。"],"yuyueText":"预约享资格","yuyueTime":"2020-12-17 16:50~2020-12-23 10:50"},"price":{"discount":"4.1折","epp":"","hagglePromotion":false,"id":"100015236850","l":"","m":"15000.00","nup":"","op":"6299.00","p":"6299.00","plusTag":{"limit":false,"min":0,"max":0,"overlying":false},"pp":"","sdp":"","sfp":"","sp":"","tkp":"","tpp":""},"makeMoreTime":{"appointMoreTimeFlag":true,"banner":{"img":"http://m.360buyimg.com/cc/jfs/t1/69858/32/16298/154577/5ddcd24cE51bafea1/0797d3da17b06570.png","logo":"http://m.360buyimg.com/cc/jfs/t1/71767/25/16406/9140/5ddcd2e7E180dfeea/c7c14ac7810ab184.png","text":"PLUS会员专享购"},"endTime":"2020-12-23 14:00:00","makeMoreTimeFlag":true,"plusShopFlag":false,"userFlag":true},"adText":"【3期免息！180天换新！】硬派电竞3080超频版！敬请期待！硬派电竞3070超频版》跳转链接查看>","shopInfo":{"shop":{"avgEfficiencyScore":0.0,"avgServiceScore":0.0,"avgWareScore":0.0,"brief":"华硕京东自营，正品保证，服务贴心。","cardType":3,"cateGoodShop":0,"diamond":false,"efficiencyScore":0.0,"followCount":2033031,"giftIcon":"","goodShop":0,"hasCoupon":false,"hotcates":[{"cid":2981962,"cname":"显卡","commendSkuId":6164010,"imgPath":"http://m.360buyimg.com/n1/jfs/t1/1760/37/15665/99528/5be0144cE41fa6398/336c70b93fd757db.jpg"},{"cid":2981961,"cname":"主板","commendSkuId":100001749041,"imgPath":"http://m.360buyimg.com/n1/jfs/t1/112810/23/9338/631741/5ed89e59E931d820d/60259196da6836eb.jpg"},{"cid":2981963,"cname":"显示器","commendSkuId":100010957314,"imgPath":"http://m.360buyimg.com/n1/jfs/t1/143274/35/16430/220276/5fc5b503E136d6c2a/47a7e0c43e3eecba.jpg"},{"cid":8571993,"cname":"游戏电竞耳机","commendSkuId":100016040324,"imgPath":"http://m.360buyimg.com/n1/jfs/t1/120596/10/15771/63214/5f8e7a5cEe7b4b217/7e591165e14b2b8c.jpg"}],"hotcatestr":"华硕京东自营，正品保证，服务贴心。","isSquareLogo":true,"logo":"http://img12.360buyimg.com/cms/jfs/t1/39243/39/12382/42163/5d3950ceE197045dc/d1d8d6602ac18733.gif","name":"华硕京东自营旗舰店","nameB":"华硕京东自营旗舰店","newNum":0,"promotionNum":0,"promotions":[{"name":"限时秒杀","url":"openApp.jdMobile://virtual?params={\"category\":\"jump\",\"des\":\"jshopMain\",\"jumpTab\":\"activity\",\"shopId\":\"1000000225\",\"venderId\":\"1000000225\",\"shopName\":\"华硕京东自营旗舰店\",\"logoUrl\":\"http://img12.360buyimg.com/cms/jfs/t1/39243/39/12382/42163/5d3950ceE197045dc/d1d8d6602ac18733.gif\",\"signboardUrl\":\"http://img12.360buyimg.com/cms/jfs/t1/53626/25/12252/159070/5d91d284E0f15fd6f/810023493711bb53.jpg\",\"activityTabInfo\":{\"sort\":\"secKillPage\"},\"source\":{\"moduleId\":\"app-productDetail\",\"entrance\":\"商详卡片\"}}"},{"name":"限时闪购","url":"openApp.jdMobile://virtual?params={\"category\":\"jump\",\"des\":\"jshopMain\",\"jumpTab\":\"activity\",\"shopId\":\"1000000225\",\"venderId\":\"1000000225\",\"shopName\":\"华硕京东自营旗舰店\",\"logoUrl\":\"http://img12.360buyimg.com/cms/jfs/t1/39243/39/12382/42163/5d3950ceE197045dc/d1d8d6602ac18733.gif\",\"signboardUrl\":\"http://img12.360buyimg.com/cms/jfs/t1/53626/25/12252/159070/5d91d284E0f15fd6f/810023493711bb53.jpg\",\"activityTabInfo\":{\"sort\":\"gwredPage\"},\"source\":{\"moduleId\":\"app-productDetail\",\"entrance\":\"商详卡片\"}}"}],"score":0.0,"serviceScore":0.0,"shopActivityTotalNum":25,"shopId":1000000225,"shopImage":"http://img11.360buyimg.com/cms/jfs/t1/77105/16/3734/106147/5d1ea809E8398742c/6c0e43e663b31dda.jpg","signboardUrl":"http://img12.360buyimg.com/cms/jfs/t1/53626/25/12252/159070/5d91d284E0f15fd6f/810023493711bb53.jpg","squareLogo":"http://img13.360buyimg.com/cms/jfs/t1/47773/38/5941/406578/5d39562fE3b4799c3/327a199428e7c82f.gif","telephone":"","totalNum":793,"venderType":"1","wareScore":0.0},"customerService":{"hasChat":false,"hasJimi":false,"mLink":"http://m.jd.com/product/100015236850.html","online":false}},"ad":"【3期免息！180天换新！】硬派电竞3080超频版！敬请期待！硬派电竞3070超频版》跳转链接<a href='//item.jd.com/100009177343.html' target='_blank'>查看></a>","disableCoupon":{"iconServiceType":0,"jichu":false,"name":"不可使用全品类券","tip":"此商品不可使用全品类京券、全品类东券"},"servicesInfoUnited":{"addressInfo":{"cityId":"2768","cityName":"台湾","countyId":"53511","countyName":"台中市","provinceId":"32","provinceName":"台湾","townId":"54158","townName":"北屯区"},"hasWarranty":false,"icon":true,"isSupport":1,"promiseFxgInfo":{"fxgCode":"0"},"servIconRelations":[{"iconType":"exclamation","iconValue":"detail_006"},{"iconType":"right","iconValue":"detail_005"}],"serviceInfo":{"basic":{"iconList":[{"iconType":"right","imageUrl":"https://m.360buyimg.com/cc/jfs/t4984/195/1172610074/2110/e12abb06/58ede3e4Nfc650507.png","jichu":false,"show":true,"sortId":3,"text":"可配送港澳台","tip":"支持收货地址为港澳台"}],"title":"服务说明"}},"soldOversea":{"isSoldOversea":true,"isYanbaoShield":true,"soldOverseaService":{"soldOverseaIcon":"http://m.360buyimg.com/cc/jfs/t4984/195/1172610074/2110/e12abb06/58ede3e4Nfc650507.png","soldOverseaText":"售全球","soldOverseaDesc":"支持收货地址为海外或港澳台地区"},"soldOverseaStr":"3"},"stockInfo":{"area":{"cityId":"2768","cityName":"台湾","countyId":"53511","countyName":"台中市","provinceId":"32","provinceName":"台湾","townId":"54158","townName":"北屯区"},"deliveryInfo":{"state":"SUPPORT","support":true},"isPlus":true,"code":1,"serviceInfo":"由 <span class='hl_red'>京东</span> 发货, <a href='http://asus.jd.com/' clstag='shangpin|keycount|product|bbtn' class='hl_red'>华硕京东自营旗舰店</a>提供售后服务. ","stockDesc":"<strong>无货</strong>，此商品暂时售完","is7ToReturn":"不支持7天无理由退货","stockState":34,"stockInfo":{"ae":0,"ah":-1,"availableNum":-1,"businessType":-1,"ca":-1,"date":"","dcId":10,"dcIdDely":10,"ef":0,"freshEdi":0,"popPatType":-1,"preStore":-1,"reservationType":"OTHER","rid":0,"sidDely":88,"siteId4Dada":-1,"stDely":51,"stockM":0,"stockState":"DISABLE","stockV":0,"storeId":88,"storeId4Dada":-1,"storeState4Dada":-1,"storeType":51,"useStockNum":-1000000000},"supportHKMOShip":true,"serverIcon":{"wlfwIcons":[],"basicIcons":[{"iconType":"right","imageUrl":"https://m.360buyimg.com/cc/jfs/t4984/195/1172610074/2110/e12abb06/58ede3e4Nfc650507.png","jichu":false,"show":true,"sortId":3,"text":"可配送港澳台","tip":"支持收货地址为港澳台"}]},"support":[],"isStock":false},"wareExtendWarrantyInfo":{"descUrl":"https://baozhang.jd.com/static/serviceDesc","detailUrl":"http://static.360buyimg.com/finance/mobile/insurance/warrantyServiceDesc/html/warrantyExtension.html?mainSkuId={mainSkuId}&brandId={brandId}&thirdCategoryId={cid3}&bindSkuId={bindSku}","serviceItems":[]},"wareStockInfo":{"is7ToReturn":false,"is7shortService":"不可七天退货"},"warmTips":[{"imageUrl":"","text":"不支持7天无理由退货"}]},"couponInfo":[],"overSea":{"overseaSaleSupport":true,"supportHKMOShip":true},"warrantyInfo":{"descUrl":"https://baozhang.jd.com/static/serviceDesc","detailUrl":"http://static.360buyimg.com/finance/mobile/insurance/warrantyServiceDesc/html/warrantyExtension.html?mainSkuId={mainSkuId}&brandId={brandId}&thirdCategoryId={cid3}&bindSkuId={bindSku}","serviceItems":[]},"shopUrl":"http://asus.jd.com/","giftShoppingInfo":{"gaoduanGift":false,"hasGift":false,"huodongGift":false},"hasFinanceCoupon":false,"jdddFlag":false,"isSamMember":false,"stockInfo":{"area":{"cityId":"2768","cityName":"台湾","countyId":"53511","countyName":"台中市","provinceId":"32","provinceName":"台湾","townId":"54158","townName":"北屯区"},"deliveryInfo":{"state":"SUPPORT","support":true},"isPlus":true,"code":1,"serviceInfo":"由 <span class='hl_red'>京东</span> 发货, <a href='http://asus.jd.com/' clstag='shangpin|keycount|product|bbtn' class='hl_red'>华硕京东自营旗舰店</a>提供售后服务. ","stockDesc":"<strong>无货</strong>，此商品暂时售完","is7ToReturn":"不支持7天无理由退货","stockState":34,"stockInfo":{"ae":0,"ah":-1,"availableNum":-1,"businessType":-1,"ca":-1,"date":"","dcId":10,"dcIdDely":10,"ef":0,"freshEdi":0,"popPatType":-1,"preStore":-1,"reservationType":"OTHER","rid":0,"sidDely":88,"siteId4Dada":-1,"stDely":51,"stockM":0,"stockState":"DISABLE","stockV":0,"storeId":88,"storeId4Dada":-1,"storeState4Dada":-1,"storeType":51,"useStockNum":-1000000000},"supportHKMOShip":true,"serverIcon":{"wlfwIcons":[],"basicIcons":[{"iconType":"right","imageUrl":"https://m.360buyimg.com/cc/jfs/t4984/195/1172610074/2110/e12abb06/58ede3e4Nfc650507.png","jichu":false,"show":true,"sortId":3,"text":"可配送港澳台","tip":"支持收货地址为港澳台"}]},"support":[],"isStock":false},"userInfoMap":{"flagInfoByPin":"0000000000000000201000000000010500100000000000006300401000000080000000000000000000000000000000000000","idAuthThrough":true,"jingXiangScore":23340,"plusMember":"1","samMember":false,"unJdUserFlag":false},"isPlusMember":"1","wozheFlag":false,"isJdkd":false,"actions":{"highPriceBuy":{"bizKey":"yjhx","desc":"旧品回收，免费估价，极速到账","icon":"http://m.360buyimg.com/cc/jfs/t1/17024/4/15356/2143/5caeb5efEf90f64a9/f4205d7302e4433c.png","jumpType":1,"mustLogin":false,"truthBigSale":false,"url":"https://huishou.m.jd.com/index?source=3&skuId=100015236850&cid1=670&cid2=677&cid3=679&province=32&city=2768&town=0&hx=0&IsSXQJ=0&IsYZS=0&menu=0&commodityType=2&activityType=1"}},"isJdwl":false,"fullOrderInfo":{"activityId":"30407","businessType":"8","link":"https://pro.jd.com/mall/active/3Fh9CrKeyMeDxf71AwtvLycFDGXP/index.html","proSortNum":"13","text":"满额返券","value":"购母婴、玩具、清洁、个护、厨具、生鲜、食品、宠物、酒水、家电、电脑数码部分自营商品满1元返券包"},"promotion":{"activity":[{"value":"购母婴、玩具、清洁、个护、厨具、生鲜、食品、宠物、酒水、家电、电脑数码部分自营商品满1元返券包","activityId":"30407","text":"满额返券","businessType":"8","proSortNum":13,"skuId":"","typeNumber":"fullOrder","link":"&nbsp;&nbsp;<a href='//pro.jd.com/mall/active/3Fh9CrKeyMeDxf71AwtvLycFDGXP/index.html' clstag='shangpin|keycount|product|满额返券' target='_blank'>详情<s class='s-arrow'>&gt;&gt;</s></a>","activityType":"","promoId":""}],"attach":[],"canReturnHaggleInfo":false,"customtag":{},"gift":[{"mp":"jfs/t1/148965/33/7716/96679/5f55f558Ebafa1151/476c0f54463d4905.jpg","proId":"200030739312","num":"1","customTag":{"1":"赠品"},"link":"","tip":"（赠完即止）","text":"赠品","activityType":"10","value":"显卡180天质保换新（4000-7000）（赠完即止）","skuId":"100008567537"}],"giftTips":"（赠完即止）","isBargain":false,"isTwoLine":false,"limitBuyInfo":{"limitNum":"1","noSaleFlag":"0","promotionText":"限购1件","resultExt":{"isPlusLimit":"1","beginTime":"2020-12-17 16:50:00","endTime":"2020-12-23 14:00:00"}},"normalMark":"tab_var_071","plusMark":"tab_var_124","prompt":"此商品不可使用全品类京券、全品类东券","screenLiPurMap":{},"tip":"","tips":[],"upgradePurchaseMap":{}}}
            """

            if p.text:
                try:
                    yyinfo = json.loads(p.text).get('yuyueInfo')
                    if yyinfo:
                        rtx['appoint_url'] = yyinfo['url']
                        rtx['order_time'] = yyinfo['buyTime'].split('-202')[0]
                        self.config[rtx['title']] = rtx
                        rtx['appoint'] = False
                        print('正在添加如下商品：' + rtx['title'])
                        pass
                    pass
                except BaseException:
                    print(p.text)


    
    def appoint(self):
        print('开始预约\n')
        for key in self.config:
            if not self.config[key]['appoint']:
                if not self.config[key]['appoint_url']:
                    continue
                ##
                ares = self.session.get(url='https:' + self.config[key]['appoint_url'], headers=JD.headers)
                bf = BeautifulSoup(ares.text, features='html5lib')
                texts = bf.find_all(class_ = 'bd-right-result')
                if len(texts) > 0:
                    print(key + ' 预约结果：\n' + texts[0].text.strip())
                    self.config[key]['appoint'] = True
                else:
                    print(LOG_TEMPLE_RED.format(key + '\n需要手动预约：') + LOG_TEMPLE_BLUE.format('https:' + self.config[key]['appoint_url']))
                print('--------------------------')  
        for i in range(10):
            time.sleep(1) 
            end_str = '100%'
            print('\r' + str(10 - i) + '秒后进入监控页面，若需要手动预约请CTRL+C退出脚本预约后再执行...', end='', flush=True)


jd = JD()
#修改本地时间和服务器时间的差值
jd.initTime()
##获取用户信息和商品信息（如开始时间，预约地址等）
jd.rep()
#预约操作
jd.appoint()

##结算下单操作
jd.buy()	


while 1:
    time.sleep(10)

