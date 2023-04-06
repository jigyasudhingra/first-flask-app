import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import re
from flask import request, Response

# To ignore the warnings
import warnings
warnings.filterwarnings("ignore") 

# Constants
BANK_SCRIPS = ['HDFCBANK','ICICIBANK','AXISBANK','KOTAKBANK','SBIN','CANBK']
IT_SCRIPS = ['INFY', 'HCLTECH', 'TCS','LTTS', 'WIPRO' ]
SCRIPS = BANK_SCRIPS
BASE_URL = 'https://www.screener.in/company/'

# PROFIT-LOSS STRATEGY - CONFIG
PROFIT_LOSS_YEARS = 3
SCREENER_ROW_PL = 'Net Profit' # or can be 'Profit before tax'
CURRENT_HIGH_THRESHOLD_PERCENT = 10

# ROE and ROCE should be greater than sector average - Eg. 20% more than sector average (ROE - 20, ROCE - 20 - or anything) 

# PE should be lower than sector average - Eg. Atleast 10% less than sector average

def extract_table_by_class(soup, section_id, class_name):
    section_html = soup.find('section',{'id': section_id})
    table_html = section_html.find('table',{'class': class_name})

    headers = []
    for header in table_html.find_all('th'):
        headers.append(  header.text or 'Type')

    table_df = pd.DataFrame(columns = headers)

    for row_element in table_html.find_all('tr')[1:]:
            row_data = row_element.find_all('td')
            row = [tr.text.strip() for tr in row_data]
            length = len(table_df)
            table_df.loc[length] = row 
            
    return table_df
    
def fetch_number_span(list_element):
    num_span = list_element.find('span',{'class':'number'})
    num_span = num_span.text.replace(',', '')
    return float(num_span) if (num_span != '') else 0.0
    
def extract_scrip_ratios(soup,div_class, ul_id):
    div_html = soup.find('div',{'class': div_class})
    ul_html = div_html.find('ul',{'id': ul_id})
    current_price = 0
    high = 0.0
    low = 0.0
    dividend_yield = 0.0
    pe = 0.0
    roe = 0.0
    roce = 0.0
    market_cap = 0.0
     
    scrip_data = pd.Series()
    
    for li in ul_html.find_all("li"):
        name_span = li.find('span',{'class':'name'})
        
        if 'Current Price' in name_span.text: 
            current_price = fetch_number_span(li)

        if 'High / Low' in name_span.text:
            num_spans = li.find_all('span',{'class':'number'})
            if(len(num_spans) == 2):
                high_num = num_spans[0].text.replace(',', '')
                low_num = num_spans[1].text.replace(',', '')
                high = float(high_num) if (high_num != '') else 0.0
                low = float(low_num) if (low_num != '') else 0.0 
                
        if 'Market Cap' in name_span.text: 
            market_cap = fetch_number_span(li)
            
        if 'Stock P/E' in name_span.text:
            pe = fetch_number_span(li) 
            
        if 'Dividend Yield' in name_span.text:
            dividend_yield = fetch_number_span(li) 
            
        if 'ROCE' in name_span.text:
            roce = fetch_number_span(li) 
            
        if 'ROE' in name_span.text:
            roe = fetch_number_span(li) 
            
    scrip_data['Price'] = current_price
    scrip_data['High'] = high
    scrip_data['Low'] = low
    scrip_data['Market_Cap'] = market_cap
    scrip_data['PE'] = pe
    scrip_data['Dividend'] = dividend_yield
    scrip_data['ROCE'] = roce
    scrip_data['ROE'] = roe
    return scrip_data

def fetch_scrip_data(scrip):
    link = f'{BASE_URL}{scrip}'
    hdr = {'User-Agent':'Mozilla/5.0'}
    req = Request(link,headers=hdr)
    
    profit_loss_df = None
    scrip_data = pd.Series()
    try:
        page=urlopen(req)
        soup = BeautifulSoup(page)
        scrip_data = extract_scrip_ratios(soup,'company-ratios', 'top-ratios')
        profit_loss_df = extract_table_by_class(soup, 'profit-loss', 'data-table responsive-text-nowrap')
    except:
        print(f'EXCEPTION THROWN: UNABLE TO FETCH DATA')

    return scrip_data, profit_loss_df
 
def extract_last_n_years_pl(pl_df, n_years):
    # Extract data for all years from the column names
    mon_year_regex = re.compile('([A-Z][a-z]{2}) (\d{4})')
    years = {}
    for col in list(pl_df.columns):
        res = re.search(mon_year_regex,col)
        if res:
            years[res.group(2)] = col

    # Get only the last n (PROFIT_LOSS_YEARS) years for checking the P&L 
    years_list = sorted(years.keys())
    years_list = years_list[-n_years:]
    cols = [years[year] for year in years_list]
    pl_values = pl_df[cols].iloc[0, :].values.tolist()
    pl_values = [float(x.replace(',', '')) for x in pl_values] 
    return pl_values

# Check if current price is below the 52-week high with a certain threshold
# Eg: If current price is 100, 52-week high is 120, threshold is 10%, then return True
#     If current price is 100, 52-week high is 105, threshold is 10%, then return False
def check_current_below_high_threshold(current,high, threshold_percent):
    below_threshold = False
    if ((current < high) & ((high-current)/high*100 > threshold_percent)):
        below_threshold = True
    return below_threshold   

def apply_pl_strategy(current_price, scrip_high, profit_loss_df, high_threshold_percent):
    req = request.get_json()
    if req:
        if req.get('threshold') is not None:
            high_threshold_percent = req['threshold']
        if req.get('plYears') is not None:
            PROFIT_LOSS_YEARS = req['plYears']


    strategy_result = 'NOT BUY'
    try: 
        # CHECK IF REQUIRED VALUES COULD BE SCRAPED
        if (current_price is None or current_price == 0.0 or 
            scrip_high is None or scrip_high == 0.0):
            strategy_result = 'NOT FOUND'

        else:
            profit_loss_df = profit_loss_df[profit_loss_df['Type'] == SCREENER_ROW_PL]
            last_pl_list = extract_last_n_years_pl(profit_loss_df, PROFIT_LOSS_YEARS)
            print(f'Profit/Loss for last {PROFIT_LOSS_YEARS} years:{last_pl_list}')
            print(f'Current Price:{current_price}, 52-week High:{scrip_high}, Threshold%: {high_threshold_percent}%')

            # CHECK IF PROFIT-LOSS IS CONSISTENTLY INCREASING
            if(last_pl_list == sorted(last_pl_list)):
                # IF YES, CHECK IF CURRENT MARKET VALUE IS NOT AT ALL TIME HIGH
                if check_current_below_high_threshold(current_price, scrip_high, high_threshold_percent):
                    # BUY RECOMMENDATION
                    strategy_result = 'BUY'
    except:
        print(f"UNABLE TO APPLY PROFIT-LOSS STRATEGY")

    return strategy_result

def fundamentalAnalysis():
    req = request.get_json()
    if req.get('stocks') is not None:
        SCRIPS = req['stocks']
    else:
        return "Stocks is required field"

    final_df = pd.DataFrame({'Symbol':SCRIPS},
                            columns=['Symbol','Market_Cap','Price','High','Low','PE','ROE','ROCE','Dividend','STRATEGY_PL']).set_index('Symbol')
    res = {}
    for scrip in SCRIPS:
        print(f"\nSYMBOL: {scrip}")
        scrip_data, profit_loss_df = fetch_scrip_data(scrip)
        
        for index, value in scrip_data.items():
            final_df[index][scrip] = value

        strategy_result = apply_pl_strategy(scrip_data['Price'], scrip_data['High'], profit_loss_df, CURRENT_HIGH_THRESHOLD_PERCENT)
        print(f"APPLYING PROFIT/LOSS STRATEGY ON {scrip}: {strategy_result}")
        final_df['STRATEGY_PL'][scrip] = strategy_result
        res[scrip] = strategy_result
    return res