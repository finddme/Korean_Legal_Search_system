import json
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
from urllib.parse import quote
import xml.etree.ElementTree as ET
import pandas as pd
import glob

import glob
file_list = glob.glob("/workspace/.gen/Crawler/Law/law_name_list" + "/*")
law_name_list=[]
for idx,fl in enumerate(file_list):
    if idx==0:
        df = pd.read_excel(fl)
        law_name_list.append(df["법령명"].tolist())
law_name_list=sum(law_name_list,[])
law_name_list=list(reversed(law_name_list))

def law_info_with_detail(xml_data):
    page = 1
    index_name = 'law_bulk'
    law_content = ['조문번호', '조문가지번호', '조문여부','조문제목','조문시행일자', '조문이동이전','조문이동이후',
                        '조문변경여부','조문제개정유형', '조문내용','조문참고자료','항']

    law_info = xml_data[8:]
    bulk_data = []
    for info in law_info:
        lawNum = info.find('법령일련번호').text
        lawTitle = info.find('법령명한글').text
        lawSubtitle = info.find('법령약칭명').text
        lawID = info.find('법령ID').text
        announce_date = info.find('공포일자').text
        announce_num = info.find('공포번호').text
        change = info.find('제개정구분명').text
        rel_with = info.find('소관부처명').text
        law_cat = info.find('법령구분명').text
        effect_data = info.find('시행일자').text
        lawLink = info.find('법령상세링크').text 
    
        # 상세 링크를 통해 본문 가져오기
        url_head = "https://www.law.go.kr/" 
        detail_link = url_head + lawLink.replace('HTML', 'XML')
        detail = urlopen(detail_link).read()
        root = ET.fromstring(detail)
    
        
        
        detail_dict = {}    # 전체
        depth1_dict = {}    # 항
        depth2_dict = {}    # 호
        depth3_dict = {}    # 목
    
        detail_list = []
    
        for n in range(len(root[1])):
            # print(root[1][n].tag)
            for content in law_content:
                dict_key = content
                
                try:
                    if(content == '항'):
                        if(root[1][n].find('항') is not None):
                            detail_dict['항'] = []
                            for depth1 in root[1][n].iter('항'):
                                if(depth1.find('호') is not None):
                                    depth1_dict['호'] = []
                                    for depth2 in depth1.iter('호'):
                                        if(depth2.find('목') is not None):
                                            depth2_dict['목'] = []
                                            for depth3 in depth2.iter('목'):
                                                if(depth3.find('목내용')is not None):
                                                    # print(depth3.find('목내용').text.strip())
                                                    depth3_dict['목내용'] = depth3.find('목내용').text.strip()
                                                    depth2_dict['목'].append(depth3_dict)
                                                    depth3_dict = {}
                                        if(depth2.find('호내용')is not None):
                                            # print(depth2.find('호내용').text.strip())
                                            depth2_dict['호내용'] = depth2.find('호내용').text.strip()
                                            depth1_dict['호'].append(depth2_dict)
                                            depth2_dict = {}
                                        else:
                                            depth1_dict['호'].append(depth2_dict)
                                            depth2_dict = {}
                                if(depth1.find('항내용') is not None):
                                    # print(depth1.find('항내용').text.strip())
                                    depth1_dict['항내용'] = depth1.find('항내용').text.strip()
                                    detail_dict['항'].append(depth1_dict)
                                    depth1_dict = {}
                                else:
                                    detail_dict['항'].append(depth1_dict)
                                    depth1_dict = {}
                        
                        
                    else:
                        dict_value = root[1][n].find(content).text.strip().replace('\n', '')
                        detail_dict[dict_key] = dict_value
                except:
                    continue
                
            detail_list.append(detail_dict)
            detail_dict = {}
        
        result = {
                    '_index': index_name,
                    '_source': {
                        '법령일련번호': lawNum,
                        '법령명한글': lawTitle,
                        '법령약칙명': lawSubtitle,
                        '법령ID': lawID,
                        '공포일자': announce_date,
                        '공포번호': announce_num,
                        '제개정구분명': change,
                        '소관부처명': rel_with,
                        '법령구분명': law_cat,
                        '시행일자': effect_data,
                        '조문': detail_list
                    }
                }
        
        bulk_data.append(result)
    return bulk_data


# total_res=[]
# url = "https://www.law.go.kr/DRF/lawSearch.do?OC=yein4452&target=law&type=XML"
# response = urlopen(url).read()
# xml_data = ET.fromstring(response)
# totalCnt = int(xml_data.find('totalCnt').text)
# for i in range(int(totalCnt / 20)):
# # for i in range(int(totalCnt)):
#     print(f"{i}/{totalCnt / 20}")
#     res=law_info_with_detail(xml_data)
#     for r in res:
#         total_res.append(r)
#     # total_res=sum(total_res,[])
#     save_as="./laws_final.json"
#     with open(save_as, 'w', encoding='utf-8') as outfile:
#         json.dump(total_res, outfile,indent="\t",ensure_ascii=False)


def collect_law_info(flag):
    total_res=[]
    if flag=="law_list":
        for idx,lnl in enumerate(law_name_list):
            try:
                query=quote(lnl)
                url = f"https://www.law.go.kr/DRF/lawSearch.do?OC=yein4452&target=law&type=XML&query={query}"
                response = urlopen(url).read()
                xml_data = ET.fromstring(response)
                totalCnt = int(xml_data.find('totalCnt').text)
                print(f"============ {idx} / {len(law_name_list)} ============")
                
                res=law_info_with_detail(xml_data)
                for r in res:
                    total_res.append(r)

                save_as="./laws_final2_reverse.json"
                with open(save_as, 'w', encoding='utf-8') as outfile:
                    json.dump(total_res, outfile,indent="\t",ensure_ascii=False)
            except Exception as e: 
                with open("./except.txt","w") as f:
                    f.write(f"{lnl}\n")
    else:
        url = "https://www.law.go.kr/DRF/lawSearch.do?OC=yein4452&target=law&type=XML"
        response = urlopen(url).read()
        xml_data = ET.fromstring(response)
        totalCnt = int(xml_data.find('totalCnt').text)
        for i in range(int(totalCnt / 20)):
        # for i in range(int(totalCnt)):
            print(i)
            total_res.append(low_info_with_detail(xml_data))
        total_res=sum(total_res,[])

if __name__=="__main__":
    collect_law_info("law_list")