import requests, sys, time, datetime
from bs4 import BeautifulSoup as bs 
import psycopg2 as psql 

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
    cur.execute(query, (timestamp, ticker, price))

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
    except:
        print(f'[-] For some reason, not able to get the price for {ticker}')
        price = '0.00'


    return price

def main():
    try:
        # ticker
        # low
        # high
        ticker = sys.argv[1]
        low = sys.argv[2]
        high = sys.argv[3]

    except:
        print(f'[-] Usage: {sys.argv[0]} <ticker> <low price> <high price>')
        return 1

    conn, cur = dbconnect()

    while True:
        price = pagePull(ticker)
        if float(price) > float(high):
            print(f'[-] {ticker} has exceeded the high price @ ${price}')
        elif float(price) < float(low):
            print(f'[-] {ticker} has gone below the low price @ ${price}')
        else:
            print(f'[-] Stock price has stayed the same!')
        insertdb(conn, cur, ticker, price)
        time.sleep(3)

    return 0

if __name__ == '__main__':
    main()