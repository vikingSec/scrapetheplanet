import requests 
import psycopg2 as psql 
from bs4 import BeautifulSoup as bs
import json, sys, time

DBUSER = 'testdb'
DBPASS = 'password'
DBHOST = '10.0.0.8'
MAX_DEPTH = 5

def getActorLink(actor = ''):
    searchreq = requests.get(f'https://imdb.com/find?q={actor}')
    if searchreq.status_code != 200:
        print(f'[x] Search for {actor} unsuccessful, error code {searchreq.status_code}')
        return
    searchreq_page = searchreq.text
    searchreq_bs = bs(searchreq_page, 'html.parser')
    # Parse for the Names table
    try:
        names_table = searchreq_bs.find_all('div', class_='findSection')[0]
        actor_link = f'https://imdb.com{names_table.find_all("a")[1]["href"]}'
    except:
        print(f'[-] Actor {actor} not found!')
        return ''
    # In the Names table, parse for the first link and pull it out as the actor link'

    return actor_link

def getActorMovies(actor_link = ''):
    actor_req = requests.get(actor_link)
    actor_page = actor_req.text
    # Parse for the filmography_actors table
    actor_bs = bs(actor_page, 'html.parser')
    try:
        actor_table = actor_bs.find('div', id='filmography').find_all('div', class_='filmo-category-section')[0].find_all('div', class_='filmo-row')
    except Exception as e:
        print(f'[x] Error on actor_link {actor_link} : {str(e)}\n\t\tStatus code: {actor_req.status_code}')
        return []
    # Create the movies array that will hold the movie objects
    movies = []

    # Print each movie
    for row in actor_table:
        movie_name = row.find_all('a')[0].text
        movie_link = f"https://imdb.com{row.find_all('a')[0]['href']}"
        # Parse out all the movies into objects, append them to the movies array
        movie_obj = {'name':movie_name.strip('()\"'), 'link':movie_link}
        movies.append(movie_obj)
    return movies

def getActorList(movie_obj = {}):
    actor_list = {}
    # TODO: Go from a movie object to a list of actors/actresses that were in said movie
    movie_link = movie_obj['link']
    try:
        movie_page = requests.get(movie_link)
    except:
        print(f'[x] Some sort of error occured in getActorList\nMovie Object: {movie_obj}')
        return []
    movie_bs = bs(movie_page.text, 'html.parser')
    try:
        feature_cast = movie_bs.find('section',attrs={'data-testid':'title-cast'})
        cast_members = feature_cast.find('div', class_='title-cast__grid').find_all('div',attrs={'data-testid':'title-cast-item'})
        print(f'[-] Found {len(cast_members)} cast members in {movie_obj["name"]} : {movie_link} !')
        for actor in cast_members:
            #print(actor.prettify())
            actor_name = actor.find('a',attrs={'data-testid':'title-cast-item__actor'}).text
            actor_link = actor.find('a', attrs={'data-testid':'title-cast-item__actor'})['href']
            actor_list[actor_name] = actor_link
    except Exception as e:
        print('[-] Skipping this movie, it\'s probably still in production')
        print(f'\t[-] {movie_link}')
        print(f'\t[-] Exception: {str(e)}')
        
    return actor_list

def get_actor_cache(name):
    #TODO: A function to return cached actor information in the DB
    # RETURNS: Returns an actor link and a list of movies
    name = name.strip('()\"')
    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=DBHOST, port=5432)
    cur = conn.cursor()
    actor_link = ''
    movie_list = []
    initial_query = """
    CREATE TABLE IF NOT EXISTS actor_data
    (actor_name TEXT NOT NULL, actor_link TEXT NOT NULL PRIMARY KEY, movie_list TEXT[] NOT NULL);
    """

    cur.execute(initial_query)
    conn.commit()

    query = """
    SELECT actor_link, movie_list FROM actor_data
    WHERE actor_name = %s;
    """
    
    cur.execute(query, (name,))
    rows = cur.fetchall()
    print(f'[-] Checked cache for {name}, number of results: {len(rows)}')
    for row in rows:
        actor_link = row[0]
        movie_list_db = row[1]
        for item in movie_list_db:
            # item = (name, link)
            # item = [name, link]
            try:
                item = item.strip('()\"')
                item_spl = item.split(',')
                name = item_spl[0]
                link = item_spl[1]
                movie_obj = {'name':name.strip('()\"'), 'link':link}
                movie_list.append(movie_obj)
            except:
                print(f'[x] Type {type(item)} : {item}')

    conn.close()
    return actor_link, movie_list

def cache_actor(actor = {}):
    #TODO: A function to store actor data in the DB
    
    movie_list = actor['movies']
    actor_link = actor['actor_link']
    actor_name = actor['actor_name'].strip('"').strip(' ')

    initial_query = """
    CREATE TABLE IF NOT EXISTS actor_data
    (actor_name TEXT NOT NULL, actor_link TEXT NOT NULL PRIMARY KEY, movie_list TEXT[] NOT NULL);
    """

    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=DBHOST, port=5432)
    cur = conn.cursor()

    cur.execute(initial_query)
    conn.commit()

    add_query = """
    INSERT INTO actor_data 
    (actor_name, actor_link, movie_list)
    VALUES (%s, %s, %s)
    """
    cleaned = []
    for movie in movie_list:
        cleaned.append((movie['name'],movie['link']))
    try:
        cur.execute(add_query, (actor_name, actor_link, list(cleaned)))
        print(f'[-] Committing the actor {actor_name}')
    except Exception as e:
        print(str(e))
        print(f'[-] {actor_name} already in database!')
    
    conn.commit()
    conn.close()
    return
    
def get_movie_cache(movie):
    #TODO: A function to return cached movie information in the DB
    # RETURNS: Returns a dictionary of actor_name:link pairs

    query = """
    SELECT actor_list FROM movie_data
    WHERE movie_link = %s;
    """
    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=DBHOST, port=5432)
    cur = conn.cursor()
    cur.execute(query, (movie['link'],))
    rows = cur.fetchall()

    actor_list = {}
    for row in rows:
        print(f'[-] Found movie {movie["name"]}!')
        res = row[0]
        for item in res:
            item = item.strip("()\"")
            item_spl = item.split(',')
            name = item_spl[0]
            link = item_spl[1]
            actor_list[name] = link
    conn.close()

    return actor_list

def cache_movie(movie = {}):
    #TODO: A function to store movie data in the DB

    actor_list = get_movie_cache(movie)
    if len(actor_list) == 0:
        actor_list = getActorList(movie)
    movie_link = movie['link']
    movie_name = movie['name'].strip('()\"')

    initial_query = """
    CREATE TABLE IF NOT EXISTS movie_data
    (movie_name TEXT NOT NULL, movie_link TEXT NOT NULL PRIMARY KEY, actor_list TEXT[] NOT NULL);
    """

    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=DBHOST, port=5432)
    cur = conn.cursor()

    cur.execute(initial_query)
    conn.commit()

    add_query = """
    INSERT INTO movie_data 
    (movie_name, movie_link, actor_list)
    VALUES (%s, %s, %s)
    """
    cleaned = []
    try:
        for name, link in actor_list.items():
            name = name.strip('()\"')
            cleaned.append((name.strip('()\"'),link))
        try:
            cur.execute(add_query, (movie_name, movie_link, cleaned))
            print(f'[-] Committing the movie {movie_name}')
        except Exception as e:
            print(f'[-] {movie_name} already in database!')
    except Exception as e:
        print(f'[x] Weird exception, idk: {str(e)}')
        print(f'[x] actor_list: {actor_list}')
    conn.commit()
    conn.close()
    return
def main():
    try:
        actor = sys.argv[1]
    except:
        print('[x] Please run spider with one actor name in quotes')
        return

    print(f'[-] Started IMDb Spider on {actor}!')
    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=DBHOST)
    cur = conn.cursor()
    print('[-] Connection to database successful!')
    # Grab actor link
    actor_link, movie_list = get_actor_cache(actor)
    if actor_link == '' or len(movie_list) == 0:
        actor_link = getActorLink(actor)
        # Grab a list of all of their movies 
        movie_list = getActorMovies(actor_link)
    print(f'[-] Actor link: {actor_link}')
    print(f'[-] Length of actor filmography: {str(len(movie_list))}')

    depth = 0
    Kevin_Bacon = False
    
    tried_actors = []
    tried_movies = []

    start = time.time()
    #Load root actor into big actor_list
    actor_list = [{'actor_name':actor, 'actor_link':actor_link, 'movies':movie_list}]

    # while the big actor_list isn't empty, we haven't created a connection to Kevin Bacon and we're under the maximum depth...
    while len(actor_list) > 0 and depth < MAX_DEPTH and not Kevin_Bacon:
        # Caching actor_list, actor_link, movie_list
        time.sleep(2)
        depth+=1
        print(f'[-] Depth: {depth}\n\tLength of actor_list: {len(actor_list)}\n\tLength of tried_movies: {len(tried_movies)}\n\tLength of tried_actors: {len(tried_actors)}')
        # Here's what was causing the issue: small pre_actor list is supposed to contain all actors at the current level of depth.
        # If you do pre_actor_list = actor_list, that passes it *by reference*, meaning that appending to the big actor_list also appends to the small pre_actor_list that is
        # supposed to only contain actors from the current level of depth.
        pre_actor_list = actor_list[:]
        for actor in pre_actor_list:
            # As long as the actor isn't in the list of actors we've already searched...
            if actor['actor_name'] not in tried_actors:
                print(f'[-] Starting with new actor: {actor["actor_name"]} in a list of size {len(pre_actor_list)}')
                # Loop over every movie that the actor has been in
                for movie in actor['movies']:
                    # If Kevin Bacon connection still hasn't been found...
                    if not Kevin_Bacon:
                        # and we haven't yet searched that movie for a connection to KB
                        if movie['name'] not in tried_movies:
                            additions = get_movie_cache(movie)
                            if len(additions) == 0:
                                additions = getActorList(movie)
                            time.sleep(1)
                            clean = {}
                            # As long as we have a movie object...
                            if len(additions) > 0:
                                # For every actor that was in the movie...
                                for actor_name, link in additions.items():
                                    # as long as the actor isn't the one that we're currently iterating over, and hasn't already been searched...
                                    if actor_name != actor['actor_name'] and actor_name not in tried_actors:
                                        # add it to the dictionary containing only the relevant actors to check later.
                                        clean[actor_name] = link
                                
                                for name, link in clean.items():
                                    name = name.strip('()\"')
                                    # If one of the actors in the movie is Keven Bacon, set Kevin_Bacon to True and print out what level of depth, what movie and what the final actor link was.
                                    if name == 'Kevin Bacon':
                                        Kevin_Bacon = True
                                        print(f'[-] Found Kevin Bacon @ depth {depth} related to movie {movie["name"]} which is linked to {actor["actor_name"]}')
                                    # If the actor isn't KB
                                    else:
                                        #... and they haven't been searched before
                                        if name not in tried_actors:
                                                # scrape for the link
                                            actor_link, movies = get_actor_cache(name)
                                            if actor_link == '' or len(movies) == 0:
                                                actor_link = getActorLink(name)
                                                # and as long as that link is legit, scrape for a list of their movies and cache the actor object
                                                if len(actor_link) > 0:
                                                    time.sleep(1)
                                                    movies = getActorMovies(actor_link)
                                                    cache_actor({'actor_name':name.strip('()\"'), 'actor_link':actor_link, 'movies':movies})
                                        # Here's another critical line: 
                                        # This is supposed to append the new actor (that we haven't checked yet) to the *big list* of actor (actor_list)
                                        # This actor will be checked *at the next level of depth.*
                                        # However, if we're copying by reference instead of by value, it's also going to append actors meant to the next 
                                        # level of depth to the small list that's being iterated over for the current level of depth. 
                                        actor_list.append({'actor_name':name.strip('()\"'), 'actor_link':actor_link, 'movies':movies})

                        if not Kevin_Bacon:
                            print(f'[-] Kevin Bacon not associated with {movie["name"]}')
                    if not Kevin_Bacon:
                        # If over the full iteration of all actors associated with this movie KB still isn't found, append the movie to the list of movies already tried.
                        tried_movies.append(movie['name'].strip('()\"'))
                        cache_movie(movie)
                if not Kevin_Bacon:
                    # If over the full iteration of the current actor's filmography KB still isn't found, append the actor to the list of actors already tried
                    print(f'[-] Kevin Bacon not found associated with {actor["actor_name"]}, moving on to the next actor in the list!\nList size: {len(pre_actor_list)}')
                    tried_actors.append(actor['actor_name'].strip('()\"'))
                    
                else:
                    # If he has been found, close the connection to the DB, print out the level of depth, and print out how long it took to run.
                    print(f'[-] Kevin Bacon found at depth {depth} connected to actor {actor["actor_name"]}!')
                    conn.close()
                    end = time.time()
                    print(f'[-] It took {end-start} seconds to run!')
                    return
    conn.close()
if __name__ == '__main__':
    main()