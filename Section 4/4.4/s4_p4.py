# imports 
import requests 
import psycopg2 as psql 
from bs4 import BeautifulSoup as bs 
import json, sys, time
from datetime import datetime

# database info
DBUSER = 'testdb'
HOST = '10.0.0.8'
DBPASS = 'password'
MAX_DEPTH = 5

# functions
def getActorLink(actor = ''):
    # Get the link to the actor's page using the search function
    start = datetime.now()
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
    end = datetime.now()
    #print(f'[-] Total time in getActorLink(): {end-start}')
    return actor_link


def getActorMovies(actor_link = ''):
    start = datetime.now()
    # Get the movies that an actor was in using their actor page from 
    # the function above. 
    # Movie object = {movie_name, movie_link}
    actor_link = actor_link
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
    end = datetime.now()
    #print(f'[-] Total time in getActorMovies(): {end-start}')
    return movies


def getActorList(movie_obj = {}):
    # List of actors related to the movie object
    # Actor object {actor_name:actor_link}
    
    actor_list = {}
    start = datetime.now()
    movie_link = movie_obj['link']
    movie_name = movie_obj['name']
    try:
        movie_page = requests.get(movie_link)
    except:
        print(f'[x] Possibly a network error, couldn\'t get the movie page')
        return []
    try:
        movie_bs = bs(movie_page.text, 'html.parser')
        feature_cast = movie_bs.find('section', attrs={'data-testid':'title-cast'})
        cast_divs = feature_cast.find_all('div', attrs={'data-testid':'title-cast-item'})
        for cast_div in cast_divs:
            actor_name = cast_div.find('a', attrs={'data-testid':'title-cast-item__actor'}).text
            actor_link = cast_div.find('a', attrs={'data-testid':'title-cast-item__actor'})['href']
            actor_list[actor_name] = actor_link

    except Exception as e:
        print('[x] Something went wrong on this movie, it might be in production')
        print(f'\t[x] Link: {movie_link}')
        print(f'\t[x] Exception: {str(e)}')
    end = datetime.now()
    #print(f'[-] Time elapsed in getActorList(): {end-start}')
    return actor_list

def cache_movie(movie = {}):
    # Cache a movie in the movie_table
        # Cache an actor in the actor_table
    movie_name = movie['name']
    movie_link = movie['link']
    start = datetime.now()
    try:
        actor_list = movie['actor_list']
    except:
        actor_list = getActorList(movie)


    initial_query = """
    CREATE TABLE IF NOT EXISTS movie_data
    (movie_name TEXT NOT NULL, movie_link TEXT NOT NULL PRIMARY KEY, actor_list TEXT[] NOT NULL);
    """

    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=HOST, port=5432)
    cur = conn.cursor()

    cur.execute(initial_query)
    conn.commit()

    add_query = """
    INSERT INTO movie_data
    (movie_name, movie_link, actor_list)
    VALUES (%s, %s, %s);
    """
    

    cleaned = []
    try:
        for name, link in actor_list.items():
            cName = name.strip('()\"')
            cleaned.append((cName,link))
        try:
            cur.execute(add_query, (movie_name, movie_link, list(cleaned)))
            print(f'[-] Commiting the movie {movie_name}')
            conn.commit()
        except Exception as e:
            print(str(e))
            print(f'[-] {movie_name} already in database!')
    except Exception as bigE:
        print(f'[x] Weird exception: {str(e)}')
        print(f'[x] actor_list: {str(actor_list)}')
    conn.close()
    end = datetime.now()
    #print(f'[-] Time in cache_movie(): {end-start}')
    return


def cache_actor(actor = {}):
    # Cache an actor in the actor_table
    movie_list = actor['movies']
    actor_link = actor['actor_link']
    actor_name = actor['actor_name'].strip('"')
    start = datetime.now()

    initial_query = """
    CREATE TABLE IF NOT EXISTS actor_data
    (actor_name TEXT NOT NULL, actor_link TEXT NOT NULL PRIMARY KEY, movie_list TEXT[] NOT NULL);
    """

    conn = psql.connect(database='testdb', user=DBUSER, password=DBPASS, host=HOST, port=5432)
    cur = conn.cursor()

    cur.execute(initial_query)
    conn.commit()

    add_query = """
    INSERT INTO actor_data
    (actor_name, actor_link, movie_list)
    VALUES (%s, %s, %s);
    """
    

    cleaned = []
    for movie in movie_list:
        cleaned.append((movie['name'],movie['link']))
    try:
        cur.execute(add_query, (actor_name, actor_link, list(cleaned)))
        print(f'[-] Commiting the actor {actor_name}')
        conn.commit()
    except Exception as e:
        print(str(e))
        print(f'[-] {actor_name} already in database!')
    
    conn.close()
    end = datetime.now()
    #print(f'[-] Total time in cache_actor(): {end-start}')
    return


def main():
    start = datetime.now()
    try:
        actor = sys.argv[1]
    except:
        print('[x] Please input an actor name between quotes!')
        return 1

    # Set up the DB connection

    # Grab actor link for the first actor
    actor_link = getActorLink(actor)

    # Grab the list of all of their movies
    movie_list = getActorMovies(actor_link)

    # Initializing variables
    depth = 0
    kevin_bacon = False 
    tried_actors = []
    tried_movies = []

    actor_list = [{'actor_name':actor, 'actor_link':actor_link, 'movies':movie_list}]

    # Main loop
    while len(actor_list) > 0 and depth < MAX_DEPTH and not kevin_bacon:
        depth+=1
        level = datetime.now()
        # Make a copy for the current level of depth
        
        pre_actor_list = actor_list[:]
        print(f'[-] Depth: {depth}\n\tLength of actor_list {len(actor_list)}\n\tMovies tried: {len(tried_movies)}\n\tActors tried: {len(tried_actors)}')
        print(f'[-] Currently {level-start} after the start')
        f = open('./p4_4.log','a')
        f.write(f'[-] Currently {level-start} after the start\n')
        f.write(f'[-] Depth: {depth}\n\tLength of actor_list {len(actor_list)}\n\tMovies tried: {len(tried_movies)}\n\tActors tried: {len(tried_actors)}\n')
        f.close()


        for actor in pre_actor_list:
            if actor['actor_name'] not in tried_actors:
                # Loop over every movie that actor has been in 
                for movie in actor['movies']:
                    if movie['name'] not in tried_movies:
                        # Check if the current actor is Kevin Bacon
                        if not kevin_bacon:
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

                    # We've looped through every actor in this movie. 
                    # If we haven't found Kevin Bacon in the list of actors in the movie,
                    # We add this movie to the tried_movies list
                    if not kevin_bacon:
                        print(f'[-] Kevin Bacon not in {movie["name"]}')
                        print(f'\t[-] Depth: {depth}\n\tActors in current level: {len(pre_actor_list)}')
                        print(f'\t[-] Tried actors: {len(tried_actors)}\n\tTried movies: {len(tried_movies)}')
                        print(f'\t[-] Current actor: {actor["actor_name"]}')
                        tried_movies.append(movie['name'])   
                        f = open('./p4_4.log','a')
                        f.write(f'[-] Kevin Bacon not in {movie["name"]}\n')
                        f.write(f'\t[-] Depth: {depth}\n\tActors in current level: {len(pre_actor_list)}\n')
                        f.write(f'\t[-] Tried actors: {len(tried_actors)}\n\tTried movies: {len(tried_movies)}\n')
                        f.write(f'\t[-] Current actor: {actor["actor_name"]}\n')
                        f.close()
                if not kevin_bacon:
                    tried_movies.append(movie["name"])
                    cache_movie(movie)
                        
            if not kevin_bacon:
                print(f'[-] Kevin Bacon has not been in a movie with {actor["actor_name"]}')
                tried_actors.append(actor["actor_name"])
                cache_actor(actor)
                f = open('./p4_4.log','a')
                f.write(f'[-] Kevin Bacon has not been in a movie with {actor["actor_name"]}\n')
                f.close()

    if depth >= MAX_DEPTH and not kevin_bacon:
        print(f'[-] We reached max depth without finding KB')
    elif len(actor_list) == 0: 
        print(f'[-] For whatever reason, the size of the current level of depth is 0')
    elif kevin_bacon:
        print(f'[-] Found KB at level {depth}, tried {len(tried_actors)} actors and {len(tried_movies)} movies')
    else:
        print(f'[-] IDK something weird happened')
    end = datetime.now()
    print(f'[-] Finished running in {end-start}')
    return
if __name__ == '__main__':
    main()