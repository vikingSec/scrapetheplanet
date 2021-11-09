import requests as req
from bs4 import BeautifulSoup as soup
import json 
import sys

def main():
    # Actor name from user
    actor_name = sys.argv[1]

    # Base URL for search
    base_url = 'https://www.imdb.com/find?q='
    print(actor_name)

    searchreq = req.get(base_url+actor_name)
    print(searchreq.status_code)

    # The parent of what we want
    # <td class="result_text"> </td>
    # What we want
    # <a href="/name/nm0005458/?ref_=fn_al_nm_1">Jason Statham</a>
    searchsoup = soup(searchreq.text, 'html.parser')

    parent = searchsoup.find('td', class_='result_text')
    child = parent.find('a')['href']
    print(f'[-] Actor link: {child}')

    actor_link = 'https://imdb.com'+child

    actorpage = req.get(actor_link)
    actorsoup = soup(actorpage.text, 'html.parser')
    # class=filmo-category-section
    actortable = actorsoup.find('div', class_='filmo-category-section')
    movies = actortable.find_all('b')

    actor_object = {}
    actor_object['name'] = actor_name
    actor_object['link'] = actor_link
    actor_object['movies'] = []

    for movie in movies:
        movietitle = movie.find('a').text
        movielink = movie.find('a')['href']
        #print(f'[-] Movie: {movietitle} @ link: https://imdb.com{movielink}')
        movie_obj = {'title':movietitle, 'link':movielink}
        actor_object['movies'].append(movie_obj)
    
    #print(actor_object)

    f = open(actor_name+'.json', 'w')
    actor_json = json.dumps(actor_object)
    f.write(actor_json)
    f.close()


    


    return 

if __name__ == '__main__':
    main()