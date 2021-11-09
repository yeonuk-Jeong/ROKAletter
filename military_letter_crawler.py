import requests
import os.path
import json
from bs4 import BeautifulSoup
from bs4 import Comment
from enum import Enum
import re
from webob.compat import urlparse
import schedule
import time
import math
# --Class PageFeed : Get facebook page/group's writing--
'''
Usage
fbc = FacebookCrawler()
fbc.set_user("username")

fbc.addPagetoList or GroupList
fbc.auto~~.
or
fbc.pageFeed(...)
'''


#Letter Sending Class
class LetterClient:
    host = 'https://www.thecamp.or.kr'

    def __init__(self):
        self.session = requests.Session()

    def _post(self, endpoint, data):
        response = self.session.post(self.host + endpoint, data=data)
        if response.status_code != 200:
            raise ConnectionError(f'Connection failed: [{response.status_code}] - {response.text}')
        return response.text

    def login(self, userid='kjhg4330@naver.com', passwd='zmfhffj08!'):
        endpoint = '/login/loginA.do'
        data = {
            'state': 'email-login',
            'autoLoginYn': 'N',
            'userId': userid,
            'userPwd': passwd,
        }

        result = self._post(endpoint, data)
        result = json.loads(result, encoding='utf-8')

        if 'resultCd' in result and result['resultCd'] == '0000':
            print(f'Successfully Login! [{userid}]')
            return True
        print(f'Login failed. [{result["resultMsg"] if "resultMsg" in result else "Unknown Error"}]')
        return False


    def send_letter(self, name, title, content):
        print(time.strftime('%D//%H:%M'))
        chkedContent = self.splitContent(content)# 1500자 제한

        i=1
        for cont in chkedContent:
            print('letter',i)
            i=i+1
            self.send(name, title, cont)
            time.sleep(1)

    def send(self, name, title, content):
        cafes = self.get_cafes()
        if name not in cafes:
            print(f'No Cafe with name: [{name}].')
            return False
        if cafes[name] is None:
            print(f'Cafe[{name}] is not open yet.')
            return False

        mgr_seq = self._get_mgr_seq(*cafes[name])
        endpoint = '/consolLetter/insertConsolLetterA.do'
        data = {
            'boardDiv': '',
            'tempSaveYn': 'N',
            'sympathyLetterEditorFileGroupSeq': '',
            'fileGroupMgrSeq': '',
            'fileMgrSeq': '',
            'sympathyLetterMgrSeq': '',
            'traineeMgrSeq': mgr_seq,
            'sympathyLetterSubject': title,
            'sympathyLetterContent': content,
        }

        result = self._post(endpoint, data)
        #result = json.loads(result, encoding='utf-8')
        print(result)
        
    def splitContent(self, content): # 1500자 제한때문에 크롤링한 글이 길면 편지를 나눠 보내야함.근데 제한수가 매년 바뀌는듯.
        bodies = []
        
        if len(content) < 1450 :
            bodies.append(content)
        else:
            for i in range(0, math.ceil(len(content)/1450)):
                bodies.append(content[i*1450:i*1450+1450])
                
        return bodies
            


    def get_cafes(self):
        endpoint = '/eduUnitCafe/viewEduUnitCafeMain.do'
        data = {}
        
        result = self._post(endpoint, data)
        soup = BeautifulSoup(result, 'html.parser')

        cafe_table = {}

        cafes = soup.select('.cafe-card-box')
        
        ### 첫번째 카페확인 눌러보기 ###
        for cafe in cafes:
            name_div = cafe.select('.profile-wrap .id span')[0]
            name = name_div.text.split()[0]

            buttons = cafe.select('.btn-wrap')[0].find_all('a')
            
            for button in buttons:
                
                if button.text == '카페확인': # 맨 처음에는 가입확인를 눌러줘야 가입하기 버튼 뜸.
                    regex = re.compile('\'.*\'')
                    codes = regex.findall(button['href'])
                    codes = codes[0].split(',')
                    regOrder,name,enterDate,birth,trainUnitTypeCd,trainUnitCd,grpCd=map(lambda x: x[1:-1], codes)
                    data = {'regOrder':regOrder,
                            'enterDate':enterDate,
                            'name':name,
                            'birth': birth,
                            'trainUnitTypeCd':trainUnitTypeCd,
                            'trainUnitCd': trainUnitCd,
                            'grpCd': grpCd}
                    result = self._post('/main/cafeCreateCheckA.do',data)
                    print(result)
                    
                    # 확인버튼 눌렀으면 다시 페이지 접속함. if 문 안에 두는 이유는 한번 카페개설 확인 뒤에는 새로고침 안하려고.
                    result = self._post(endpoint,{})
                    soup = BeautifulSoup(result, 'html.parser')
                    cafes = soup.select('.cafe-card-box')
                    
         
        
        
        #### 두번째. 가입하기 누르기 ####### 
        for cafe in cafes:
            name_div = cafe.select('.profile-wrap .id span')[0]
            name = name_div.text.split()[0]

            buttons = cafe.select('.btn-wrap')[0].find_all('a')
            for button in buttons:
            
                
                if button.text == '가입하기': # 맨 처음에는 가입하기를 눌러줘야 가입이되고 편지쓰기 버튼이 나옴.
                    regex = re.compile('\'\d+\'')
                    codes = regex.findall(button['href'])
                    trainUnitEduSeq, traineeMgrSeq,traineeRelationshipCd =map(lambda x: int(x[1:-1]), codes)
                    data = {'insertType':1,
                            'trainUnitEduSeq':trainUnitEduSeq,
                            'traineeMgrSeq': traineeMgrSeq,
                            'traineeRelationshipCd': traineeRelationshipCd}
                    result = self._post('/eduUnitCafe/insertCafeJoinAndMissSoldierA.do',data)
                    if 'resultCd' in json.loads(result)['resultCd'] == '0000':
                        print(f'Successfully join the cafe! [{name}]')

                    # 확인버튼 눌렀으면 다시 페이지 접속함. if 문 안에 두는 이유는 한번 카페가입 뒤에는 새로고침 안하려고.
                    result = self._post(endpoint,{})
                    soup = BeautifulSoup(result, 'html.parser')
                    cafes = soup.select('.cafe-card-box')
               
            
        for cafe in cafes:
            name_div = cafe.select('.profile-wrap .id span')[0]
            name = name_div.text.split()[0]

            buttons = cafe.select('.btn-wrap')[0].find_all('a')
            for button in buttons:    
                #### 세번째. 위문편지 작성 #######
                # 확인버튼 눌렀으면 다시 페이지 접속함
                result = self._post(endpoint,data)
                soup = BeautifulSoup(result, 'html.parser')
                cafes = soup.select('.cafe-card-box')
                for cafe in cafes:
                    name_div = cafe.select('.profile-wrap .id span')[0]
                    name = name_div.text.split()[0]

                    buttons = cafe.select('.btn-wrap')[0].find_all('a')


                    for button in buttons:
                        if button.text == '위문편지':
                            regex = re.compile('\'\d+\'')
                            codes = regex.findall(button['href'])

                            edu_seq, train_unit_code = map(lambda x: int(x[1:-1]), codes)
                            cafe_table[name] = (edu_seq, train_unit_code)

                            break

                        else:
                            cafe_table[name] = None
                            continue

        return cafe_table

    def _get_mgr_seq(self, edu_seq, train_unit_code):
        endpoint = '/consolLetter/viewConsolLetterMain.do'
        data = {
            'trainUnitEduSeq': edu_seq,
            'trainUnitCd': train_unit_code,
        }
        result = self._post(endpoint, data)
        soup = BeautifulSoup(result, 'html.parser')

        letter_box = soup.select('.letter-card-box')[0]
        regex = re.compile('\'\d+\'')
        codes = regex.findall(letter_box['href'])

        mgr_seq = map(lambda x: int(x[1:-1]), codes)
        return mgr_seq

    def get_group_code(self, group_name):
        group_code_table = {
            '육군':   '0000010001',
            '해군':   '0000010002',
            '공군':   '0000010003',
            '해병대':  '0000010004',
        }
        if group_name not in group_code_table:
            return ''
        return group_code_table[group_name]

    def get_train_unit_table(self, group_name):
        # endpoint = '/selectCmmnCodeListA.do'
        # endpoint = '/join/selectCommCdListA.do'
        endpoint = '/join/selectTrainUnitListA.do'
        data = {
            'grpCd': self.get_group_code(group_name),
        }
        result = self._post(endpoint, data)
        result = json.loads(result, encoding='utf-8')

        unit_table = {}
        for unit in result['trainUnitList']:
            unit_table[unit['trainUnitNm']] = unit['trainUnitCd']
        return unit_table

    def get_relation_code(self, relation_name):
        relation_code_table = {
            '부모': '0000420001',
            '형제/자매': '0000420002',
            '배우자': '0000420003',
            '친척': '0000420004',
            '애인': '0000420005',
            '친구/지인': '0000420006',
            '팬': '0000420007',
        }
        if relation_name not in relation_code_table:
            return ''
        return relation_code_table[relation_name]

class company_price:
    def __init__(self):
        pass
    
    def get_code(self, company_code):
        url = "http://finance.naver.com/item/main.nhn?code=" + str(company_code)
        result = requests.get(url)
        bs_obj = BeautifulSoup(result.content , 'html.parser')
        return bs_obj


    def get_price(self, company_code):
        bs_obj = self.get_code(company_code)
        no_today = bs_obj.find("p", {"class" : "no_today"})
        blind = no_today.find("span", {"class" : "blind"})
        now_price = blind.text

        no_info = bs_obj.find("table", {"class" : "no_info"})
        table = no_info.find_all("span",{"class" : "blind"})
        table_info =[]
        for i in table:
            table_info.append(i.text)
        tag = ['전일', '고가', '상한가', '거래량', '시가', '저가', '하한가', '거래대금(백만)']

        return now_price , dict(zip(tag,table_info))


    
class NaverFinanceNewsCrawler:
    URL_NAVER_FINANCE = "http://finance.naver.com"
    URL_NAVER_FINANCE_NEWS_QUERY = "http://finance.naver.com/news/news_search.nhn?q=%s&x=0&y=0" # params: query
    URL_NAVER_FINANCE_NEWS_CODE = "http://finance.naver.com/item/news_news.nhn?code=%s&page=%s" # params: (code, page)
    URL_NAVER_NEWS_FLASH = "http://finance.naver.com/news/news_list.nhn?mode=LSS2D&section_id=101&section_id2=258"
    URL_NAVER_STOCK_NOTICE = "http://finance.naver.com/item/news_notice.nhn?code=%s&page=%s" # params: (code, page)

    def __init__(self):
        pass

    def crawl(self, query=None, code=None, page=1):
        """

        :param query:
        :param code:
        :param page:
        :return:
        """
        if query:
            return self._crawl_by_query(query)
        elif code:
            return self._crawl_by_code(code, page=page)
        else:
            raise Exception("[Error] 'query' or 'code' should be entered.")

    def _crawl_by_query(self, query):
        """
        Crawl Naver Finance News
        :param query: string; search keywords
        :return: generator; [{title, summary, url, articleId, content, codes}, ...]
        """

        # Convert the query to euc-kr string
        q = ""
        for c in query.encode('euc-kr'):
            q += "%%%s" % format(c, 'x').capitalize()

        r_url = NaverFinanceNewsCrawler.URL_NAVER_FINANCE_NEWS_QUERY % (q)
        r = requests.get(r_url)

        soup = BeautifulSoup(r.text, 'html.parser')
        news = soup.find('div', class_='newsSchResult').find('dl', class_='newsList')
        news_title = news.find_all('dt', class_='articleSubject')
        news_summary = news.find_all('dd', class_='articleSummary')
        for title, summary in zip(news_title, news_summary):
            url = NaverFinanceNewsCrawler.URL_NAVER_FINANCE + title.a.get("href")
            res = {
                "title": title.a.text,
                "summary": summary.find(text=True).strip(' \t\n\r'),
                "url": url,
                "articleId": urlparse.parse_qs(urlparse.urlparse(url).query)["article_id"][0]
            }
            res.update(self._crawl_content(url))
            yield res

    def _crawl_by_code(self, code, page=1):
        """
        Crawl Naver Stock News
        :param code: string; a stock code
        :return: generator;
        """

        r_url = NaverFinanceNewsCrawler.URL_NAVER_FINANCE_NEWS_CODE % (code, page)
        r = requests.get(r_url)

        soup = BeautifulSoup(r.text, 'html.parser')
        news_rows = soup.find('table', class_='type2').find_all('td', class_='title')

        for row in news_rows:
            yield {"title": row.a.text.strip(' \t\n\r'), "url": row.a.get('href')}

    def _crawl_content(self, url):
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        content = soup.find('div', id="content", class_='articleCont')
        codes = re.findall(r"\d{6}", content.text)
        return {"content": content.text.strip(' \t\n\r'), "codes": codes}


if __name__ == "__main__":
    
    def job():
        
        letter_ = ''

        price = company_price()
        now , dic = price.get_price(215000)
        letter_ = letter_  + '골프존 현재가격 : ' + str(now) + '\n' +str(dic) + '\n\n'




        crawler = NaverFinanceNewsCrawler()
        docs = crawler.crawl(query='주요 증시')
        for i, d in enumerate(docs):
            letter_ = letter_+'\n' +"{i}번째 뉴스".format(i=i+1) + '\n'+ "내용: {content}".format(content=d["content"])
            if i==3:
                break


#         docs = crawler.crawl(query='AMD')
#         for i, d in enumerate(docs):
#             letter_ = letter_+ '\n' +"{i}번째 뉴스".format(i=i+1) + '\n'+ "내용: {content}".format(content=d["content"])
#             if i==3:
#                 break

        lc = LetterClient()
        #print('\n'.join(newsList))
        lc.login("이메일아이디", "비밀번호")
        lc.send_letter("이름", "편지제목", letter_)
#         print(letter_)
#         print(len(letter_))
        
 
     # 매일 특정 HH:MM 에 작업 실행
    schedule.every().day.at("17:00").do(job)

    while True:
        schedule.run_pending()

