# Python version 3.7

import pandas as pd

import re, time
import datetime
from selenium import webdriver
from tabulate import tabulate
from bs4 import BeautifulSoup



def is_float(x):
    try:
        float(x)
    except ValueError:
        return False
    return True


def get_table_from_url(stock_name_to_num, prices, stock, try_num):
    prices = []
    if (try_num < 10):
        url = "https://www.tase.co.il/en/market_data/security/" + str(
            stock_name_to_num[stock]) + "/historical_data?pType=1&oId=0" + str(stock_name_to_num[stock])
        driver = webdriver.Firefox()  # executable_path = 'your/directory/of/choice'
        # get web page
        driver.get(url)
        # execute script to scroll down the page
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        # sleep for 10s
        time.sleep(5)
        # driver.quit()
        content = driver.page_source
        soup = BeautifulSoup(content, features='lxml')
        stock_prices = soup.find_all('script')
        # print("STOCK PRICES")
        # print (len(stock_prices))
        old_prices = 0
        old_prices = soup.find_all('td')
        prices = [x.text for x in old_prices]
        # prices.split("<td>")
    elif (try_num >= 10):
        return
    if (len(prices) < 40):
        driver.quit()
        get_table_from_url(stock_name_to_num, prices, stock, try_num + 1)
    driver.quit()
    return prices


def find_tlv_stock_price():
    stock_list_df = pd.read_excel('Stocks.xlsx', sheet_name="Stock Names")
    stock_list = stock_list_df['Stocks'].tolist()
    stock_names = stock_list_df['Names'].tolist()
    stock_name_to_num = dict(zip(stock_names, stock_list))
    all_slocks = {}
    for stock in stock_names:
        print(stock)
        web_df = pd.DataFrame(columns=['Date', 'Adj Close', 'Close', 'change', 'Open', 'Base', 'High', 'Low'])
        prices = []
        prices = get_table_from_url(stock_name_to_num, prices, stock, 0)
        if (prices == None):
            print(f"Can't find stock data {stock} moving to next stock")
            continue
        # Parse some of the web page
        row = []
        row_index = 0
        for x in prices:
            if (x == ''):
                continue
            elif "לינקים" in x:
                # print(row)
                web_df.loc[row_index] = row
                row_index += 1
                row = []
                continue
            else:
                x = x.replace(',', '')
                row.append(x)
                continue
        # remove unimportant columns
        web_df = web_df.drop(columns=['Adj Close'], axis=1)
        web_df = web_df.drop(columns=['change'], axis=1)
        web_df = web_df.drop(columns=['Base'], axis=1)
        # print(web_df)
        dates = []
        old_dates = web_df["Date"].tolist()
        for x in old_dates:
            x = x.strip()
            x = datetime.datetime.strptime(x, "%d/%m/%Y")
            x = x.strftime('%Y-%m-%d')
            dates.append(x)
        # print(dates)
        web_df["Date"] = dates
        web_df[['Close', 'Open', 'High', 'Low']] = web_df[['Close', 'Open', 'High', 'Low']].apply(pd.to_numeric)
        all_slocks[stock] = web_df.head(9)

    return all_slocks

def check_doji(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    if(abs(open0-close0)<((high0-low0)*0.2) or (abs(close0-open0)/close0<=0.003)) \
            and check_hammer_and_hanging_man(stocks_dict) == '' and check_inverted_hammer_and_shooting_star(stocks_dict) == '':
        return 'Doji, '
    return ''


def check_bullish_engulfing(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((open1>close1) and (open0<close0)
            and (close0 > open1) and (close1 > open0)
            and ((close0-open0) > (open1-close1))):
        return 'Bullish engulfing, '
    return ''


def check_bearish_engulfing(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((close1>open1) and (open0>close0)
            and (open0 > close1) and (open1 > close0)
            and ((open0-close0) > (close1-open1))):
        return 'Bearish engulfing, '
    return ''


def check_hammer_and_hanging_man(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    if (((close0 > open0) and ((high0 - low0) > 3 * (close0 - open0))
        and ((close0 - low0) / (0.001 + high0 - low0) > 0.6)
        and ((open0 - low0) / (0.001 + high0 - low0) > 0.6)
        and ((open0 - low0) / (0.001 + high0 - close0) > 4))\
        or ((open0 > close0) and ((high0 - low0) > 3 * (open0 - close0))
            and ((close0 - low0) / (0.001 + high0 - low0) > 0.6)
            and ((open0 - low0) / (0.001 + high0 - low0) > 0.6)
            and ((close0 - low0) / (0.001 + high0 - open0) > 4))):
        return "Hammer/Hanging man, "
    return ''


def check_piercing_line(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((close1<open1) and (((open1+close1)/2) < close0)
            and (open0 < close0) and (open0 < close1)
            and (close0 < open1) and ((close0-open0)/(0.001+(high0-low0)) > 0.6)):
        return "Piercing line, "
    return ''


def check_dark_cloud(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((close1>open1) and (((close1+open1)/2)>close0)
            and (open0>close0) and (open0>close1)
            and (close0>open1) and ((open0-close0)/(0.001+(high0-low0))>0.6)):
        return "Dark cloud, "
    return ''


def check_bullish_harami(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((open1>close1) and ((((close0>open0)
        and (close0 < open1) and (close1 < open0))
        or ((open0>close0) and (open1 > open0) and (close0 > close1))))
        and ((abs(close0-open0)) < (abs(open1-close1)))):
        return 'Bullish harami, '
    return ''



def check_bearish_harami(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((close1>open1) and ((((close0>open0)
        and (open1<open0) and (close1>close0))
        or ((open0>close0) and (close1>open0)
        and (open1<close0)))) and ((abs(open0-close0)) < (abs(close1-open1)))):
        return 'Bearish harami, '
    return ''


def check_morning_star(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    high1 = stocks_dict.iloc[1]['High']
    low1 = stocks_dict.iloc[1]['Low']
    open2 = stocks_dict.iloc[2]['Open']
    close2 = stocks_dict.iloc[2]['Close']
    high2 = stocks_dict.iloc[2]['High']
    low2 = stocks_dict.iloc[2]['Low']
    if((open2>close2) and ((open2-close2)/(0.001+high2-low2)>0.4)
            and (close2>max(close1,open1)) and ((high1-low1)>(3*abs(close1-open1)))
            and (close0>open0) and (open0>max(close1,open1)) and (close0>(close2+open2)/2)):
        return "Morning star, "
    return ''

def check_evening_star(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    high1 = stocks_dict.iloc[1]['High']
    low1 = stocks_dict.iloc[1]['Low']
    open2 = stocks_dict.iloc[2]['Open']
    close2 = stocks_dict.iloc[2]['Close']
    high2 = stocks_dict.iloc[2]['High']
    low2 = stocks_dict.iloc[2]['Low']
    if((close2>open2) and ((close2-open2)/(0.001+high2-low2)>0.4)
            and (close2<min(close1,open1)) and ((high1-low1)>(3*abs(close1-open1)))
            and (open0>close0) and (open0<min(close1,open1)) and (close0<(close2+open2)/2)):
        return 'Evening star, '
    return ''


def check_bullish_kicker(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((open1>close1) and (open0>=open1) and (close0>open0)):
        return 'Bullish kicker, '
    return ''


def check_bearish_kicker(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    if((open1<close1) and (open0<=open1) and (close0<open0)):
        return 'Bearish kicker, '
    return ''

def check_inverted_hammer_and_shooting_star(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    if(((open0>close0) and ((high0-low0)>3*(open0-close0))
        and ((high0-close0)/(0.001+high0-low0)>0.6)
        and ((high0-open0)/(0.001+high0-low0)>0.6)
        and ((close0-low0)/(0.001+high0-open0)<0.25))
        or ((close0>open0)
            and (abs(high0-low0)>3*(close0-open0))
            and ((high0-close0)/(0.001+high0-low0)>0.6)
            and ((high0-open0)/(0.001+high0-low0)>0.6)
            and ((open0-low0)/(0.001+high0-close0)<0.25))):
        return 'Inverted hammer/Shooting star, '
    return ''


def check_3_white_soldiers(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    high1 = stocks_dict.iloc[1]['High']
    low1 = stocks_dict.iloc[1]['Low']
    open2 = stocks_dict.iloc[2]['Open']
    close2 = stocks_dict.iloc[2]['Close']
    high2 = stocks_dict.iloc[2]['High']
    low2 = stocks_dict.iloc[2]['Low']
    if((close0>open0*1.01) and (close1>open1*1.01)
            and (close2>open2*1.01) and (close0>close1)
            and (close1>close2) and (open0>open1)
            and (open1>open2) and (((high0-close0)/(high0-low0))<0.2)
            and (((high1-close1)/(high1-low1))<0.2) and (((high2-close2)/(high2-low2))<0.2)):
        return '3 White soldiers, '
    return ''


def check_3_black_soldiers(stocks_dict):
    open0 = stocks_dict.iloc[0]['Open']
    close0 = stocks_dict.iloc[0]['Close']
    high0 = stocks_dict.iloc[0]['High']
    low0 = stocks_dict.iloc[0]['Low']
    open1 = stocks_dict.iloc[1]['Open']
    close1 = stocks_dict.iloc[1]['Close']
    high1 = stocks_dict.iloc[1]['High']
    low1 = stocks_dict.iloc[1]['Low']
    open2 = stocks_dict.iloc[2]['Open']
    close2 = stocks_dict.iloc[2]['Close']
    high2 = stocks_dict.iloc[2]['High']
    low2 = stocks_dict.iloc[2]['Low']
    if((open0>close0*1.01) and (open1>close1*1.01)
            and (open2>close2*1.01) and (close0<close1)
            and (close1<close2) and (open0>close1) and (open0<open1)
            and (open1>close2) and (open1<open2) and (((close0-low0)/(high0-low0))<0.2)
            and (((close1-low1)/(high1-low1))<0.2) and (((close2-low2)/(high2-low2))<0.2)):
        return '3 black doldiers, '
    return ''


def check_day_signals(stocks_dict):
    cur_signals = ''
    cur_signals += check_doji(stocks_dict)
    cur_signals += check_bullish_engulfing(stocks_dict)
    cur_signals += check_bearish_engulfing(stocks_dict)
    cur_signals += check_hammer_and_hanging_man(stocks_dict)
    cur_signals += check_piercing_line(stocks_dict)
    cur_signals += check_dark_cloud(stocks_dict)
    cur_signals += check_bullish_harami(stocks_dict)
    cur_signals += check_bearish_harami(stocks_dict)
    cur_signals += check_morning_star(stocks_dict)
    cur_signals += check_evening_star(stocks_dict)
    cur_signals += check_bullish_kicker(stocks_dict)
    cur_signals += check_bearish_kicker(stocks_dict)
    cur_signals += check_inverted_hammer_and_shooting_star(stocks_dict)
    cur_signals += check_3_white_soldiers(stocks_dict)
    cur_signals += check_3_black_soldiers(stocks_dict)
    if cur_signals != '':
        cur_signals = cur_signals[:-2]
    return cur_signals


def check_signals(stocks_dict):
    signals = pd.DataFrame(columns=['Name', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7'])
    for i, stock in enumerate(stocks_dict.keys()):
        stock_signals = []
        stock_signals.append(stock)

        for j in range (1,8):
            if j == 7:
                stock_signals.append(check_day_signals(stocks_dict[stock].iloc[j-1:]))
            else:
                stock_signals.append(check_day_signals(stocks_dict[stock].iloc[j-1:j+2]))

        signals.loc[i] = stock_signals
    print(tabulate(signals, headers='keys', tablefmt='grid'))
    # print(tabulate(signals, headers='keys', tablefmt='psql'))



if __name__ == "__main__":
    all_stocks = find_tlv_stock_price()
    check_signals(all_stocks)
