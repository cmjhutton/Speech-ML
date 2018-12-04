"""
-Naim Sen-
Jun 18
"""
# A script to scrape youtube for videos given a query. Adapted from work
# done previously for A. Clarke.
# This script requires at least PyTube 2.2.3 which is available via the
# PyTube Github repo. This is so that we can make use of the youtube.length
# attribute for filtering by duration.
from bs4 import BeautifulSoup as bs
import requests
import os
import time
import datetime
import pytube
from pytube import YouTube


# A function to grab the upload date of a youtube video from HTML. The age of the
# video is calculated (in yrs?) and compared to the max upload age. Returns True
# if the upload age is less than or equal to the max upload age, returns false otherwise.

def IsYounger(vid_url, max_upload_age):
    if max_upload_age is None:
        return True
    elif type(max_upload_age) != int or max_upload_age < 1:
        raise ValueError("IsYounger() : Invalid argument - max_upload_age should be a positive integer")
    try:
        watch_page = requests.get(vid_url).text
    except Exception as e:
        print("IsYounger() : request failed ", e)
        exit(1)

    soup = bs(watch_page, 'html.parser')
    date_element = soup.findAll(class_='watch-time-text')
    date_text = date_element[0].text
    # grab year only
    upload_year = int(date_text.split()[-1])
    current_year = datetime.datetime.now().year
    # calculate video age
    upload_age = current_year - upload_year

    # return values
    if upload_age <= max_upload_age:
        return True
    else:
        return False


# Returns true if a video's runtime is shorter than the specified max_length (in seconds)
def IsCorrectLength(yt_object, min_length=0, max_length=0):
    # check args
    if min_length > max_length:
        raise ValueError("min_length should be less than max_length dummy!")

    # grab length from the yt object.
    if int(yt_object.length) > max_length:
        return False
    elif max_length is None:
        return True
    else:
        return True


# A function to scrape audio from youtube videos given a set of queries passed as
# a string of terms separated by '+' or ' '. Scrapes page by page, (20 videos per
# page). Creates new directory in CWD to store audio files. Can filter by video
# upload age in years and video length.
# The force_in_title flag can be set to force searching using YouTube's intitle search flag.
def ScrapeVideo(query, num_videos, save_path=None, max_upload_age=None,
                max_length=None, force_in_title=True, check_directory=True):
    # define a few parameters that aren't often tweaked
    min_duration = 30
    max_duration = 12000

    # Check arguments
    if type(num_videos) is not int or num_videos <= 0:
        raise ValueError("ScrapeVideo() : Invalid argument - num_videos should be a positive integer")

    if type(query) is not str:
        raise ValueError("ScrapeVideo() : Invalid argument - query should be a string with terms separated by \'+\'")
    if ' ' in query:
        query = query.replace(' ', '+')

    # save_path is optional and can be auto generated if left blank
    if save_path is None:
            save_path = os.getcwd()+'/SCRAPES_'+query.replace('+', '_')
    # max_upload_age is optional, None=no filter on upload date.
    if max_upload_age is None:
        pass
    elif type(max_upload_age) is not int or max_upload_age < 1:
        raise ValueError("ScrapeVideo() : Invalid argument - max_upload_age should be a positive integer")

    # declare counters
    download_count = 0
    parsed_count = 0
    page_counter = 0

    # switch base depending on force_in_title flag. Makes the first query search with
    # intitle: set
    if force_in_title:
        base = "https://www.youtube.com/results?search_query=intitle%3A"+query
    elif not force_in_title:
        base = "https://www.youtube.com/results?search_query="+query

    print("URL : ", base)
    # For saving to file we need to make a directory if it doesn't exist already
    # and check the file is empty etc.
    # if the path exists check it's empty
    if os.path.isdir(save_path):
        if os.listdir(save_path) == []:
            pass
        elif check_directory:
            # if directory is not empty ask for confimration
            valid_response = False
            while not valid_response:
                response = input("The directory : {0} is not empty. Are you sure you wish to proceed? Y/N\n".format(save_path))
                if response.lower() == 'y':
                    valid_response = True
                elif response.lower() == 'n':
                    valid_response = True
                    print("The program will now quit.")
                    exit(1)
                else:
                    print("Invalid response, please try again.")
                    valid_response = False

    else:
        os.makedirs(save_path)

    # get scrape start time
    scrape_start_t = time.time()

    # Loop is broken when download_count = num_videos
    while True:
        # grab page and parse html
        r = requests.get(base)
        page = r.text
        soup = bs(page, 'html.parser')
        # grab video links from thumbnail links
        vids = soup.findAll('a', attrs={'class': 'yt-uix-tile-link'})
        # create a list of relevant URLS
        videolist = []
        for v in vids:
            # parse href attribute for 'http' regex to skip google adverts
            if (v['href'][0:4] == 'http'):
                continue
            tmp = 'https://www.youtube.com' + v['href']
            videolist.append(tmp)
        print("There are ", len(videolist), " videos returned for page "+str(page_counter+1))
        # loop over video (YT) objects in each page
        for video_url in videolist:
            parsed_count += 1
            try:
                # initialise youtube object
                yt = YouTube(video_url)
                # check video upload age
                if IsYounger(video_url, max_upload_age) and IsCorrectLength(yt, min_duration, max_duration):
                    # filter AV stream
                    stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution='360p').first()
                    # download audio from stream
                    # check whether title already exists
                    if os.path.isfile(save_path+'/'+stream.default_filename):
                        stream.download(save_path, filename=yt.title+' ('+str(download_count+1)+')')
                    else:
                        stream.download(save_path)
                    # Increment counter
                    download_count += 1
                    print('Downloaded video '+str(download_count))

                    # Check if download_count = num_videos
                    if download_count == num_videos:
                        scrape_end_t = time.time()
                        print("{0} of {1} videos downloaded.\n".format(download_count, parsed_count))
                        print("total time: {0} seconds".format(scrape_end_t - scrape_start_t))
                        return
            except Exception as e:
                print("Error: ", e, "\n", "download_count: ", download_count)
                continue

        # Next page
        # find the navigation buttons in the page html:
        buttons = soup.findAll('a', attrs={'class': "yt-uix-button vve-check yt-uix-sessionlink yt-uix-button-default yt-uix-button-size-default"})
        # the button for the next page is the last one in the list:
        nextbutton = buttons[-1]
        # get the url of the next page:
        base = 'https://www.youtube.com' + nextbutton['href']
        page_counter += 1


if __name__ == '__main__':

    print("pytube version : ", pytube.__version__)
    
    
    ScrapeVideo('what americans agree on when it comes to health', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5)
    ScrapeVideo('how cryptocurrency can help startups get investment', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 ways to be a better ally in the workplace', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why its too hard to start a business in africa', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why being respectful to your coworkers is good for business', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what doctors should know about gender identity', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can make energy more affordable for low income families', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to build a thriving music scene in your city', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what happened when we tested thousands of abandoned rape kits in detroit', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how police and the public can create safer neighbourhoods together', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how whistle blowers shape history', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we could teach our bodies to heal faster', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the press trampled on my privacy. heres how i took back my story', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why we choke under pressure and how to avoid it', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('your fingerprints reveal more than you think', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to create a world where no one dies waiting for a transplant', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how im using lego to teach arabic', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('did the global response to 9/11 make us safer', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 ways businesses can fight sex trafficking', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('looks arent everything believe me im a model', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a new way to think about the transition to motherhood', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how i went from child refugee to international model', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how china is and isnt fighting pollution and climate change', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a rare galaxy thats challenging our understanding of the universe', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('understanding ptsds effects on brain body and emotions', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to get serious about diversity and inclusion in the workplace', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('to transform child welfare take race out of the equation', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how women in rural india turned courage into capital', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how cancer cells communicate and how we can slow them down', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why i fight for the education of refugee girls like me', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the little risks you can take to increase your luck tina seelig', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how teachers can help kids find their political voices', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why art thrives at burning man nora atkinson', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can use light to see deep inside our bodies and brains', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('you may be accidentally investing in cigarette companies', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to stop swiping and find your person on dating apps', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why doctors are offering free tax prep in their waiting rooms', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to train employees to have difficult conversations', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the power of diversity within yourself rebecca hwang', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('an honest look at the personal finance crisis elizabeth white', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a new way to monitor vital signs that can see through walls', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a new way to remove co2 from the atmosphere jennifer wilcox', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why teens confess to crimes they didnt commit lindsay malloy', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the tiny creature that secretly powers the planet penny chisholm', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what if we eliminated one of the worlds oldest diseases caroline harper', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why you should love gross science anna rothschild', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('technology that knows what youre feeling poppy crum', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how im bringing queer pride to my rural village katlego', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the incredible potential of flexible soft robots', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('inside the fight against russias fake news empire olga yurkova', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how technology can fight extremism and online harassment', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the critical role librarians play in the opioid crisis', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how vultures can help solve crimes', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a teen scientists invention to help wounds heal ted', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('this simple test can help kids hear better susan emmett', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to turn a group of strangers into a team', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how i made friends with reality', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('where joy hides and how to find it', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how pakistani women are taking the internet back', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('scientists must be free to learn to speak and to challenge', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the doctors nurses and aid workers rebuilding syria rola hallam', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a healthy economy should be designed to thrive not grow kate raworth', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the truth about unwanted arousal emily nagoski', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a playful solution to the housing crisis sarah murray', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how baltimore called a ceasefire erricka bridgeford', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to build and rebuild trust frances frei', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why you dont like the sound of your own voice rebecca kleinberger', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('to design better tech understand context tania douglas', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('learning a language speak it like youre playing a video game', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how work kept me going during my cancer treatment sarah donnelly', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a womans fury holds lifetimes of wisdom tracee ellis ross', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('war and what comes after clemantine wamariya', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a parkland teachers homework for us all diane wolk rogers', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the dead zone of the gulf of mexico nancy rabalais', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('why you should make useless things simone giertz', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a printable flexible organic solar cell hannah burckstummer', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what if we ended the injustice of bail robin steinberg', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how the arts help homeless youth heal and build malika whitley', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how language shapes the way we think lera boroditsky', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the standing rock resistance and our fight for indigenous rights tara houska', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('math can help uncover cancers secrets irina kareva', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the role of faith and belief in modern africa ndidi nwuneli', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('academic research is publicly funded why isnt it publicly available erica stone', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how fungi recognize and infect plants mennat el ghalid', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the human stories behind mass incarceration eve abrams', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what if gentrification was about healing communities instead of displacing them liz ogbu', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how i use art to bridge misunderstanding adong judith', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what we can do about the culture of hate sally kohn', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the great migration and the power of a single decision isabel wilkerson', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what a world without prisons could look like deanna van buren', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the best way to help is often just to listen sophie andrews', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('to solve the worlds biggest problems invest in women and girls musimbi kanyoro', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how shocking events can spark positive change', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what i learned when i conquered the worlds toughest triathlon minda', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('to learn is to be free shameem akhtar', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the brain changing benefits of exercise wendy suzuki', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the role of human emotions in science and research ilona stengel', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('a life saving intervention that prevents human stampedes nilay kulkarni', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can build ai to help humans not hurt us margaret mitchell', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the secret to great opportunities the person you havent met yet', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 lessons of revolutionary love in a time of rage valarie kaur', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can help hungry kids one text at a time', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('this deep sea mystery is changing our understanding of life', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('6 space technologies we can use to improve life on earth danielle wood', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('black life at the intersection of life and death mwende', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('my failed mission to find god and what i found instead anjali kumar', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the gift and power of emotional courage susan david', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the business benefits of doing good wendy woods', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('want to change the world start be being brave enough to care', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('talk about your death while youre still healthy michelle knox', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('want to be more creative go for a walk marily oppezzo', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how adaptive clothing empowers people with disabilities', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('the power of citizen video to create undeniable truths yvette', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('how china is changing the future of shopping angela wang', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('inside africas thriving art scene touria el glaoui', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('what we dont teach kids about sex sue jaye', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 thoughtful ways to conserve water lana mazahreh', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('you arent at the mercy of your emotions your brain creates them', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)
    ScrapeVideo('good and bad are incomplete stories we tell ourselves heather lanier', 1, save_path='/raid/scratch/chutton/scraping/voice/women', max_upload_age=5, check_directory=False)


    ScrapeVideo('what baby boomers can learn from millenials at work and vice versa', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5)
    ScrapeVideo('how i climbed a 3000 foot vertical cliff without ropes', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the secrets of spider venom', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the simple genius of a good graphic', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why the hospital of the future will be your own home', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 ways to make better decisions by thinking like a computer', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what are the most important moral problems of our time', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('a new way to fund healthcare for the most vulnerable', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how ai could compose a personalised soundtrack to your life', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how data is helping us unravel the mysteries of the brain', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what commercialization is doing to cannabis', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how art can shape americas conversation about freedom', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why the wrong side of the tracks is usually the east side of cities', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how urban spaces can preserve history and build community', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what if you could trade a paperclip for a house', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what a scrapyard in ghana can teach us about innovation', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how ai can save our humanity', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('you are fluent in this language and dont even know it', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how ai is making it easier to diagnose disease', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('where are all the aliens stephen webb', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what the russian revolution would have looked like on social media', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the mission to create a searchable database of earths surface', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to build synthetic dna and send it across the internet', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we study the microbes living in your gut', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how farming could employ africas young workforce and help build peace', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the rapid growth of the chinese internet and where its headed', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('a crash course in organic chemistry', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('fake videos of real people and how to spot them', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how were saving one of earths last wild places', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how autonomous flying taxis could change the way you travel', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the agony of opioid withdrawl and what doctors should tell patients about it', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the symbols of systemic racism and how to take away their power', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('bridges should be beautiful ian firth ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can design timeless cities for our collective future', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the genius behind some of the worlds most famous buildings', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the nightmare videos of childrens youtube and whats wrong with the internet today', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can bring mental health support to refugees ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the surprising science of alpha males', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('four billion years of evolution in six minutes ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to get empowered but not overpowered by ai', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what well learn about the brain in the next century', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the journey through loss and grief jason b rosenthal', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why the secret to success is setting the right goals ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('lets turn the high seas into the worlds largest nature reserve', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what if we replaced politicians with randomly selected people', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why theater is essential to democracy ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can turn the cold of outer space into a renewable resource', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what gardening taught me about life tobacco brown', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how well become cyborgs and extend human potential', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('comics belong in the classroom ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to start a conversation about suicide jeremy forbes', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the shocking danger of mountaintop removal and why it must end', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what its like to be the child of immigrants michael rain', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why fascism is so tempting and how your data could power it', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the age old sharing economies of africa and why we should scale them', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what its like to be a transgender dad ted', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how a male contraceptive pill could work john amory', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why tech needs the humanities eric berridge', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('is the world getting better or worse a look at the numbers', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how i turn negative online comments into positive offline conversations', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)      
    ScrapeVideo('what ive learnt about parenting as a stay at home dad glen henry', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why its worth listening to people you disagree with zachary r wood', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the harm reduction model of drug addiction treatment mark tyndall', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what does the universe sound like a musical tour matt russo', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('should we create a solar shade to cool the earth danny hillis', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('to eliminate waste we need to rediscover thrift andrew dent', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('my $500 house in detroit and the neighbours who helped me rebuild it drew philip', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why i choose humanism over faith leo igwe', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('my descent into americas neo nazi movement and how i got out', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how quantum physics can make encryption stronger vikram sharma', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what if we paid doctors to keep people healthy matthias mullenbeck', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('need a new idea start at the edge of what is known vittorio loreto', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('for survivors of ebola the crisis isnt over soka moses', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('a rite of passage for late life bob stein', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('can i have your brain the quest for truth on concussions and cte chris nowinski', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why must artists be poor hadi eldebek', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 myths about the future of work and why theyre not true daniel susskind', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to inspire every child to be a lifelong reader alvin irby', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how fashion helps us express who we are and what we stand for kaustav dey', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('do you really know why you do what you do petter johansson', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('what soccer can teach us about freedom marc bamuthi joseph', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to connect with depressed friends bill bernat', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we look kilometers below the antartctic ice sheet dustin schroeder', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('be humble and other lessons from the philosophy of water raymond tang', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('refugees want empowerment not handouts robert hakiza', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to resolve racially stressful situations howard c stevenson', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('looking for a job highlight your ability not your experience jason shen', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('3 creative ways to fix fashions waste problem amit kalra', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why i train grandmothers to treat depression dixon chibanda', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('capitalism isnt an ideology its an operating system bhu', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the surprising ingredient that makes businesses work marco alvera', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how protest is redefining democracy around the world zachariah mampilly', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('this company pays kids to do their maths homework mohamad jebara', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how architecture can create dignity for all john cary', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('a funny look at the unintended consequences of technology', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('from death row to law graduate peter ouko', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how i use minecraft to help kids with autism', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('could fish social networks help us save coral reefs', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why i study the most dangerous animal on earth mosquitoes fredros okumu', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the thrilling potential for off grid solar energy', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the surprising solution to ocean plastic david katz', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the dangerous evolution of hiv edsel salvana', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the hidden role informal care givers play in health care', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('american bipartisan politics can be saved heres how bob inglis', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the search for aha moments matt goldman', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how to put the power of law into peoples hands vivek', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how we can stop africas scientific brain drain', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how record collectors find lost music and preserve our cultural heritage alexis charpentier', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('medical tech designed to meet africas needs', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('a vehicle built in africa for africa joel jackson', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('our treatment of hiv has advanced why hasnt the stigma changed', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('photos of africa taken from a flying lawn chair', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how adoption worked for me christopher ategeka', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('a new weapon in the fight against superbugs david brenner', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('success stories from kenyas first makerspace', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('adventures of an interplanetary architect xavier', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('the brain benefits of deep sleep and how to get more of it dan gartenberg', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('why im done trying to be man enough justin baldoni', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
    ScrapeVideo('how fake handbags fund terrorism and organized crime alastair gray', 1, save_path='/raid/scratch/chutton/scraping/voice/men', max_upload_age=5, check_directory=False)
