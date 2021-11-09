# imports 
import sys

# database info
DBUSER = 'testdb'
HOST = '10.0.0.8'
DBPASS = 'password'
MAX_DEPTH = 5

# functions
def getActorLink(actor = ''):
    # Get the link to the actor's page using the search function
    actor_link = ''

    return actor_link

def getActorMovies(actor_link = ''):
    # Get the movies that an actor was in using their actor page from 
    # the function above. 
    # Movie object = {movie_name, movie_link}
    movies = []

    return movies

def getActorList(movie_obj = {}):
    # List of actors related to the movie object
    # Actor object {actor_name:actor_link}
    actor_list = []

    return actor_list

def cache_movie(movie_obj = {}):
    # Cache a movie in the movie_table

    return

def cache_actor(actor_obj = {}):
    # Cache an actor in the actor_table

    return


def main():
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

        # Make a copy for the current level of depth
        pre_actor_list = actor_list[:]
        for actor in pre_actor_list:
            if actor['actor_name'] not in tried_actors:
                # Loop over every movie that actor has been in 
                for movie in actor['movies']:
                    if movie['name'] not in tried_movies:
                        # Check if the current actor is Kevin Bacon
                        if not kevin_bacon:
                            actors = getActorList(movie)
                            # For each actor that is in this movie related 
                            # to this actor at this level of depth
                            for curActor in actors:
                                # Check if curActor is Kevin Bacon
                                if curActor['actor_name'] == 'Kevin Bacon':
                                    kevin_bacon = True
                                    print(f'[-] Kevin Bacon found at depth {depth} in movie {movie["name"]}')
                                # If not, and we haven't checked this actor yet,
                                else:
                                    tried_actors.append(curActor['actor_name'])
                                # add them to tried_actors
                    # We've looped through every actor in this movie. 
                    # If we haven't found Kevin Bacon in the list of actors in the movie,
                    # We add this movie to the tried_movies list
                    if not kevin_bacon:
                        print(f'[-] Kevin Bacon not in {movie["name"]}')
                        tried_movies.append(movie["name"])
                        
            if not kevin_bacon:
                print(f'[-] Kevin Bacon has not been in a movie with {actor["actor_name"]}')
                tried_actors.append(actor["actor_name"])

    if depth >= MAX_DEPTH and not kevin_bacon:
        print(f'[-] We reached max depth without finding KB')
    elif len(actor_list) == 0: 
        print(f'[-] For whatever reason, the size of the current level of depth is 0')
    elif kevin_bacon:
        print(f'[-] Found KB at level {depth}, tried {len(tried_actors)} actors and {len(tried_movies)} movies')
    else:
        print(f'[-] IDK something weird happened')

    return
if __name__ == '__main__':
    main()