# Project Description

This tool is a part of a broader project* of using wikipedia to analyze contemporary history of science.

Our code generates a group of wikipedia article ("corpus") based on a Term Of Interest (TOI) of the user.

1. It first selects all the wikipedia articles based on the defined criteria (see below)
2. It scraps certain data for all these articles (see below)

The output is dataframe containing all the selected wikipedia articles and their data
The code also generates some plots of the data

*Published works:
O. Benjakob# and R. Aviram#. A clockwork Wikipedia: from a broad perspective to a case study. Journal of Biological Rhythms, 2018
O. Benjakob#, R. Aviram#, J. Sobel#. Citation needed? Wikipedia and the COVID-19 pandemic. GigaScience, 2022

## How are articles selected ?

The code will search all the articles of the English Wikipedia for those containing the TOI.
Within this broad search, the code will filter only those articles containing the TOI in their article title or the title of a section, subsection or subsubsection.

## Which data are scraped ?

For each article, the following data are scrapped: article name, its url, a count of the article's references, a count of scientific journal citations, a Sciscore (see below), the page protection status, the page length, the date of birth, the creator user id, the total number of edits, the recent edits and the date of birth in some useful formats.

All the data comes from the "page information", the main "Article" page and the "page statistics" (Xtools).

Using these scraped data, we also apply some basics functions for instance to calculate the [Sci-score](https://github.com/Augustoni/wiki-score/edit/main/README.md#sci-score-).

### Sciscore 
The Sciscore is the ratio of scientific papers of the total number of references (and therefore lies between 0 and 1). For its calculation, we count the total number refernces in a given Wikipedia article, and the nuber of either doi, pmid or pmc, based on the assumption that scientific references have a doi, a pmid or a pmc. In Wikipedia, there could be miscounts due to erronous citation formatting.
A score close to 1 means a higly scientific based article.
A score close to 0 means a low scientific based article.

# How to Install and Run the Project

## Installation
To run the code first install the following : [setuptools](https://pypi.org/project/setuptools/), [pywikibot](https://github.com/wikimedia/pywikibot#readme), [mwparserfromhell](https://mwparserfromhell.readthedocs.io/en/latest/), [pandas](https://pandas.pydata.org/), [numpy](https://numpy.org/install/), [scipy](https://scipy.org/install/), [nltk](https://www.nltk.org/install.html), [tqdm](https://tqdm.github.io/), [wikipedia](https://pypi.org/project/wikipedia/), [pyqt5](https://pypi.org/project/PyQt5/), [pyqtwebengine](https://pypi.org/project/PyQtWebEngine/), [pathlib](https://docs.python.org/3/library/pathlib.html), [ruamel-yaml](https://pypi.org/project/ruamel.yaml/), [lxml](https://lxml.de/installation.html) and [seaborn](https://seaborn.pydata.org/)

All can be installed using pip : 

```
!pip install wikipedia setuptools pywikibot mwparserfromhell pandas numpy scipy nltk tqdm seaborn pyqt5 pyqtwebengine ruamel-yaml lxml
```
## Run the Project

The project has two ways of working at the moment - notebook or pure python:

1. (ipynb) The project is contained in a .ipynb file which corresponds to a python notebook file. The code is designed to be run using the cells' logic of a notebook. [Jupyter](https://jupyter.org/) is an example of a free notebook you can use.
To create the corpus first launch *corpus creation and name of journal analysis* notebook. Then to compare corpora you can launch the *poster figures* notebook. 
If you want to have the history on one article using wikicode manually found you can look at the branch history.
The *wikipediaAnalysishistory* notebook is made based on Leo Blondel code that you can find in this gitlab: https://gitlab.com/xqua/wikipedia-data-collector/-/tree/main 
This notebook is a modification of the notebook *WikipediaAnalysisDemo* with the extraction of the name of the citation to make it work yu firstly need to run the code on Leo Blondel's Github.

2) (python) just run the command 
   >> python3 corpus_creation.py -term 'circadian clock' 

   or use the file starter.sh which can be run more easily (edit it with text editor then run it)
   
# How to Use the Project

## Corpus Selection 
To launch the corpus selection for your article, you need to use your arguments for the function "corpus_selection".
In the function "corpus selection":
1. The first argument of our function correspond to the name of the main article.
2. The second argument is the number of article that the wiki search will analyze (5000 is the maximum).
3. The third argument is the keyword that will be searched in the main titles and the titles of sections, subsections or subsubsections.

In other words, you need to replace "Effects of climate change" by your main article and "Climate change" with the keywords for your corpus.

![image](https://user-images.githubusercontent.com/60670025/167416548-4a2ee4f1-d15b-4ed6-b877-708876ffaa77.png)

This function usually lasts 1h-2h. Do not turn off your computer. 

### Fine tuning the corpus selection code
By default, the code scrapps the whole text for each article. This means that the information on the references are concerning the whole article. However, for the article of the corpus that do not contain the keyword in their main title, the whole article may not be relevant of what you are studying. As so, if you only want to scrap the references of the section whose title contains your keyword, remove the ''' ''' shown in the picture: 

![image](https://user-images.githubusercontent.com/60670025/167449184-7e5fcb83-3ba2-4abd-89cb-37e8101f1e49.png)

You also need to remove the ''' ''' and the "line page_text=page‧text" if you want the more precise wikicode. Use "#" to comment the line, inactivating it without fully loosing it.

![image](https://user-images.githubusercontent.com/60670025/167449226-4967675f-fa0f-42dd-b3cd-967846f0e017.png)

## Plotting the data
The corresponding cells need to be run once the corpus has been charged. You get access to the following plots:
1. A pie chart of the creators
2. A yearly timeline of the artices date of birth
3. Barplots of the most cited references

# Acknowledgements

This code is the product of the talented LPI students: Ariane Augustoni, Louise Jouveshomme and Matthieu Collet. They based their work on the work of Leo Blondel and Jean-Marc Sevin. The code was later improved by Roy Amit. All was done under the supervision and reseach design of Omer Benjakob and Rona Aviram. 
