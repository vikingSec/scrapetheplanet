import requests, sys, time, datetime
from bs4 import BeautifulSoup as bs 
import psycopg2 as psql 
import threading

def dbconnect():
    # Open config file, connect using that data
    config = open('./config.txt', 'r')
    lines = config.readlines()
    config.close()
    ip = lines[0].strip()
    dbname = lines[1].strip()
    username = lines[2].strip()
    password = lines[3].strip()

    conn = psql.connect(database = dbname, user = username, password = password, host=ip, port=5432)
    conn.set_session(autocommit=True)
    cur = conn.cursor() 

    intitial_query = """
    CREATE TABLE IF NOT EXISTS stock_data
    (timestamp TEXT NOT NULL PRIMARY KEY, ticker TEXT NOT NULL, price FLOAT8 NOT NULL);
    """
    cur.execute(intitial_query)

    return conn, cur

def insertdb(conn, cur, ticker, price):
    query = """
    INSERT INTO stock_data
    (timestamp, ticker, price)
    VALUES (%s, %s, %s)"""

    timestamp = datetime.datetime.now()
    cur.execute(query, (ticker+str(timestamp), ticker, price))

    return 

def pagePull(ticker):
    pagelink = 'https://finance.yahoo.com/quote/'+ticker
    res = requests.get(pagelink)
    soup = bs(res.text, 'html.parser')

    try:
        price = ''
        quote_div = soup.find('div', id='quote-header-info')
        prices = quote_div.find_all('span', attrs={'data-reactid':"49"})
        price = prices[0].text
        print(price)
    except Exception as e:
        print(f'[-] For some reason, not able to get the price for {ticker}\n\t{str(e)}')
        price = '0.00'


    return price

def serviceThread(key, value, stocks_obj, conn, cur):
    ticker = key 
    low = float(value['low'])
    high =float(value['high'])
    price = pagePull(ticker).replace(',','')
    if float(price) > float(high):
        print(f'[-] {ticker} has exceeded the high price @ ${price}')
    elif float(price) < float(low):
        print(f'[-] {ticker} has gone below the low price @ ${price}')
    else:
        print(f'[-] Stock price has stayed the same!')
    insertdb(conn, cur, ticker, price)

    return

def main():
    stocks_obj = {}
    try:
        # ticker = sys.argv[1]
        # low = sys.argv[2]
        # high = sys.argv[3]
        stocks = open('./stocks.data','r')
        lines = stocks.readlines()
        stocks.close()
        for line in lines:
            spl = line.split(',')
            ticker = spl[0].strip()
            low = spl[1].strip()
            high = spl[2].strip()
            stocks_obj[ticker] = {'low':low, 'high':high}

    except:
        print(f'[-] Usage: {sys.argv[0]} <ticker> <low price> <high price>')
        return 1

    conn, cur = dbconnect()

    # Single-threaded: 0:01:12.021579
    # Multi-threaded: 0:00:21.312662
    start = datetime.datetime.now()
    BATCH_SIZE = 4
    
    arr = list(stocks_obj.items())
    print(len(arr))
    while True:

        index = 1
        batch = arr[:BATCH_SIZE*index]
        while len(batch) > 0:
            
            threads = []
            for key, value in batch:
                print(f'[-] Scraping ticker {key}')
                thread = threading.Thread(target=serviceThread, args = (key, value, stocks_obj, conn, cur))
                thread.start()
                threads.append(thread)
            joined = 0
            for thread in threads:
                joined+=1
                print(f'[-] Joined {joined} out of {len(threads)}')
                thread.join()
            time.sleep(3)
            index+=1
            batch = arr[BATCH_SIZE*(index-1):BATCH_SIZE*index]
            
            print(batch)
        time.sleep(10)
    end = datetime.datetime.now()
    print(f'[-] Run time: {end-start}')
    return 0

if __name__ == '__main__':
    main()