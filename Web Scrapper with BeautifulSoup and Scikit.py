
############# Imports ####################
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
##########################################

def menu():
    '''
    from user input get 2 band names    
    returns search, search1, search2, search12, search22, search02, prock1, prock2
    
    '''
    #initialize vars
    prock1= 3
    prock2= 3
    search = '0'
    search1 = '1'
    search2 = '2'
    search12 = '12'
    search22 = '22'
    search02 = '02'
    
    #Request 1st Band input
    print('Enter a Band, max 2 words with no special characters')
    print('Recommended: Radiohead, Sade, Metallica and The cure --CASE SENSITIVE dears')
    Band = input()
    
    # test for correct Band text length
    prock1 = len(Band.split())
    while prock1 > 2:
        print('Enter a correct Band, max 2 words with no special characters :(')
        Band = input()
        prock1 = len(Band.split())
        
    # Store Band in vars
    if prock1 == 2:
        search1 = Band.split()[0]
        search2 = Band.split()[1]
    else :
        search = Band
        
    # storing the second Band name
    print('Thanks, now enter the second Band :)')    
    Band2 = input()
    
    # test for correct Band2 text length
    prock2 = len(Band2.split())
    while prock2 > 2:
        print('Enter a correct Band, max 2 words without special chars :(')
        Band2 = input()
        prock2 = len(Band2.split())
        
    # Store Band in vars
    if prock2 == 2:
        search12 = Band2.split()[0]
        search22 = Band2.split()[1]
    else :
        search02 = Band2
        
    print('Cool, Im Fetching the good stuff now, pls be patient')
    # print(search, search1, search2, search02, search12, search22, prock1, prock2)  ## this is a flow test print
    return search, search1, search2, search02, search12, search22, prock1, prock2

def get_lyrics (search, search1, search2, prock1):
    # Deciding 1 or 2 words band to enter scrapping
    if prock1 == 2:
    # Now fetch urls from website
        lyrics_html = requests.get(f'https://www.lyrics.com/artist/{search1}+{search2}').text
        songsurl = re.findall(rf'(\bhref=\"(/lyric/\d*/{search1}\+{search2}.*?)")', lyrics_html)
        band = search1 + ' ' + search2
    elif prock1 == 1:
        #print('I went to search')
        lyrics_html = requests.get(f'https://www.lyrics.com/artist/{search}').text
        #print(lyrics_html)
        songsurl = re.findall(rf'(\bhref=\"(/lyric/\d*/{search}.*?)")', lyrics_html)
        band = search
        
    # make sure that no null values are worked on
    # if songsurl:
    # get the urls in a list
    d1, d2 = zip(*songsurl)
    
    #prepare the full working URLs to songs
    www = 'http://www.lyrics.com'
    urllist = []
    for i in d2: 
        urllist.append(www+i)
        
    # treat the list of URLs and convert to BeautifulSoap
    songlist = []
    # loop to fetch and store all lyrics of 1 band
    for i in urllist:
        # get the html for the song
        lyrics_html = requests.get(i).text
        # convert to BS object
        lyrics_soup = BeautifulSoup(lyrics_html, 'html.parser')
        # get the lyrics
        songlist.append(lyrics_soup.body.find(class_ = 'lyric-body')) 
        
        
    # Clean any HTML left in the lyrics
    cleansongs = []
    for song in songlist:
        tempsong = re.findall(r'([\s\S]*?)(\<.*?>)', str(song), re.DOTALL)
    
        if tempsong:  
            d1, d2 = zip(*tempsong)
            d1 = ''.join(d1) #this is the key! treats regext created tupples
            d1 = re.sub('\n|\r|\t|\.|\,|\[|\|\;|\(|\)|\'|\"|\!|\]', ' ', str(d1))
            d1 = re.sub('\s+',' ',d1)  
            cleansongs.append((d1,band))
            
    #save the results in a csv        
    cleansongs = pd.DataFrame(cleansongs, columns =['Songs','Band'])
    cleansongs.to_csv(f'lyrics_{band}.csv', index= False)
    print(f'FYI: I got {band} lyrics and saved them, just in case')
    return cleansongs      

def balance_bands(cleansongs_band1,cleansongs_band2):
    #this returns a dataframe with both songlists balanced
    
    #prepare Test and Train datasets
    test1 = cleansongs_band1.iloc[-5:]
    test2 = cleansongs_band2.iloc[-5:]
    b_test = pd.concat([test1,test2])
    
    b1 = cleansongs_band1.iloc[:-5]
    b2 = cleansongs_band2.iloc[:-5]
    
    # first decide what is the minimum songs
    selec = min(cleansongs_band1.shape[0],cleansongs_band2.shape[0])
    
    # then shuffle song selection with the minimum as total
    b1 = cleansongs_band1.sample(selec)
    b2 = cleansongs_band2.sample(selec)
    b3 = pd.concat([b1,b2])   
    
    #b3 is Train, b_test is TEST
    print('Train and Test data are created and balanced')
    return b3 , b_test

def train_beast(b3):
    
    cv = CountVectorizer(stop_words = 'english') #we even have stop words built in the CV!    
    text_corpus = b3['Songs']
    vec = cv.fit_transform(text_corpus)   
    tf = TfidfTransformer()  
    vec2 = tf.fit_transform(vec)  
    # vec2.todense().shape
    X = vec2
    y = b3['Band']   
     
    m = MultinomialNB()
    m.fit(X, y)
    print('model is trained')
    return cv, tf, m

def test_beast(testing_songs,cv,tf,m):
    
    new_songs = testing_songs['Songs']
    vec_test = cv.transform(new_songs)
    vec_test_final = tf.transform(vec_test)
    print('Aaand the predictions are:' ,m.predict(vec_test_final))
    print('Reality check:', testing_songs['Band'])
    print('How the magic was decided, AKA probs:', m.predict_proba(vec_test_final))

    return print('That was all automated folks')

def manual_test(cv,tf,m):
    
    print('Now, Would you like to manualy enter a song for test Y or N')
    t = input()
    if t == 'Y':
        print('type the song plsss')    
        new_songs = input()
        vec_test = cv.transform(new_songs)
        vec_test_final = tf.transform(vec_test)
        print('Aaand the song belongs to:' ,m.predict(vec_test_final))
    else:
        print('Ok, bye')
 

if __name__ == "__main__":
    
    search, search1, search2, search02, search12, search22, prock1, prock2 = menu()
    cleansongs_band1 = get_lyrics(search, search1, search2,prock1)
    cleansongs_band2 = get_lyrics(search02, search12, search22,prock2)
    complete_songs, testing_songs = balance_bands(cleansongs_band1, cleansongs_band2)
    cv, tf, m = train_beast(complete_songs)
    test_beast(testing_songs,cv,tf,m)
    manual_test(cv,tf,m)
    
    
    