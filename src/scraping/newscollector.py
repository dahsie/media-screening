from newsapiscraper import *
from googlescraper import *
from typing import Union

class NewsCollector:
    """
    A class to collect news articles using specified scrapers.
    """

    def __init__(self, scraper: Union[GoogleScraper, NewsApiScraper], config :dict, path_to_save):
        """Initialises the NewsCollector."""
        self.scraper = scraper
        self.news_config = config
        self.path_to_save = path_to_save
        self.limit : int =30720


    def collect_news(self):
        """Collects news articles based on the provided configuration."""
        
        dataframe = None
        for item in tqdm(self.news_config):
            print(item)
            self.scraper.country = item['country']
            self.scraper.lang = item['lang']
            for query in item['queries']:
                
                self.scraper.query =  query
                self.scraper.news_collection()
                print(self.scraper.country, self.scraper.lang, self.scraper.query)
                data_ = self.scraper.articles_dataframe

                data_ = data_.loc[data_['titles'] !='',:] if data_ is not None and len(data_) !=0  else None

                data_ = data_.loc[data_['texts'] !='',:] if data_ is not None and  len(data_) !=0 else None
                data_ = data_.loc[data_['texts'].str.len() < self.limit, :] if data_ is not None and  len(data_) !=0 else None
                if data_ is not None :
                    print(f" data_.shape :{ data_.shape}")

                if data_ is None or len(data_) == 0:
                    continue
                    
                dataframe = pd.concat([dataframe, data_], axis=0)
        self.data = dataframe
        dataframe.to_csv(self.path_to_save, index= False)
        return self.data