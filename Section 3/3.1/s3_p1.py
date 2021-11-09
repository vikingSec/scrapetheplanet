import requests as req
import time

def main():
    # Main URL
    base_url = 'https://finance.yahoo.com/quote/'

    # Our tickers
    stocks = ['AAPL','MSFT', 'GME', 'GOOG', 'T']

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
        time.sleep(1)

    print(f'[-] Last page requested, raw html:\n\n\n{stockpage.text}')

    return 

if __name__ == '__main__':
    main()