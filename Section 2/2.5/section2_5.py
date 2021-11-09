# Bubblr 
# API 
#   /user
#   /followers
#   /posts
#   /creation_date


# Nouns
# Users
#   follower_count
#   account_link
#   creation_date
#   follower_list
# Posts
#   poster
#   creation_date
#   number_likes

# This is the function that I will use to initialize a connection to our database
def initDB(database='', user='', password=''):
    # TODO: Implement
    return


def followers(username=''):
    #TODO: Implement
    followerCount = 0
    followerList = []
    return followerCount, followerList

def gatherUser(username=''):
    # Hit the /user endpoint 
    basicInfo = ''
    followCount, followerList = followers(username)
    


def gatherPosts(postLinks=[]):
    # TODO:
    return


# Take in a CSV full of usernames
def ingest_list(filename=''):
    # TODO: Implement
    # Initialize file and pull in usernames
    users = []
    # Load users with values in file
    for user in users:

    return