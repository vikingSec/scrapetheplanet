import sys, requests, hashlib, time 
from bs4 import BeautifulSoup as bs
import psycopg2 as psql 

def connectdb(ip='', dbname='', username='', password=''):
    conn = psql.connect(database=dbname, user=username, password = password, host= ip, port=5432)
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    initial_query = """
    CREATE TABLE IF NOT EXISTS wiki_data
    (uuid TEXT NOT NULL PRIMARY KEY, link TEXT NOT NULL, length INTEGER NOT NULL, links TEXT[] NOT NULL, title TEXT NOT NULL);
    """

    cur.execute(initial_query)
    return conn, cur

def pullPage(pagelink=''):
    """
        X obj.link - hyperlink to object's page
        X obj.links - array of (internal) links contained in page
        X obj.length - length of page
        X obj.title - title of the page
        X obj.uuid - unique ID
    """
    obj = {}
    obj['link'] = pagelink 
    res = requests.get('https://wikipedia.org'+pagelink)
    restext = res.text 
    soup = bs(restext, 'html.parser')

    obj['title'] = soup.find('h1', id="firstHeading").text
    obj['length'] = len(restext)
    obj['uuid'] = hashlib.md5((obj["title"]+pagelink).encode()).hexdigest()
    print(f'\t[-] Hash for link {pagelink}: {obj["uuid"]}')
    hrefs = soup.find_all('a')
    obj['links'] = []
    for link in hrefs:
        try:
            href = link['href']
            if 'wiki' in href and ('http://' not in href and 'https://' not in href and 'www' not in href and '.org' not in href and '.jpg' not in href):
                obj['links'].append(href)

        except:
            continue
    return obj

def insertdb(obj={}, conn='', cur=''):
    query = """
    INSERT INTO wiki_data
    (link, title, uuid, length, links)
    VALUES (%s, %s, %s, %s, %s);
    """

    try:
        cur.execute(query, (obj['link'], obj['title'], obj['uuid'], obj['length'], obj['links']))
        return 'Success!'
    except Exception as e:
        if 'duplicate key' in str(e):
            print(f'[-] Key already exists for link {obj["link"]}')
            return 'Success!'
        return 'Fail: '+str(e)

    return 

def checkdb(obj, conn, cur):
    query = """
    SELECT uuid FROM wiki_data WHERE uuid = %s;
    """
    cur.execute(query, (obj['uuid'],))

    rows = cur.fetchall()

    return len(rows) > 0

def main():
    # take wikilink (internal) as input from user for rootnode
    try:
        rootnode = sys.argv[1]
    except:
        print('[x] Please run the script with one internal wikipedia link')
        return 
    try:
        config = open('./config.txt', 'r')
        lines = config.readlines()
        config.close()
    except:
        print('[x] No config file found!')
        return
    ip = lines[0].strip()
    username = lines[1].strip()
    dbname = lines[2].strip()
    password = lines[3].strip()


    conn, cur = connectdb(ip, dbname, username, password)

    queue = []

    queue.append(rootnode)
    while True:
        print(f'[-] Queue size: {len(queue)}')
        # queue is a list of links
        currnode = queue[0]
        # pullPage returns an object
        obj = pullPage(currnode)
        # Checkdb returns a boolean
        indb = checkdb(obj, conn, cur)

        if indb:
            print(f'[-] Object with link {obj["link"]} was already in DB, not adding links to queue')
        else:
            print(f'[-] Object with link {obj["link"]} was not in DB, adding {len(obj["links"])}')
            res = insertdb(obj, conn, cur)
            print(f'[-] Result of insertdb: {res}')
            for link in obj['links']:
                queue.append(link)
        queue = queue[1:]
        time.sleep(3)


    return 

if __name__ == '__main__':
    main()

