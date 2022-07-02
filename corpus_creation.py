import argparse
import datetime, time
import os
import sys
import wikipedia
import re
import pywikibot
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from corpus_creation_utils import get_protection_status, get_citations, get_modified_urls
tqdm.pandas()
import logging

v = 3.0
logger = logging.getLogger(f'Wikiscore-logger_{v}')


def err_handler(type, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))
sys.excepthook = err_handler


def get_all_the_bloody_titles(key_words: str) -> (list, int):
    '''

    '''
    titles = []
    a = key_words.lower().replace(' ', '+')
    # todo: make search limit effective
    scraped_url = 'https://en.wikipedia.org/w/index.php?title=Special:Search&limit=5000&offset=0&profile=default&search={}&ns0=1'.format(
        a)
    html_text = requests.get(scraped_url).text
    soup = BeautifulSoup(html_text, features='lxml')
    r = soup.find('div', {'class': 'results-info'})
    nbr_result = int(r.get('data-mw-num-results-total'))
    for interest in soup.find_all('div', {'class': 'mw-search-result-heading'}):
        titles.append(interest.find('a')['title'])
    return titles, nbr_result


def get_section_titles(page : str) -> list:
    '''
    Returns the section titles

    :param page: Title of the page
    :return: The list of section titles
    '''
    section_tit = set()
    section_title = []
    scraped_url = wikipedia.page(page, auto_suggest = False).url
    html_text = requests.get(scraped_url).text
    soup = BeautifulSoup(html_text, features='lxml')
    r = soup.find_all('h2') + soup.find_all('h3') + soup.find_all('h4')
    for i in r:
        if i.find('span', {'class' : 'mw-headline'}) is not None:
            section_tit.add(i.find('span', {'class' : 'mw-headline'})['id'])
    for i in section_tit:
        section_title.append(i.replace('_', ' '))
    return section_title


# We define a function to automatically set up a corpus of related articles
def corpus_selection(word_keys: str, number_of_results: int, key_for_section: str) -> list:
    '''
    Select the corpus if the keywords are in the section or in the title

    :param word_keys : string

    :return: a dictionnary containing the title of all the pages of the corpus
    '''
    st = time.time()
    logger.info(f'starting getting search pages for term {word_keys} max pages {number_of_results}, secondary term {key_for_section}')
    corpus = []
    proper_list = []
    left_list = []
    search_list, nbr_result= get_all_the_bloody_titles(word_keys)
    logger.info(f'total search results {len(search_list)}')
    # Select and put in a list number_of_results wikipedia articles related to word_keys

    for article in tqdm(search_list):
        try:
            wikipedia.summary(article, auto_suggest=False)
            proper_list.append(article)
        except wikipedia.exceptions.DisambiguationError as e:
            pass
        except wikipedia.exceptions.PageError as e:
            try:
                wikipedia.summary(article, auto_suggest=False)
                proper_list.append(article)
            except wikipedia.exceptions.PageError as e:
                pass
    logger.info(f'proper search results {len(proper_list)}')
    for proper_article in tqdm(proper_list):
        if key_for_section in proper_article.lower():  # Among these articles, select the ones whose title contains key_for_selection for the corpus
            corpus.append(proper_article)
        else:
            left_list.append(proper_article)  # Put the rest of the articles in a list
    logger.info(f'title has search key in  {len(corpus)} results')
    for left_article in tqdm(left_list):
        sec_tit = []
        try:
            sec_tit = get_section_titles(left_article)
            for section in sec_tit:
                if key_for_section.lower() in section.lower() and left_article not in corpus:
                    corpus.append(left_article)
        except wikipedia.exceptions.DisambiguationError as e:
            pass
        except wikipedia.exceptions.PageError as e:
            try:
                sec_tit = get_section_titles(left_article)
                for section in sec_tit:
                    if key_for_section.lower() in section.lower() and left_article not in corpus:
                        corpus.append(left_article)
            except wikipedia.exceptions.PageError as e:
                pass
    logger.info(f'found a total of {len(corpus)} results, in {time.time()-st} seconds')
    logger.info(f'search terms found: {corpus[:number_of_results]} s')

    return corpus[:number_of_results]


def crea_dataframe(search_list: list, keyword: str) -> pd.DataFrame:
    #todo: why is keyword not used??

    '''
    param search_list: liste containing the name of all the articles
    param keyword: string containing the keyword that we want to scrap


    return: data frame containg the name, the url and the wikicode of the entire page if the keyword is in the title.
    If it's not it returns the wiki code of the section containing the keyword only. Or return the wikicode for each entire page if the line with recode are commented
    '''
    tableau = []  # creation of a list that will contain a dictionnary for each page with the information

    # this part is if you only want to scrap the citations for the functions
    # It detects if the keyword is included in a section, a subsection or a subsubsection
    # if the aim is to plot only the section then just remove the ''' '''
    '''
    recode= r'(?:==(?:\w|\ )*?(?:'+keyword[0].lower()+'|'+keyword[0].upper()+')'+keyword[1:]+'(?:\w|\ )*?==\n)((?:.|\n)*?)(?:==(?:\w|\ )*==\n)'
    recode2=r'(?:===(?:\w|\ )*?(?:'+keyword[0].lower()+'|'+keyword[0].upper()+')'+keyword[1:]+'(?:\w|\ )*?===\n)((?:.|\n)*?)(?:(?:===|==)(?:\w|\ )*(?:===|==)\n)'
    recode3=r'(?:====(?:\w|\ )*?(?:'+keyword[0].lower()+'|'+keyword[0].upper()+')'+keyword[1:]+'(?:\w|\ )*?====\n)((?:.|\n)*?)(?:(?:===|==|====)(?:\w|\ )*(?:===|==|====)\n)'
    '''
    # browse all the titles  of the search list
    for i in tqdm(range(len(search_list))):
        # find the wikipedia page
        page = wikipedia.page(search_list[i], auto_suggest=False)
        page_title = page.title  # give the clean name of the page
        page_url = page.url  # give the url of the page
        site = pywikibot.Site("en", "wikipedia")
        page = pywikibot.Page(site, page_title)

        # if you want to scrap for only the section containing the keywordremove the next line and '''  '''
        page_text = page.text

        '''
        if keyword.lower() in page_title.lower(): 
            page_text=page.text
        else:
            page_text = str(re.findall(recode , page.text))
        if page_text=="[]":
            page_text = str(re.findall(recode2, page.text))
        if page_text== "[]":
            page_text = str(re.findall(recode3, page.text))
        '''

        infopage = {'Name only': page_title, 'page url': page_url, 'text': page_text}
        tableau.append(infopage)
    df = pd.DataFrame.from_dict(tableau)
    return df

def parse_df_citations(df):
    logger.info('collecting and parsing citations')
    df['citations'] = df['text'].progress_apply(lambda x: get_citations(x))

    df['Ref count'] = df['citations'].progress_apply(lambda x: x['Ref count'])

    df['nb_journal_citations'] = df['citations'].progress_apply(lambda x: x['nb_journal_citations'])  # number of scientific citations
    df["journalcitation"] = df['citations'].progress_apply(lambda x: x['citationjournal'])
    df["journal"] = df['citations'].progress_apply(lambda x: x['journal'])
    df["nbjournaldetected"] = df['citations'].progress_apply(lambda x: x['journal_count'])

    df["citation org"] = df['citations'].progress_apply(lambda x: x['citations.org'])  # number of .org citation
    df["citationorgtext"] = df['citations'].progress_apply(lambda x: x["citationorgtext"])

    df["citation gov"] = df['citations'].progress_apply(lambda x: x["citations.gov"])  # number of .gov citations
    df["citationgovtext"] = df['citations'].progress_apply(lambda x: x["citationgovtext"])
    df["citation IPCC"] = df['citations'].progress_apply(lambda x: x["citationsIPCC.ch"])  # number of IPCC citations

    df["citation com"] = df['citations'].progress_apply(lambda x: x["citations.com"]) # number of .com citations
    df["citationcomtext"] = df['citations'].progress_apply(lambda x: x["citationcomtext"])

    df["citationipbes"] = df['citations'].progress_apply(lambda x: x["citationsipbes"]) # number of .ipbes citations
    df["citationguardian"] = df['citations'].progress_apply(lambda x: x["citationguardian"]) # others:
    df["citationautre"] = df['citations'].progress_apply(lambda x: x["citationautre"])
    df["citationtext_total"] = df["citationgovtext"] + df["citationcomtext"] + df["citationorgtext"] + df["journal"]
    df["org count"] = df["citation org"] / df["Ref count"]
    df["gov count"] = df["citation gov"] / df["Ref count"]
    df["com count"] = df["citation com"] / df["Ref count"]
    df["Sci count"] = df['nb_journal_citations'] / df['Ref count']
    df['IPCC count'] = df['citation IPCC'] / df['Ref count']
    df['percentage of official sources'] = (df['nb_journal_citations'] + df['citation gov'] + df['citation org'] + df[
        'citation IPCC'] + df['citationipbes']) / df['Ref count']
    return df

def add_pageinfo(df,urls):
    # Cell to scrap infos from "page info" section (2 to scrap the third table of the page)
    doblist = []
    creatorlist = []
    totaledits = []
    recentedits = []
    pageid = []
    pagelenght = []
    editprotection = []
    recentpageviews = []

    for i in tqdm(urls):
        source = requests.get(i)
        soup = BeautifulSoup(source.text, features='lxml')
        alltables = soup.findAll('table', {"class": "wikitable mw-page-info"})
        tableau_html_liste = pd.read_html(str(alltables))  # We get it as a list
        df_pageinfo2 = pd.DataFrame(tableau_html_liste[2])  # And make it a df
        # The number between brackets corresponds to the number of the table according to its order on the html page
        creatorlist += [df_pageinfo2.iat[0, 1]]
        doblist += [df_pageinfo2.iat[1, 1]]
        totaledits += [df_pageinfo2.iat[4, 1]]
        recentedits += [df_pageinfo2.iat[5, 1]]

        # Scrap of the first table of the page (0)
        df_pageinfo0 = pd.DataFrame(tableau_html_liste[0])
        pagelenght += [df_pageinfo0.iat[2, 1]]
        pageid += [df_pageinfo0.iat[3, 1]]

        # Scrap of the second table of the page (1)
        df_pageinfo1 = pd.DataFrame(tableau_html_liste[1])
        editprotection += [df_pageinfo1.iat[1, 1]]

    #Cell to add the new lists as new columns of the df
    df["Page id"]=pageid
    df["Edit protection"]=editprotection
    df["Page lenght (Bytes)"]=pagelenght
    df["DOB"]=doblist
    df["Creator"]=creatorlist
    df["Total edits"]=totaledits
    df["Recent edits"]=recentedits
    return df


def clean_df(df):
    # Cleaning the table

    # Getting rid of the time
    df["DOB"] = df["DOB"].str.slice(7, 100, 1)
    # peutêtre qu'on pourrait mettre comme end point la len de la string

    # Format the date
    df["Formated DOB"] = pd.to_datetime(df["DOB"], format='%d %B %Y')
    df["Year_month"] = pd.to_datetime(df['DOB']).dt.to_period('M')

    # Getting the year
    df['Year'] = pd.DatetimeIndex(df['DOB']).year

    # Cleaning the creator
    df["Creator"] = df["Creator"].str.replace(r"\(.*\)", '', regex=True)
    del df['text']
    return df


def set_logger(term, v):
    wikipedia.set_lang("en")  # We make our research in english
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    fileName = 'wikiscore_' + term+'_'+str(datetime.datetime.now())[:10]

    fileHandler = logging.FileHandler(os.path.join(os.getcwd(), 'outputs', fileName+ '.log'))
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logger.setLevel(10)
    logger.info(f"""\
    
    ██╗    ██╗██╗██╗  ██╗██╗      ███████╗ ██████╗ ██████╗ ██████╗ ███████╗
    ██║    ██║██║██║ ██╔╝██║      ██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║ █╗ ██║██║█████╔╝ ██║█████╗███████╗██║     ██║   ██║██████╔╝█████╗  
    ██║███╗██║██║██╔═██╗ ██║╚════╝╚════██║██║     ██║   ██║██╔══██╗██╔══╝  
    ╚███╔███╔╝██║██║  ██╗██║      ███████║╚██████╗╚██████╔╝██║  ██║███████╗
     ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚═╝      ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝                                      
                                          version {v}""")
    return logger


if __name__ == '__main__':
    "usage (from command line):"
    " python3 corpus_creation.py -term 'covid-19'   "

    ap = argparse.ArgumentParser()
    ap.add_argument("-term", "--term", default='', help="search term")
    ap.add_argument("-secondary_term", "--secondary_term", default='', help="search term 2")
    ap.add_argument("-search_limit", "--search_limit", default=5000, help="search limit N pages")

    args = vars(ap.parse_args())
    set_logger(args['term'], v)
    search_list = corpus_selection(args['term'], args['search_limit'], args['secondary_term'] or args['term'])

    protection_status_evolution = get_protection_status(search_list, logger)
    df = crea_dataframe(search_list, args['term'])
    df = parse_df_citations(df)
    logger.info(f'mean scietificness score {df["nbjournaldetected"].sum()/df["nb_journal_citations"].sum()}')

    urls = get_modified_urls(df["Name only"]) #make a list will all titles
    df = add_pageinfo(df, urls)
    df = clean_df(df)
    fileName = 'wikiscore_' + args['term'] + '_' + str(datetime.datetime.now())[:10]
    df.to_csv(os.path.join(os.getcwd(), 'outputs', fileName + '.csv'))
