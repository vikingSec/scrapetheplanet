import requests as req
print(f'[-] Requests library is installed!')
import time
from bs4 import BeautifulSoup as soup

def main():
    # Main URL
    base_url = 'https://finance.yahoo.com/quote/'

    # Our tickers
    stocks = ['AAPL','MSFT', 'GME', 'GOOG', 'T','chickentendies']

    res = req.get(base_url)

    # Status codes
    # 200 - It succeeded
    # 404 - Page not found
    # 400 - Generic error
    # 302 - Redirected 

    print(f'[-] Status code: {res.status_code}')
    # https://finance.yahoo.com/quote/AAPL
    for ticker in stocks:
        stockpage = req.get(base_url+ticker)
        print(f'[-] Status code: {stockpage.status_code}')
        if stockpage.status_code == 200:
            # We succeeded!
            source = stockpage.text
            # Price element
            # <span class="Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)" data-reactid="49">148.76</span>
            parsedpage = soup(source, 'html.parser')

            # Grab the price
            try:
                price = parsedpage.find('span', attrs={'data-reactid':'49'}, class_='Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)').text
            except:
                price = parsedpage.find('span', class_='Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)').text
            print(f'[-] Ticker {ticker} has price {price}!')
            print(f'\t[-] {base_url+ticker}')
            
            # Grab the delta
            # <span class="Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($positiveColor)" data-reactid="50">+2.21 (+1.51%)</span>
            try:
                try:
                    delta = parsedpage.find('span', attrs={'data-reactid':'50'}).text
                except:
                    delta = parsedpage.find('span', class_='Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($negativeColor)').text
            except:
                try:
                    delta = parsedpage.find('span', attrs={'data-reactid':'50'}).text
                except:
                    delta = parsedpage.find('span', class_='Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($positiveColor)').text
            print(f'[-] Ticker {ticker} has delta {delta}')
            print(f'\t[-] {base_url+ticker}')


        else:
            # We failed!
            print(f'[x] Request to page {base_url+ticker} failed, status code: {stockpage.status_code}')
        time.sleep(1)

    #print(f'[-] Last page requested, raw html:\n\n\n{stockpage.text}')

    return 

if __name__ == '__main__':
    main()