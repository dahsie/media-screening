import sys
sys.path.append("../src/pygooglenews")
sys.path.append("../src/utils")

from scraper import *


import requests
import re
import math
import time 
from time import sleep

from newspaper import  Article, Config


from tqdm import tqdm
from pygooglenews import GoogleNews

import selenium
from selenium import webdriver #Webdriver de Selenium qui permet de contrôler un navigateur
from selenium.webdriver.common.by import By 
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

from utils import create_logger

logger = create_logger(__name__, 'google_scrapper.log')


class GoogleScraper(Scraper) :
    
    """
    A scraper for fetching news articles from Google News.

    This class extends the Scraper class and provides functionality to fetch, process,
    and store news articles using Google News. It supports querying by topic, location,
    date ranges, and additional filters.

    Attributes:
        country (str): The country code (e.g., 'us', 'fr') for news filtering.
        lang (str): The language code (e.g., 'en', 'fr') for news filtering.
        query (str, optional): A search query to filter the news articles.
        topic (str, optional): A topic to filter the news articles (e.g., 'WORLD', 'TECHNOLOGY').
        geo_loc (str, optional): A geographical location to filter the news articles.
        save_path (str, optional): Path to save the collected news articles as a CSV file.
        start_date (str, optional): The start date for the news articles (format 'YYYY-MM-DD').
        end_date (str, optional): The end date for the news articles (format 'YYYY-MM-DD').
        when (str): Time period for the news articles (e.g., '1d' for 1 day).
        ecart (int): The number of days to subtract from the end date to determine the start date if not provided.
        true_link (bool): Flag to indicate whether to follow redirects to the final article URL.
        timeout (float): Timeout duration for HTTP requests.
        user_agent (str): User agent string for HTTP requests.
    """
    def __init__(self, 
                country :str,lang : str,query :str = None,topic :str = None,geo_loc : str = None,
                save_path : str = None,start_date :str= None, 
                end_date :date = date.today().strftime('%Y-%m-%d'), when = '1d', ecart : int =1, true_link :bool= False,timeout :float = 5,
                ) -> None:
        """
        """
        super(GoogleScraper, self).__init__(
                          save_path = save_path,end_date = end_date,ecart = ecart,start_date = start_date,
                         country = country, lang= lang, timeout = timeout, query = query)
        self.topic = topic
        self.geo_loc = geo_loc
        self.engine_init()
        self.when = when
        self._true_link = true_link
        self.selector =".VtwTSb > form:nth-child(1) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1) > span:nth-child(4)"
        self.__first_scraping = True # Allow to know if GoogleScraper object is being used for the first time

    @Scraper.country.setter
    def country(self, country):
        """
        Setter for the country attribute.

        Args:
            country (str): The new country code for news filtering.
        """
        Scraper.country.fset(self, country)
        if hasattr(self, 'gn'):
            self.gn.country = self._country

    @Scraper.lang.setter
    def lang(self, lang):
        """
        Setter for the lang attribute.

        Args:
            lang (str): The new language code for news filtering.
        """
        Scraper.lang.fset(self, lang)
        if hasattr(self, 'gn'):
            self.gn.lang = self._lang
    
    @Scraper.timeout.setter
    def timeout(self, timeout):
        """
        Setter for the timeout attribute.

        Args:
            timeout (float): The new timeout duration for HTTP requests.
        """
        self._timemout = timeout
        if hasattr(self, 'driver') :
            self.driver.set_page_load_timeout(self._timeout)
    
    def kill_driver(self) :
        """
        Closes and quits the WebDriver instance if it exists.
        """
        if hasattr(self,'driver') :
            self.driver.close()
            self.driver.quit()
            
    def init_driver(self, options = None, driver = None) :
        """
        Initializes the WebDriver instance.

        Args:
            options (optional): WebDriver options to be used.
            driver (optional): An existing WebDriver instance to use.
        """
        if driver is not None :
            self.driver = driver
        else :
            
            if options is not None :
                if isinstance(options, selenium.webdriver.chrome.options.Options):
                    self.driver = webdriver.Chrome(options=options)
                elif isinstance(options, selenium.webdriver.firefox.options.Options):
                    self.driver = webdriver.Firefox(options=options)
            else :
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('disable-infobars')
                options.add_argument('--no-sandbox')
                self.driver = webdriver.Chrome(options=options)
                self.driver.set_page_load_timeout(self._timeout)
                
    
    def engine_init(self) -> None:
        """
        Initializes the Google News engine and WebDriver.

        If the Google News engine (`gn`) does not exist, it is created and initialized with
        the current language and country settings. The WebDriver is also initialized.
        """
        if not hasattr(self, 'gn'):
            self.gn = GoogleNews(lang=self._lang, country=self._country)
        else:
            self.gn.lang = self._lang
            self.gn.country = self._country
        self.init_driver()
            
    
    def search(self) -> dict :
        """
        Performs a search query on Google News based on the provided parameters.

        Returns:
            dict: A dictionary containing the search results from Google News.

        Raises:
            Exception: If an invalid topic is provided.
        """
        if self.query is not None : #ser=arch by query
            if self.start_date is not None and self.end_date is not None:
                return self.gn.search(self.query, from_=self.start_date, to_=self.end_date)
            elif self.when is not None :
                return self.gn.search(self.query, when=self.when)
            else :
                return self.gn.search(self.query)

        elif self.topic is not None : # Search by topic
            try:
                return self.gn.topic_headlines(self.topic, proxies=None, scraping_bee = None)
            except Exception as e:
                print(e)
                print(f"Accepted topics are : {'WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SCIENCE, SPORTS, HEALTH'}")
                
        elif self.geo_loc :
            return self.gn.geo_headlines(self.geo_loc)
        
        else :
            return self.gn.top_news()
    
    
    def process_article(self,article, **kwargs):
        """
        Processes an individual article and appends relevant information to the lists contained
        in the kwargs dictionary. Raises a ValueError if one or more required lists are missing.

        Args:
            article (dict): The article data obtained from the API.
            **kwargs: A dictionary containing lists to store article information:
                - 'links' (list): List to store article URLs.
                - 'dates' (list): List to store article publication dates.
                - 'titles' (list): List to store article titles.
                
        Raises:
            ValueError: If one or more required lists are missing from kwargs.
        """
        expected_keys = {'links', 'dates', 'titles'}
        if not expected_keys.issubset(kwargs.keys()):
            logger.error("Missing one or more required lists in kwargs.")
            raise ValueError("Missing one or more required lists in kwargs")
        
        if article['link'] not in kwargs['links'] and article['link'] not in self.URLS:
            self.URLS.append(article['link'])
            kwargs['links'].append(article['link'])
            kwargs['titles'].append(article['title'])
            kwargs['dates'].append(time.strftime('%Y-%m-%dT%H:%M:%SZ', article['published_parsed']))
            
    
    def fetch_articles(self) -> None:
        """
        Fetches and processes articles by updating the lists
        of links, dates and titles with the processed data.

        Returns:
            None
        """
        
        sources = set()
        kwargs = {
            "dates" : [],
            "titles" : [],
            "links" : []
        }

        json_data = self.search()

        for article in json_data['entries'] :
            sources.add(article['source'])
            self.process_article(article=article, **kwargs)
            
            if len(article['sub_articles']) != 0:
                for sub_article in article['sub_articles']:
                    self.process_article(article=sub_article, **kwargs)

        self.articles = kwargs
        self.sources = list(sources)
        print("search ended !")
    
    
    def scrapping(self, **kwargs):
        """
        Downloads and extracts text content from the article links.

        Args:
            **kwargs: A dictionary containing lists to store article information:
                -links (list): List of article URLs.
                -dates (list): List of article publication dates.
                -times (list): List of article publication times.
                -titles (list): List of article titles.

        Returns:
            dict: A dictionary containing the articles with their extracted text.
        """
        
        article = Article("//")
        texts = []
        true_links = []
        fails_index = []
        for i, link in enumerate(tqdm(kwargs["links"])):
            
            try :
                self.driver.get(link)

                if self.__first_scraping:
                    sleep(1)
                    self.driver.find_element(By.CSS_SELECTOR, self.selector).click() # accept cookies
                    self.__first_scraping = False
                
                sleep(1)

                article.download(input_html = self.driver.page_source )
                article.parse()
                
                texts.append(article.text)
                true_links.append(self.driver.current_url)
                
            except Exception as e : # If exception it means that we do not get the text correctly the index will be kept so that some processing will be made on them
                fails_index.append(i)
        
        for index in fails_index : # Deleting the failing index titles and dates so that 'texts' will match them (texts, articles["dates"], articles["titles"] must have the same length
            self.articles['dates'].pop(index)
            self.articles['titles'].pop(index)
        
        self.articles['texts']  = texts
        self.articles['links'] = true_links
    
    def news_collection(self):
        """
        Collects news articles, processes them, and optionally saves them.

        Fetches articles, extracts relevant information, and uses the parent class's
        `news_collection` method to save the articles if a save path is provided.

        Returns:
            None
        """
        self.fetch_articles()
        self.scrapping(**self.articles)
        super(GoogleScraper, self).news_collection(self.articles)
        logger.info("News collection completed.")
