import cloudscraper
from bs4 import BeautifulSoup
#import lxml
#from lxml import etree
import requests
import pandas as pd
import re
import time

h={'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'}

def find_change_in_proc(become,was):
    res = (become-was)/was*100
    return res

def make_normal(arr):
    new_arr=[]
    for i in arr:
        if i.text!='-':
            new_arr.append(float(i.text.replace(",", "")))
    return new_arr

def change_in_proc(arr):
    arr = make_normal(arr)
    new_arr = []
    for i in range(len(arr)-1, 0, -1):
        new_arr.append(find_change_in_proc(arr[i-1], arr[i]))

    return round(sum(new_arr),2), len(new_arr)

def get_normal_back(arr):
    for i in range(len(arr)-1,-1,-1):
        if arr[i].text != '-':
            return arr[i].text

    return '0'

def get_normal_start(arr):
    for i in range(0,len(arr)-1):
        if arr[i].text != '-':
            return arr[i].text

    return '0'

def count_avg(arr):
    res_arr=[]
    for i in arr:
        if i.text == '-':
            continue
        res_arr.append(float((i.text).replace("%", "").replace(",", "")))

    res = round(sum(res_arr)/len(res_arr),2)
    return res

def count_avg_only_pos(arr):
    res_arr=[]
    neg=True
    for i in arr:
        if i.text == '-':
            continue
        
        num = float((i.text).replace("%", "").replace(",", ""))
        if num<0:
            neg=False
            continue
        res_arr.append(num)

    print("P/E positive:",neg)
    res = round(sum(res_arr)/len(res_arr),2)
    return res

def CFF_and_OCF(cff, ocf):
    cff_res = []
    ocf_res = []
    for i in range(0,len(cff)-1):
            
        cff_num = float((cff[i].text).replace(",", ""))
        ocf_num = float((ocf[i].text).replace(",", ""))
        
        if cff[i]!='-' and cff_num > 0:
            cff_res.append(True)
        if ocf[i]!='-' and ocf_num < 0:
            ocf_res.append(True) 
    
    if len(cff_res) >= (len(cff)/2):
        cff_res = True
    else:
        cff_res = False
        
    if len(ocf_res) >= (len(ocf)/2):
        ocf_res = True
    else:
        ocf_res = False
        
    #print('OCF (Operating Cash Flow) < 0:',ocf_res)
    #print('CFF (Financing Cash Flow) > 0:',cff_res)    
        
    if ocf_res == True or cff_res == True:
        return False
    
    return True

def ocf(ocf):
    ocf_res = []
    for i in range(0,len(ocf)-1):
            
        ocf_num = float((ocf[i].text).replace(",", ""))
        
        if ocf[i]!='-' and ocf_num > 0:
            ocf_res.append(True)
 
    if len(ocf_res) >= len(ocf)/2:
        return True 
    return False
        
def cff(cff):
    cff_res = []
    for i in range(0,len(cff)-1):
            
        cff_num = float((cff[i].text).replace(",", ""))
        
        if cff[i]!='-' and cff_num < 0:
            cff_res.append(True)
 
    if len(cff_res) >= len(cff)/2:
        return True 
    return False

def sleep(scraper,url):
    time.sleep(60)
    page = scraper.get(url, headers=h)
    return page
        

def scrape_stockanalysis(tick):
    stock_info={}

    scraper = cloudscraper.create_scraper()
    url_income = 'https://stockanalysis.com/stocks/' + tick + '/financials/'
    url_balance_sheet = 'https://stockanalysis.com/stocks/' + tick + '/financials/balance-sheet/'
    url_cash_flow = 'https://stockanalysis.com/stocks/' + tick + '/financials/cash-flow-statement/'
    url_rations = 'https://stockanalysis.com/stocks/' + tick + '/financials/ratios/'
    
    # rations get
    page = scraper.get(url_rations, headers=h)
    if str(page) == '<Response [404]>':
        return None
    print(tick, page)
    soup_rations = BeautifulSoup(page.text, "lxml")
    
    try:
        url = 'https://stockanalysis.com/stocks/'+tick+'/'
        y_page = requests.get(url)
        print(y_page)
        soup = BeautifulSoup(y_page.text, "lxml")
        price = float(soup.body.find(class_='text-4xl font-bold inline-block').text)
        print(price)
    except:
        price = None   
    
    try:
        fiv_year_pe = soup_rations.body.find(text='PE Ratio').find_parent('tr').findAll('td')[1:6]
        fiv_year_pe = count_avg_only_pos(fiv_year_pe)
        #print('PE:',fiv_year_pe)
    except:
        fiv_year_pe = None
    
    try:
        fiv_year_ROIC = soup_rations.body.find(text='Return on Capital (ROIC)').find_parent('tr').findAll('td')[1:6]
        fiv_year_ROIC = count_avg(fiv_year_ROIC)
        #print('ROIC:',fiv_year_ROIC,"%")
    except:
        fiv_year_ROIC = None
        
    try:
        debt_to_equity = soup_rations.body.find(text='Debt / Equity Ratio').find_parent('tr').findAll('td')[1:]
        debt_to_equity = float(get_normal_start(debt_to_equity))
        #print('Debt / Equity Ratio:', float(debt_to_equity))
    except:
        debt_to_equity = None
        
    try:
        fiv_year_p_fcf = soup_rations.body.find(text='P/FCF Ratio').find_parent('tr').findAll('td')[1:6]
        fiv_year_p_fcf = count_avg(fiv_year_p_fcf)
        #print('5 year price / 5 free cash flow :', fiv_year_p_fcf)
    except:
        fiv_year_p_fcf = None
        
    try:
        market_cap = soup_rations.body.find(text='Market Capitalization').find_parent('tr').findAll('td')[1:]
        market_cap = float(get_normal_start(market_cap).replace(",", ""))
    except:
        market_cap = None
        
    stock_info['PE']=fiv_year_pe
    stock_info['ROIC (%)'] = fiv_year_ROIC
    stock_info['Debt / Equity Ratio'] = debt_to_equity
    stock_info['5 year price / 5 free cash flow'] = fiv_year_p_fcf
    stock_info['Market Capitalization'] = market_cap

    #income get
    page = scraper.get(url_income)
    soup_income = BeautifulSoup(page.text, "lxml")
    
    try:
        eps_f = soup_income.body.find(text='EPS (Basic)').find_parent('tr').findAll('td')[1:6]
        eps = float(get_normal_start(eps_f))
    except:
        eps = None
        
    try:
        fiv_year_Revenue = soup_income.body.find(text='Revenue').find_parent('tr').findAll('td')[1:6]
        fiv_year_Revenue,_ = change_in_proc(fiv_year_Revenue)
        #print('Revenue growth:',fiv_year_Revenue,'%')
    except:
        fiv_year_Revenue = None
        
    try:
        fiv_year_Net_Income = soup_income.body.find(text='Net Income').find_parent('tr').findAll('td')[1:6]
        Net_Income_now = float(get_normal_start(fiv_year_Net_Income).replace(",", ""))
        fiv_year_Net_Income,net_Income_count = change_in_proc(fiv_year_Net_Income)
        #print('Net Income growth:',fiv_year_Net_Income,'%')
        #print('Net Income now:', Net_Income_now,'$')
    except:
        fiv_year_Net_Income = None
        Net_Income_now = None
        
    try:
        fiv_year_EPS = soup_income.body.find(text='EPS (Basic)').find_parent('tr').findAll('td')[1:6]
        fiv_year_EPS,_ = change_in_proc(fiv_year_EPS)
        #print('EPS growth:', fiv_year_EPS,'%')
    except:
        fiv_year_EPS = None
        
    try:
        fiv_year_Shares_Outstanding = soup_income.body.find(text='Shares Outstanding (Basic)').find_parent('tr').findAll('td')[1:6]
        fiv_year_Shares_Outstanding,_ = change_in_proc(fiv_year_Shares_Outstanding)
        #print('Shares Outstanding growth:', fiv_year_Shares_Outstanding,'%')
    except:
        fiv_year_Shares_Outstanding = None
        
    try:
        fiv_year_EBITDA = soup_income.body.find(text='EBITDA').find_parent('tr').findAll('td')[1:6]
        fiv_year_EBITDA,count = change_in_proc(fiv_year_EBITDA)
        fiv_year_EBITDA = round(fiv_year_EBITDA / count,2)
        #print(fiv_year_EBITDA)
    except:
        fiv_year_EBITDA = None
        
    try:
        Research_and_Development = soup_income.body.find(text='Research & Development').find_parent('tr').findAll('td')[1:6]
        Research_and_Development,_ = change_in_proc(Research_and_Development)
    except:
        Research_and_Development = None
        #print(Research_and_Development)
    
    try:
        fiv_year_Other_Expense_to_Income = soup_income.body.find(text='Other Expense / Income').find_parent('tr').findAll('td')[1:6]
        fiv_year_Other_Expense_to_Income,_ = change_in_proc(fiv_year_Other_Expense_to_Income)
        #print(fiv_year_Other_Expense_to_Income)
    except:
        fiv_year_Other_Expense_to_Income = None

    stock_info['Revenue growth (%)'] = fiv_year_Revenue
    stock_info['Net Income growth (%)'] = fiv_year_Net_Income
    stock_info['Net Income now ($)'] = Net_Income_now
    stock_info['EPS growth (%)'] = fiv_year_EPS
    stock_info['Shares Outstanding growth (%)'] = fiv_year_Shares_Outstanding
    stock_info['Price'] = price
    stock_info['EPS'] = eps
    stock_info['5 year AVG EBITDA'] = fiv_year_EBITDA
    stock_info['Research & Development'] = Research_and_Development
    stock_info['Other Expense / Income'] = fiv_year_Other_Expense_to_Income

    #cash flow get
    page = scraper.get(url_cash_flow)
    soup_cash_flow = BeautifulSoup(page.text, "lxml")

    try:
        fiv_year_free_cash_flow = soup_cash_flow.body.find(text='Free Cash Flow').find_parent('tr').findAll('td')[1:6]
        
        fiv_year_free_cash_flow_avg = count_avg(fiv_year_free_cash_flow)
        free_cash_flow_now = float(get_normal_start(fiv_year_free_cash_flow).replace(",", ""))
        fiv_year_free_cash_flow,_ = change_in_proc(fiv_year_free_cash_flow)
        #print('Free cash flow avg:', fiv_year_free_cash_flow_avg)
        #print('Free cash flow growth:', fiv_year_free_cash_flow,'%')
        #print('Free cash flow now:', free_cash_flow_now,'$')
    except:
        fiv_year_free_cash_flow_avg = None
        fiv_year_free_cash_flow = None
        free_cash_flow_now = None
        
    stock_info['Free cash flow avg'] = fiv_year_free_cash_flow_avg
    stock_info['Free cash flow growth (%)'] = fiv_year_free_cash_flow
    stock_info['Free cash flow now ($)'] = free_cash_flow_now
    
    try:
        fiv_year_CFF = soup_cash_flow.body.find(text='Financing Cash Flow').find_parent('tr').findAll('td')[1:6]
        stock_info['CFF'] = cff(fiv_year_CFF)
    except:
        stock_info['CFF'] = None
        
    try:
        fiv_year_OCF = soup_cash_flow.body.find(text='Operating Cash Flow').find_parent('tr').findAll('td')[1:6]
        stock_info['OCF'] = ocf(fiv_year_OCF)
    except:
        stock_info['OCF'] = None
        
    #print(stock_info['CFF'], stock_info['OCF'] )    
    

    # balance sheet
    page = scraper.get(url_balance_sheet)
    soup_balance = BeautifulSoup(page.text, "lxml")

    try:
        Total_Long_Term_Liabilities = soup_balance.body.find(text='Total Long-Term Liabilities').find_parent('tr').findAll('td')[1:]
        Total_Long_Term_Liabilities = float(get_normal_start(Total_Long_Term_Liabilities).replace(",", ""))
    except:
        Total_Long_Term_Liabilities = None
        
    try:    
        Total_Assets = soup_balance.body.find(text='Total Assets').find_parent('tr').findAll('td')[1:]
        Total_Assets = float(get_normal_start(Total_Assets).replace(",", ""))
        #print(Total_Assets)
    except:
        Total_Assets = None
        
    try:    
        Total_Debt = soup_balance.body.find(text='Total Debt').find_parent('tr').findAll('td')[1:]
        Total_Debt = float(get_normal_start(Total_Debt).replace(",", ""))
        #print(Total_Debt)
    except:
        Total_Debt = None
        
    stock_info['Total Long-Term Liabilities ($)'] = Total_Long_Term_Liabilities
    stock_info['Total Debt'] = Total_Debt
    stock_info['Total Assets'] = Total_Assets
    
    change = 0    
    try:
        eps_avg = count_avg(eps_f)
        real_price = eps_avg * (8.5 + 2 * fiv_year_Net_Income/net_Income_count) * 4.4 / 4.8
        real_price = round(real_price,2)
        change = round(find_change_in_proc(real_price, price),2)
    except:
        real_price = None
    
    #print(stock_info)
    return stock_info,change

def calculations(stock_info):
    #print(stock_info)
    arr_1 = []
    arr_2=[]
    
    if stock_info['PE'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['PE']<=22.5)
        arr_2.append(stock_info['PE'])
        #print(1, stock_info['PE']<=22.5,stock_info['PE'])
     
    if stock_info['Price'] == None or stock_info['EPS'] == None or stock_info['EPS'] == 0:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        res = round(stock_info['Price'] / stock_info['EPS'] ,2)
        arr_1.append(res<=22.5)
        arr_2.append(res)
        #print(2, res<=22.5, res)
    
    if stock_info['ROIC (%)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['ROIC (%)']>=9)
        arr_2.append(stock_info['ROIC (%)'])
        #print(3, stock_info['ROIC (%)']>=9, stock_info['ROIC (%)'])
        
    if stock_info['Debt / Equity Ratio'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Debt / Equity Ratio']<1)
        arr_2.append(stock_info['Debt / Equity Ratio'])
        #print(4, stock_info['Debt / Equity Ratio']<1, stock_info['Debt / Equity Ratio'])

    if stock_info['Total Debt'] == None or stock_info['Total Assets'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        res = round(stock_info['Total Debt'] / stock_info['Total Assets'], 2)
        arr_1.append(res<=0.7)
        arr_2.append(res)
        #print(5, (res<=0.7, res))
        
    if stock_info['5 year price / 5 free cash flow'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['5 year price / 5 free cash flow'] < 20)
        arr_2.append(stock_info['5 year price / 5 free cash flow'])
        #print(6, stock_info['5 year price / 5 free cash flow'] < 20, stock_info['5 year price / 5 free cash flow'])
        
    if stock_info['Revenue growth (%)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Revenue growth (%)'] > 0)
        arr_2.append(stock_info['Revenue growth (%)'])
        #print(7, (stock_info['Revenue growth (%)'] > 0, stock_info['Revenue growth (%)']))
        
    if stock_info['Net Income growth (%)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Net Income growth (%)'] > 0)
        arr_2.append(stock_info['Net Income growth (%)']) 
        #print(8, stock_info['Net Income growth (%)'] > 0, stock_info['Net Income growth (%)'])
        
    if stock_info['EPS growth (%)'] == None or stock_info['ROIC (%)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['EPS growth (%)'] > stock_info['ROIC (%)'])
        arr_2.append(round(stock_info['EPS growth (%)'] - stock_info['ROIC (%)'],2))
        #print(9, stock_info['EPS growth (%)'] > stock_info['ROIC (%)'], round(stock_info['EPS growth (%)'] - stock_info['ROIC (%)'],2))
        
    if stock_info['Shares Outstanding growth (%)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Shares Outstanding growth (%)'] < 0)
        arr_2.append(stock_info['Shares Outstanding growth (%)']) 
        #print(10, stock_info['Shares Outstanding growth (%)'] < 0, stock_info['Shares Outstanding growth (%)'])
        
    if stock_info['Free cash flow growth (%)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Free cash flow growth (%)'] > 0)
        arr_2.append(stock_info['Free cash flow growth (%)']) 
        #print(11, stock_info['Free cash flow growth (%)'] > 0, stock_info['Free cash flow growth (%)'])
        
    if stock_info['Free cash flow now ($)'] == None or stock_info['Net Income now ($)'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Free cash flow now ($)'] > stock_info['Net Income now ($)'])
        arr_2.append(round(stock_info['Free cash flow now ($)'] - stock_info['Net Income now ($)'], 2))
        #print(12, stock_info['Free cash flow now ($)'] > stock_info['Net Income now ($)'], round(stock_info['Free cash flow now ($)'] - stock_info['Net Income now ($)'], 2))
        
    if stock_info['Total Long-Term Liabilities ($)'] == None or stock_info['Free cash flow avg'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        res = stock_info['Total Long-Term Liabilities ($)'] / stock_info['Free cash flow avg']
        arr_1.append(res < 5)
        arr_2.append(round(5 - res,2))
        #print(13, res < 5, round(5 - res,2))
        
    if stock_info['Total Long-Term Liabilities ($)'] == None or stock_info['Market Capitalization'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        res = 0.5 * stock_info['Market Capitalization']
        arr_1.append(stock_info['Total Long-Term Liabilities ($)'] <= res)
        arr_2.append(round(stock_info['Total Long-Term Liabilities ($)'] - res,2))
        #print(14, stock_info['Total Long-Term Liabilities ($)'] <= res, round(stock_info['Total Long-Term Liabilities ($)'] - res,2))
        
    if stock_info['5 year AVG EBITDA'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['5 year AVG EBITDA'] >= 10)
        arr_2.append(stock_info['5 year AVG EBITDA']) 
        #print(15, stock_info['5 year AVG EBITDA'] >= 10, stock_info['5 year AVG EBITDA'])
        
    if stock_info['CFF'] == None or stock_info['OCF'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        if stock_info['CFF'] == True and stock_info['OCF'] == True:
            arr_1.append(True)
            arr_2.append(True)
            #print(16, True, True)
        else:
            arr_1.append(False)
            arr_2.append(False)
            
        
    if stock_info['Research & Development'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Research & Development']>0)
        arr_2.append(stock_info['Research & Development']) 
        #print(17, stock_info['Research & Development']>0, stock_info['Research & Development'])
        
    if stock_info['Other Expense / Income'] == None:
        #print('b')
        arr_1.append(None) 
        arr_2.append(None)
    else:
        arr_1.append(stock_info['Other Expense / Income']<100)
        arr_2.append(stock_info['Other Expense / Income']) 
        #print(18, stock_info['Other Expense / Income']<100, stock_info['Other Expense / Income'])
            
    return arr_1, arr_2

def fill(df, tick, real_price, results, arr_1, arr_2):
    full_arr=[]
    for i in range(0,len(arr_1)):
        arr=[]
        arr.append(arr_1[i])
        arr.append(arr_2[i])
        full_arr.append(arr)
    #print(full_arr)
    #print(full_arr)
    df = df.append({'Ticker' : tick, 'Future price growth(%)':real_price, 'Results':results, '5 year P/E <= 22.5': full_arr[0], 'P/EPS':full_arr[1],'5 year ROIC >= 9%': full_arr[2], 'Debt/Equity < 1': full_arr[3], 
                    'Debt/Assets <= 0.7':full_arr[4], '5 year price / free cash flow < 20': full_arr[5], 'Revenue growth (%) > 0': full_arr[6], 
                    'Net Income growth (%) > 0': full_arr[7], 'EPS 5year growth > ROIC': full_arr[8], 'Shares Outstanding growth (%) < 0': full_arr[9], 
                    'Free cash flow growth (%) > 0': full_arr[10], 'Free cash flow > Net income':full_arr[11], 
                    'Long term liabilities / 5year Free cash flow < 5': full_arr[12], 'Long term liabilities <= 0.5 * market capitalization':full_arr[13], 
                    '5 year AVG EBITDA >= 10%':full_arr[14], 'OCF (Operating Cash Flow) < 0 & CFF (Financing Cash Flow) > 0':full_arr[15],
                    'Research & Development > 0':full_arr[16], 'Other Expense / Income':full_arr[17]}, ignore_index=True)
                    #'Interest Coverage' : full_arr[12], 'Piotroski F-Score' : full_arr[13], 'Altman Z-Score' : full_arr[14], 'Financial Strength' :full_arr[15], 
                    #'Profitability Rank' : full_arr[16], 'Growth Rank' : full_arr[17], 'Rations Rank' : full_arr[18]} ,ignore_index=True)

    return df,full_arr

def guru(tick, arr,arr2):
    scraper = cloudscraper.create_scraper()
    url = 'https://www.gurufocus.com/stock/'+tick+'/summary?search=#financial-strength'

    page = scraper.get(url)
    soup = BeautifulSoup(page.text, "lxml")
    
    
    financial_strength = float(soup.body.find(text=re.compile('Financial Strength')).find_parent('div').find('span', class_='t-default bold').text)
    #print('Financial Strength:',financial_strength)

    profitability_rank = float(soup.body.find(text=re.compile('Profitability Rank')).find_parent('div').find('span', class_='t-default bold').text)
    #print('Profitability Rank:', profitability_rank)

    growth_rank = float(soup.body.find(text=re.compile('Growth Rank')).find_parent('div').find('span', class_='t-default bold').text)
    #print('Growth Rank:', growth_rank)

    GF_value_rank = float(soup.body.find(text=re.compile('GF Value Rank')).find_parent('div').find('span', class_='t-default bold').text)
    #print('Rations Rank:', GF_value_rank)

    interest_coverage = float(soup.find('tbody').findAll('tr')[4].findAll('td')[2].find('span', class_='p-l-sm').text)
    #print('Interest Coverage:', interest_coverage)

    piotroski_f_score = float(soup.find('tbody').findAll('tr')[5].findAll('td')[2].find('span', class_='p-l-sm').text.split('/')[0].strip())
    #print('Piotroski F-Score:', piotroski_f_score)

    altman_z_score = float(soup.find('tbody').findAll('tr')[6].findAll('td')[2].find('span', class_='p-l-sm').text)
    #print('Altman Z-Score:', altman_z_score)
    
    arr.append(interest_coverage)
    arr.append(piotroski_f_score)
    arr.append(altman_z_score)
    arr.append(financial_strength)
    arr.append(profitability_rank)
    arr.append(growth_rank)
    arr.append(GF_value_rank)
    
    arr2.append(interest_coverage>=20)
    arr2.append(piotroski_f_score>=7)
    arr2.append(altman_z_score>=1.81)
    arr2.append(financial_strength>=7)
    arr2.append(profitability_rank>=7)
    arr2.append(growth_rank>=7)
    arr2.append(GF_value_rank>=7)
    
    return arr,arr2
    


def get_ticks_2():
    f = open("nasdaq_screener.csv", "r")
    arr=[]
    
    for x in f:
        arr.append(x.split(',')[0])
    return arr

def get_ticks():
    f = open("nasdaq_screener.csv", "r")
    arr=[]
    
    for x in f:
        if x=="":
            continue
        arr.append(x.strip())
    return arr

def get_results(arr_1):
    count=0
    for i in arr_1:
        if i == True:
            count+=1
    return count
    
    
if __name__ == '__main__':
    df = pd.DataFrame({'Ticker' : [] , 'Future price growth(%)':[], 'Results':[], '5 year P/E <= 22.5': [], 'P/EPS':[], '5 year ROIC >= 9%': [], 'Debt/Equity < 1': [], 'Debt/Assets <= 0.7': [], '5 year price / free cash flow < 20': [],
                       'Revenue growth (%) > 0': [], 'Net Income growth (%) > 0': [], 'EPS 5year growth > ROIC': [],
                       'Shares Outstanding growth (%) < 0': [], 'Free cash flow growth (%) > 0': [], 'Free cash flow > Net income':[],
                       'Long term liabilities / 5year Free cash flow < 5': [], 'Long term liabilities <= 0.5 * market capitalization':[], 
                       '5 year AVG EBITDA >= 10%':[], 'OCF (Operating Cash Flow) < 0 & CFF (Financing Cash Flow) > 0':[], 'Research & Development > 0':[],
                       'Other Expense / Income':[]})
                       #'Interest Coverage' : [], 'Piotroski F-Score' : [],
                       #'Altman Z-Score' : [], 'Financial Strength' : [], 'Profitability Rank' : [], 'Growth Rank' : [], 'Rations Rank' : []})
    
    tick = 'AA'
    stock_info_stockanalysis,real_price = scrape_stockanalysis(tick)
    arr_1,arr_2 = calculations(stock_info_stockanalysis)
    results = get_results(arr_1) 
    df,data = fill(df, tick, real_price, results, arr_1, arr_2)
    
                       
    #all_ticks = get_ticks() 

    #print(all_ticks)
    #count=0
    #last_tick='a'
    #for tick in all_ticks:
       # count+=1
        #last_tick = tick
       # if count==4:
      #      break
        #print(tick)
      #  try:
   #         stock_info_stockanalysis,real_price = scrape_stockanalysis(tick)
   #     except:
   #         continue
   #     arr_1,arr_2 = calculations(stock_info_stockanalysis)
   #     results = get_results(arr_1) 
   #     df,data = fill(df, tick, real_price, results, arr_1, arr_2)
        
   #     print()
   #     time.sleep(5)
    
   # try:
   #     ex_df = pd.read_excel('Results.xlsx')
   #     ex_df = ex_df.reset_index(drop=True)
   #     res = pd.concat([ex_df, df], axis=0)
   # except:
   #     res = df
    
   # writer = pd.ExcelWriter('Results.xlsx', engine='xlsxwriter')
   # res.to_excel(writer, sheet_name='stock_list', index=False)
   # writer.save()
    
   # index = all_ticks.index(last_tick)
    #print(index)
   # with open('nasdaq_screener.csv', 'w') as fp:
   #     for item in all_ticks[index:]:
   #         # write each item on a new line
   #         fp.write("%s\n" % item)





