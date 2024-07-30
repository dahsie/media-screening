
from scraper import *


import requests
import re
import math

from newspaper import  Article, Config

from tqdm import tqdm
from pygooglenews import GoogleNews

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
                 save_path : str = None,start_date :str= None, #year-moonth-day (i.e '2024-05-18')
                end_date :date = date.today().strftime('%Y-%m-%d'), when = '1d', ecart : int =1, true_link :bool= False,timeout :float = 5,
                 user_agent : str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                ) -> None:
        """
        """
        super(GoogleScraper, self).__init__(
                          save_path = save_path,end_date = end_date,ecart = ecart,start_date = start_date,
                         user_agent =user_agent, country = country, lang= lang, timeout = timeout, query = query)
        self.topic = topic
        self.geo_loc = geo_loc
        self.engine_init()
        self.when = when
        self._true_link = true_link
        self.selector =".VtwTSb > form:nth-child(1) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1) > span:nth-child(4)"

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
    
    def process_article(self,article, links, dates, times, titles):
        """
        Processes an individual article and appends relevant information to the lists.

        Args:
            article (dict): The article data obtained from the Google News API.
            links (list): List to store article URLs.
            dates (list): List to store article publication dates.
            times (list): List to store article publication times.
            titles (list): List to store article titles.
        """
        
        if article['link'] not in links and article['link'] not in self.URLS:
            url = article['link']
            if self._true_link:
                url = requests.head(url, allow_redirects=True).url
    
            self.URLS.append(url)
            titles.append(article['title'])
            links.append(url)
            dates.append(f"{article['published_parsed'].tm_year}-{article['published_parsed'].tm_mon:02d}-{article['published_parsed'].tm_mday:02d}")
            times.append( f"{article['published_parsed'].tm_hour:02d}:{article['published_parsed'].tm_min:02d}:{article['published_parsed'].tm_sec:02d}")
            
    def fetch_articles(self)-> list[str] :
        """
        Fetches and processes articles from Google News.

        This method calls the `google_search` method to obtain articles and processes each
        article. It updates the lists of links, dates, times, and titles with the processed data.

        """
        sources = set()
        articles, dates, times, links, titles = [],[],[],[],[]
        json_data = self.google_search()
        for article in json_data['entries'] :
            sources.add(article['source'])
            self.process_article(article, links, dates, times, titles)
            if len(article['sub_articles']) != 0:
                for sub_article in article['sub_articles']:
                    self.process_article(sub_article, links, dates, times, titles)
        self.links, self.dates, self.times, self.titles = links, dates, times, titles
        self.sources = list(sources)
        print("Google search ended !")
    
    def scrapping(self,links, dates, times, download : bool =False, google = False, verbose = False):
        """
        This method processes a list of news article URLs and extracts relevant information from each article using a WebDriver.

        Args:
            links (list of str): A list of URLs to news articles that need to be processed.
            dates (list of str): A list of publication dates corresponding to the URLs.
            times (list of str): A list of publication times corresponding to the URLs.
            titles (list of str): A list of titles corresponding to the URLs.
            download (bool, optional): Flag indicating whether to download the articles. Default is False.
            google (bool, optional): Flag indicating whether the articles are from Google News. Default is False.
            verbose (bool, optional): Flag to control the verbosity of the method's output. Default is False.

        Returns:
            list of dict: A list of dictionaries where each dictionary contains the following keys:
                - "date" (str): The publication date of the article in 'YYYY-MM-DD' format.
                - "time" (str): The publication time of the article in 'HH:MM:SS' format.
                - "title" (str): The title of the article.
                - "text" (str): The main content of the article.
                - "url" (str): The URL of the article.

        Note:
            This method uses a WebDriver to navigate to each URL and extract article content. It handles cookies acceptance and waits for the page to load.
            If an exception occurs while processing an article, the error is silently ignored.
            The `verbose` parameter can be used to enable detailed logging of the process.
        """
        
        article = Article("//")
        for i, link in enumerate(tqdm(links)):

            try :
                if i == 0:
                    sleep(1)
                    self.driver.find_element(By.CSS_SELECTOR, self.selector).click() # accept cookies
                self.driver.get(link)
                sleep(1)
                article.download(input_html = self.driver.page_source )
                article.parse()

                papers.append({
                    "date" : dates[i],
                    "time" : times[i],
                    "title" : titles[i],
                    "text" : article.text,
                    "url" : self.driver.current_url,
                })
            except Exception as e :
                pass
        return papers
    
    def news_collection(self):
        """
        Collects news articles by first fetching article metadata (links, dates, etc.) and then scraping each article for its full content.

        This method first calls `fetch_articles` to obtain a list of articles based on the current search parameters.
        It then uses the `scrapping` method to process the articles and extract their content. The resulting list of
        articles is passed to the parent class's `news_collection` method for further processing.

        Note:
            This method assumes that the `fetch_articles` method has been defined and correctly populates the lists of links,
            dates, times, and titles. It also assumes that `scrapping` method handles the actual content extraction from the URLs.

        Calls:
            - `self.fetch_articles()`: To fetch the article metadata.
            - `self.scrapping(...)`: To extract the content from the article URLs.
            - `super(GoogleScraper, self).news_collection(...)`: To call the parent class's `news_collection` method with the collected data.
        """
        self.fetch_articles()
        google_papers = self.scrapping(self.links, self.dates, self.times, self.titles, download=True, google=True, verbose = True)
        super(GoogleScraper, self).news_collection(google_papers)
