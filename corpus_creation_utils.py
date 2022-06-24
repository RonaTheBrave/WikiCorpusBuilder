import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
tqdm.pandas()
import seaborn as sns
import matplotlib.pyplot as plt

# todo: rethink logging in these functions


def get_protection_status(data, logger=None):
    if not logger:
        import logging
        logger = logging.getLogger('Wikiscore-simple-logger')

    logger.info('getting protection status')

    years_off = []
    for i in range(22):
        years_off.append(2001 + i)

    wrong_ones = []
    dot = pd.DataFrame(years_off)

    for article in data:

        html_text = requests.get(
            ('https://en.wikipedia.org/wiki/Special:Log?type=protect&user=&page={}&wpdate=&tagfilter=&subtype=').format(
                article)).text
        soup = BeautifulSoup(html_text, 'lxml')
        dic = {}
        results = soup.find_all('li', {'class': 'mw-logline-protect'})

        for i in results:
            z = i.find('a')
            protection = i.get('data-mw-logaction')
            date = str(z)[str(z).find('Log">') + 5:str(z).find('</a>')]
            dic[pd.to_datetime(date, format='%H:%M, %d %B %Y')] = protection

        if 'expires' in str(results):
            res = str(results).split('span')
            for string in res:
                if '] (expires' in string:
                    date_get = string[string.find('] (expires ') + 11:string.find(' (UTC))')]
                    if ') [' in date_get:
                        date_get = date_get[:date_get.find(') [')]
                    if '] (' in date_get:
                        date_get = date_get[date_get.find(', '):]
                    if ')' in date_get:
                        date_get = date_get.replace(')', '')
                    if date_get[:2] == ', ':
                        date_get = date_get[2:]
                    if date_get[-1] == ' ':
                        date_get = date_get[:-1]
                    if ',' in date_get:
                        date_get = date_get.replace(',', '')
                    try:
                        dic[pd.to_datetime(date_get, format='%H:%M %d %B %Y')] = 'protect/unprotect'
                    except:
                        try:
                            dic[pd.to_datetime(date_get, format='%H:%M %B %d %Y')] = 'protect/unprotect'
                        except:
                            wrong_ones.append(article)

        if len(dic) != 0:
            dic = dict(sorted(dic.items()))
            new_dic = {}
            s = set()
            list_date = list(dic.keys())[::-1]
            for date in list_date:
                s.add(date.year)
            for j in sorted(s):
                deadline = pd.to_datetime('30 June {} 00:00:00'.format(j))
                same_year = []
                for date in list_date:
                    if date.year == deadline.year and date <= deadline:
                        same_year.append(date)
                        if len(same_year) != 0:
                            new_dic[deadline.year] = dic[max(same_year)]
                    else:
                        if date.year == deadline.year and date > pd.to_datetime('30 June {}'.format(max(s))):
                            new_dic[max(s) + 1] = dic[max(list_date)]

            keys = list(new_dic.keys())
            for year in years_off:
                if year < min(keys):
                    new_dic[year] = 'protect/unprotect'
                elif year > max(keys):
                    new_dic[year] = new_dic[max(keys)]
                else:
                    for low in keys:
                        for high in keys:
                            if year > low and year < high and len(keys[keys.index(low):keys.index(high)]) == 1:
                                new_dic[year] = new_dic[low]

            d = dict(sorted(new_dic.items()))

            if len(d) == 22:
                dot[article] = d.values()
            else:
                dot[article] = list(d.values())[:22]
    logger.info('Done protection info here:')
    logger.info(dot)

    return dot


# Some additional functions
def get_ids_from_ref(ref: str) -> dict:
    '''
    detects if the reference entering this program contains a doi or a pmid or a pmc and if it's the case the return it
    Also returns the name of the journal in which the article has been published

    param ref : the string of a reference

    return ids:  a dictionnary containing the doi or pmid or pmc and the journal of the reference if it's a scientific reference
    '''

    d = dict(re.findall(r'(doi|pmc|pmid)(?:(?:\s?[=\|]\s?)|(?:\.)|(?:(?:])*?:)|(?:\s|\/)|(?: *=))([^|\s}]*)', ref))
    if d != {}:
        recode = re.findall(r'(journal of (?:\w| )*)', ref) + re.findall(r"''\[{2}(.*)\]{2}''", ref) + re.findall(
            r'(?:journal) *?=((?:\w| |\[|-|\.)*)', ref)
        if recode != []:
            d["journal"] = recode
            # print(d["journal"],ref)
        recodeaccess = re.findall(r'doi-access *?=((?:\w| )*)', ref)
        if recodeaccess != []:
            d["access"] = recode

    ids = {k: v for k, v in d.items() if v}
    return ids


def get_cit_from_ref(ref: str) -> dict:
    '''
    detects if the reference entering this program contains a.org, .gov or .com citation except if it's a guardian citation

    param ref : the string of a citation

    return ids:  a dictionnary containing as keys org, gov and com and in values the name of the site of the citation
    '''
    d = dict(re.findall(r"((?:[(?:\.)(?:\-)\w]*)\.(org|com|gov))", ref, flags=re.IGNORECASE))

    # remove the archive because we don't want to count them in the number of .org citation
    if 'archive.org' in d:
        d.pop('archive.org', None)
    if "web.archive.org" in d:
        d.pop('web.archive.org', None)
    if "www.webcitation.org" in d:
        d.pop('www.webcitation.org', None)
    if "ghostarchive.org" in d:
        d.pop("ghostarchive.org", None)
    if "www.ncbi.nlm.nih.gov" in d or "ncbi.nlm.nih.gov" in d:
        d.pop("www.ncbi.nlm.nih.gov", None)
        d.pop("ncbi.nlm.nih.gov", None)
        d["ncbi"] = "ncbi.nlm.nih.gov"

    ids = {v: k for k, v in d.items() if v}

    return ids


def get_IPCC_guardian_ipbes_from_ref(ref: str) -> dict:
    '''
    detects if the reference entering this program is an IPCC, ipbes or guardian citation

    param ref : the string of a citation

    return :  a dictionnary containing as keys guardian, ipbes and IPCC and in values the name of the citation extracted
    '''
    g = {}
    citation = list(set(re.findall(r"(ipcc|ipbes|guardian)", ref, flags=re.IGNORECASE)))
    if citation != None and citation != []:
        if "ipcc" in citation:
            g["IPCC"] = citation
        if "ipbes" in citation:
            g["ipbes"] = citation
        if "guardian" in citation:
            g["guardian"] = citation
        return g
    else:
        return {}


def get_citations(wikicode: str) -> dict:
    '''
    param  wikicode: a string containing the wikicode of the page or section of which we want to extract the code

    return a dictionnary containing all the information about the citation we want to extract
    '''
    # detection of the citations in the wikicode
    citations = [c.lower() for c in re.findall(r'<ref(?:\s(?:[^\/]*?))?>(.*?)<\/ref>', wikicode) + re.findall(
        r'({{(?:cite|vcite2|Cite)\s[^}]*}})', wikicode)]
    s = set()

    i = 0
    for c in citations:
        i += 1
        s.update(c.split('<br/>'))

    # Creation of a dataframe containing the citation
    ds = pd.DataFrame(s, columns=['ref'])

    ds['ids'] = ds['ref'].apply(get_ids_from_ref)
    ds['pmid'] = ds['ids'].apply(lambda x: x.get('pmid', None))
    ds['doi'] = ds['ids'].apply(lambda x: x.get('doi', None))
    ds['pmc'] = ds['ids'].apply(lambda x: x.get('pmc', None))
    ds["journal"] = ds['ids'].apply(lambda x: x.get('journal', None))
    ds["access"] = ds['ids'].apply(lambda x: x.get('access', None))
    ds["available"] = ds["ids"] == {}

    dsbis = ds[(~ds['pmid'].isnull()) | ~(ds['doi'].isnull()) | ~(ds['pmc'].isnull())]

    ds = ds[(~ds['pmid'].duplicated()) | (ds['pmid'].isnull())]
    ds = ds[(~ds['doi'].duplicated()) | (ds['doi'].isnull())]
    ds = ds[(~ds['pmc'].duplicated()) | (ds['pmc'].isnull())]

    dg = ds.loc[ds["available"] == True, ["ref"]]
    dg['ids'] = dg['ref'].apply(get_IPCC_guardian_ipbes_from_ref)
    dg['IPCC'] = dg['ids'].apply(lambda x: x.get('IPCC', None))
    dg['ipbes'] = dg['ids'].apply(lambda x: x.get('ipbes', None))
    dg['guard'] = dg['ids'].apply(lambda x: x.get('guardian', None))
    dg["available"] = dg["ids"] == {}

    dcit = dg.loc[dg["available"] == True, ["ref"]]
    dcit['ids'] = dcit['ref'].apply(get_cit_from_ref)
    dcit['org'] = dcit['ids'].apply(lambda x: x.get('org', None))
    dcit['gov'] = dcit['ids'].apply(lambda x: x.get('gov', None))
    dcit['com'] = dcit['ids'].apply(lambda x: x.get('com', None))
    dcit['ncbi'] = dcit['ids'].apply(lambda x: x.get('ncbi.nlm.nih.gov', None))
    dcit["available"] = dcit["ids"] == {}

    # creation of a data frame with all the other type of citation that weren't extracted
    drest = dcit.loc[dcit["available"] == True, ["ref"]]

    dsjournal = ds[(~ds['journal'].isnull())]
    dgbisgov = dcit[(~dcit['gov'].isnull())]
    dgbisorg = dcit[(~dcit['org'].isnull())]
    dgbisIPCC = dg[(~dg['IPCC'].isnull())]
    dgbiscom = dcit[(~dcit['com'].isnull())]
    dgbisncbi = dcit[(~dcit['ncbi'].isnull())]

    dsaccess = ds[(~ds["access"].isnull())]
    dic = {'Ref count': ds.shape[0],
           'journal_count': ds[(~ds['journal'].isnull())].shape[0] + dcit[(~dcit['ncbi'].isnull())].shape[0],
           'nb_journal_citations': (dcit[(~dcit['ncbi'].isnull())]).shape[0] +
                                   ds[(~ds['pmid'].isnull()) | (~ds['doi'].isnull()) | (~ds['pmc'].isnull())].shape[0],
           "citationjournal": list(
               list(dsbis["doi"]) + list(dsbis["pmid"]) + list(dsbis["pmc"]) + list(dgbisncbi["ncbi"])),
           "citations.org": dcit[(~dcit['org'].isnull())].shape[0],
           "citations.gov": dcit[(~dcit['gov'].isnull())].shape[0],
           "citationgovtext": list(dgbisgov['gov']),
           "citationorgtext": list(dgbisorg['org']),
           "citationsIPCC.ch": dg[(~dg['IPCC'].isnull())].shape[0],
           "citationautre": drest["ref"].shape[0],
           "citationcomtext": list(dgbiscom['com']),
           "access": list(dsaccess["access"]),
           "nbaccessdetect": dsaccess["access"].shape[0],
           "journal": list(dsjournal['journal']) + list(dgbisncbi["ncbi"]),
           "citations.com": dcit[(~dcit['com'].isnull())].shape[0],
           "citationsipbes": dg[(~dg['ipbes'].isnull())].shape[0],
           "citationguardian": dg[(~dg['guard'].isnull())].shape[0]}

    return dic


def creadicorg(name_cit: str, dicorg: dict, num):
    # todo: rename, improve exlanation
    '''
    and the citation name_cit to the dictionnary dicorg

    param name_cit: the name of the citation in the form of a string
    param dicorg: a dictionnary containing the name and number of citation already found is updated thanks to this funciton
    return dicorg
    '''
    # print(name_cit)
    name_cit = name_cit.replace('www.', '')
    name_cit = re.sub('^(\[| )*', '', name_cit)
    name_cit = re.sub(' *$', '', name_cit)
    if "proceedings of the national academy of science" in name_cit or "pnas" in name_cit:
        name_cit = "PNAS"
    if "google" in name_cit:
        name_cit = "books.google.com"
    if name_cit in dicorg:
        dicorg[name_cit] += 1
    else:
        dicorg[name_cit] = 1
    num += 1
    return dicorg, num


def sortcitation(d, type_of_cit: str):
    '''
    param d: a column of a dataframe containing the text of the citation

    return dico: a dictionnary  the name of the site of interest and the numbers of time it is found in d.
    return dforg : a dataframe containing the name of the site of interest and the numbers of time it's found in descending order.
    '''

    dicorg = {}
    num = 0

    for liste_cit in d:
        # if the list is empty there is no need to extract

        if type(liste_cit) == str:
            dicorg, num = creadicorg(liste_cit, dicorg, num)

        if type(liste_cit) == list:

            for i in liste_cit:
                if type(i) == str:
                    dicorg, num = creadicorg(i, dicorg, num)
                else:
                    for j in i:
                        if type(j) == str:

                            dicorg, num = creadicorg(j, dicorg, num)
                        else:
                            for r in j:
                                if type(r) == str:

                                    dicorg, num = creadicorg(r, dicorg, num)
                                else:
                                    for t in r:
                                        if type(t) == str:
                                            dicorg, num = creadicorg(t, dicorg, num)
                                        else:
                                            print("test", liste_cit)
                            # dicorg=creadicorg(name_cit,dicorg)

    dico = dicorg
    # with all dictionary keys with values.
    dforg = pd.DataFrame(list(dicorg.items()), columns=['name of site', 'number of times cited'])
    dforg["type"] = type_of_cit
    dforg.sort_values(by=['number of times cited'], inplace=True, ascending=False)
    return dforg, dico


def plot_site_most_cited(d, top: int, title: str):
    '''
    plot the most cited sites

    param d: a column of a dataframe containing the text of the type of citation for example .org or only scientific journal
    param minimum: the minimum number of times an site is cited to appear in our plot
    '''

    sns.set_style("white")
    d = d[0:top]
    palette = {"org": "#8da0cb",
               "com": "#fc8d62",
               "IPCC": "#a6d854",
               "gov": "#e78ac3",
               "journal": "#66c2a5"}

    ax = sns.barplot(x="number of times cited", y="name of site", hue="type", palette=palette, data=d, dodge=False,
                     orient='h')
    # sns.despine(left=True, bottom=True)
    sns.move_legend(ax, "lower right")
    for i in ax.containers:
        ax.bar_label(i, )
    # sns.set(font_scale=3)
    plt.legend(loc=2, bbox_to_anchor=(1, 0.5))
    ax.set(xlabel='Number of references', ylabel='', title=title)
    # sns.set_context("paper")
    sns.set_context("poster")
    sns.set(rc={"figure.figsize": (12, 11)})  # width=3, #height=4
    sfig = ax.get_figure()
    sfig.savefig('most cited journal.svg')
    # plt.savefig('most cited journal.png')


def get_modified_urls(names_col):
    # todo(future): support non-english urls
    titlelist = names_col.tolist()  # make a list will all titles
    # We need to recreate the wiki url, first step is to get rid of blanks
    titleunderscore = [sub.replace(' ', '_') for sub in titlelist]
    urls_modified = ['https://en.wikipedia.org/w/index.php?title=' + i + '&action=info' for i in titleunderscore]
    return urls_modified