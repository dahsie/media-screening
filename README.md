# Media screening

We build a pipeline which scrape news from internet related to some event like **labor strike**, **fire plant** and **flood** and then apply some sophisticated **Machine Learning**, **Deep Learning** and **Generative AI** in order to detect some relevant news that can impact Supplier Chain. To be accurate about classifying a collected news as relevant or not, we extract some information and match those informations to a supplier database. This image below describe the whole pipeline we put in place

![image.png](attachment:image.png)
## Install

We have to branch :
* Master : This branch work on **GCP**
* Dataiku : This branch is a dataiku version. Threre are some differences between the two branch. For exemple, requests are made to get access to **Gemini**, which is not the case when we are already on **GCP**

## Install all branches
git clone --branch test --single-branch https://github.com/dahsie/media-screening.git

## Install only Dataiku branch :
git clone --branch dataiku --single-branch https://github.com/dahsie/media-screening.git

## Install only Master branch :
git clone --branch master --single-branch https://github.com/dahsie/media-screening.git

# Exemple for Dataiku
## Creating configuration file.
In this part, we translate each keywords to some languages, depending on the list of language code we have in our disposal.

```py
dict_config = {}
dict_config['strike_keywords'] = ['strike', 'picket line', 'employee protest']
dict_config['country_lang'] = [
    {'country': 'BE','lang': ['fr']}, # Belgium
    {'country': 'CH','lang': ['fr', 'de', 'it']}, # Searching news with differentes languge in the same country where threre are several official language
    {'country': 'BG','lang': ['bg']},  # Bulgaria
    {'country': 'BR','lang': ['pt']}
    ]

# RAG configuration
dict_config['rag_cong'] = {'vertexai_llm': 'gemini-1.5-flash',
                            'vertexai_embedding_name': 'models/text-embedding-004',
                            'chunk_size': 2000, 'chunk_overlap': 10, 'max_doc': 5, 'retry': 1}

# List of non desirable sectors
dict_config["sectors_to_discard"] = sectors_to_discard.SECTORS_TO_DISCARD # Or spécify a liste of sectors you want to discard
dict_config["decision_function_args"] = {
    'sectors_to_discard': sectors_to_discard.SECTORS_TO_DISCARD, # Or spécify a liste of sectors you want to discard
    'desirable_temporalities' : ['upcoming', 'ongoing', 'unknown'] # for the labor strike, we discard ended and avoided strike
}
```

#### generating an initial configuration file.
We can save the first dict whithin a file and we can use it later

```py
initial_config_file ="../config/initial_config_file.json"
with open(initial_config_file, 'w') as file :
    json.dump(dict_config, file, indent = 4)
```

#### generating a final configuration file.
All keyword in the initial configuartion file will be translated into each language using the language code. 
Also, each language code and country code should be valiadated. A configuration object will be use for that purpose. 

```py
from media.src.confiration.configuration import Configuration

initial_config_file = "../config/initial_config_file.json"
final_config_file = "../config/final_config_file.json"
config = Configuration( initial_config_file = initial_config_file, final_config_file = final_config_file)
```

The final configuration file can be save for further usage. So we do not have to generate it every time. 


## Collecting news

We have to ways of collecting news. We utilise both :
* **News API**, Commercial API for getting news with a specifique keywords. However the API is very limited and can catch an limited number of news.
* **GoogleScraper**, A algorirgme we designed for news collected. It lean on **Google News RSS**. We use **Selenium** a python librairie for scraping a dynamic website.

#### collecting news with GoogleScrapper 

```py
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
import math
import json
from tqdm import tqdm
from media.src.utils.utils import read_dataiku_json
from media.src.scraping.newscollector import NewsCollector
from media.src.scraping.googlescraper import GoogleScraper
from media.src.utils.utils import read_dataiku_json
from datetime import datetime, timedelta
from media.src.utils.utils import write_logger_file

end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(days=1)).strftime('%Y-%m-%d')

today = datetime.now()
yesterday_start = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday_end = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)


#Reading the final configuration we have generate before
config = read_dataiku_json(folder_name ='configuration_files', file_name='final_config_file.json')

#index = math.ceil(len(config['country_lang'])/3)

googlescraper = GoogleScraper(start_date=start_date,end_date=end_date)

#NewsCollector use a GoogleScrapper object to iterate through the list of countries where we want to collect news.
google_collector = NewsCollector(config=config['country_lang'], scraper=googlescraper,path_to_save=None)
df = google_collector.collect_news()

if df is None or df.empty:
    df = pd.DataFrame({
        "dates" :[],
        "titles":[],
        "links":[],
        "texts":[],
        "lang": [],
        "cat":[]
    })

# Write recipe outputs
fire_data = dataiku.Dataset("googlescraper_strike1")
fire_data.write_with_schema(df)

#Writhing log for debug purpose
write_logger_file(logger_folder_name = 'googlescraper_strike_log', log_file_name = google_collector.logfile_path, final_log_name="googlescraper_strike1.log")

```

#### collecting news with News API

```py
import dataiku
import pandas as pd, numpy as np

from media.src.scraping.newsapiscraper import NewsApiScraper
from media.src.scraping.newscollector import NewsCollector
from media.src.utils.utils import get_api_key
from media.src.utils.utils import read_dataiku_json
from datetime import datetime, timedelta
from media.src.utils.utils import write_logger_file



config = read_dataiku_json(folder_name ='configuration_files', file_name='final_config_file.json')

today = datetime.now()
yesterday_start = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday_end = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
start_date = yesterday_start.strftime("%Y-%m-%dT%H:%M:%SZ")
end_date = yesterday_end.strftime("%Y-%m-%dT%H:%M:%SZ")

NEWS_API_KEY = get_api_key("NEWS_API_KEY")

scrapper = NewsApiScraper(api_key= NEWS_API_KEY , start_date=start_date,end_date=end_date)

collector = NewsCollector(config=config['country_lang'], scraper=scrapper,path_to_save=None)
df = collector.collect_news()

# Write recipe outputs
strike_data = dataiku.Dataset("strike_news")
strike_data.write_with_schema(df)

write_logger_file(logger_folder_name = 'news_api_strike_log', log_file_name = collector.logfile_path, final_log_name="strike_news.log")

```

#### Concatenating collected news via News API and GoogleScrapper 
News are collected in parallel via News API and GoogleScrapper. If one solution are down the other one remain while finding out what cause the crash.
If there all work, we get more news buy concatenating there results.

```py
import dataiku
import pandas as pd, numpy as np
from datetime import datetime, timedelta

# Read recipe inputs
news_api_strike = dataiku.Dataset("strike_news")
news_api_strike_df = news_api_strike.get_dataframe()


googlescraper_strike1 = dataiku.Dataset("googlescraper_strike1")
googlescraper_strike1_df = googlescraper_strike1.get_dataframe()




news_df = pd.concat([googlescraper_strike1_df, news_api_strike_df])

news_df.dropna(inplace= True)

# filter data base on date
today = datetime.now()
yesterday_start = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday_end = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
start_date = yesterday_start.strftime("%Y-%m-%dT%H:%M:%SZ")
end_date = yesterday_end.strftime("%Y-%m-%dT%H:%M:%SZ")
news_df = news_df[(news_df['dates'] <= end_date) & (news_df['dates'] >= start_date)]

# Write recipe outputs
news = dataiku.Dataset("news")
news.write_with_schema(news_df)
```

### Translation 

We translate all collected news into english. We have to possibilties : either we translate all the text into a single language (e.g. english) or we use a multilanguage model for the remaing processing we want to apply. We choose the first solution. 

```py
import dataiku
import pandas as pd
import numpy as np
import json
from dataiku import pandasutils as pdu
from media.src.utils.utils import get_api_key
#from media.src.translation.dataikugoogletranslation import DataikuGoogleTranslate
from media.src.translation.dataikugoogletranslation_copy import DataikuGoogleTranslate

from media.src.utils.utils import read_dataiku_json
from media.src.utils.utils import write_logger_file

# Read recipe inputs
# Dataset news_ renamed to news by p126399 on 2024-09-10 16:08:32
googlescraper_strike_stacked = dataiku.Dataset("news")
googlescraper_strike_stacked_df = googlescraper_strike_stacked.get_dataframe()


df = googlescraper_strike_stacked_df # For this sample code, simply copy input to output

# cleaning NAN
df.dropna(inplace=True)

#Dropping duplicates
df = (df.drop_duplicates(subset=['titles'])).sort_index()
df = (df.drop_duplicates(subset=['texts'])).sort_index()
df = (df.drop_duplicates(subset=['links'])).sort_index()

# Resetting the index
df = df.reset_index(drop=True)

GOOGLE_API_KEY = get_api_key(name ="GOOGLE_API_KEY")

# For translation purposes, one may encounter some issues with the number of tokens sent in each request.
# This number of tokens depends on the language. 6000 tokens is the default value.

config = read_dataiku_json(folder_name ='configuration_files', file_name='final_config_file.json')

translation = DataikuGoogleTranslate(api_key=GOOGLE_API_KEY)


trans_df = translation.translation(df, language_limits=config["language_limits"])


#Dropping duplicates
trans_df = (trans_df.drop_duplicates(subset=['titles'])).sort_index()
trans_df = (trans_df.drop_duplicates(subset=['texts'])).sort_index()
trans_df = (trans_df.drop_duplicates(subset=['links'])).sort_index()

# Resetting the index
trans_df = trans_df.reset_index(drop=True)

# a bit cleaning
if len(trans_df) == 0 :
    trans_df = None
else :
 
    trans_df = trans_df[trans_df['translated_title'].str.count('\s+').ge(3)] #keep only titles having more than 4 spaces in the title
    trans_df = trans_df[trans_df['translated_text'].str.count('\s+').ge(20)] #keep only titles having more than 20 spaces in the body

    trans_df = (trans_df.drop_duplicates(subset=['translated_title'])).sort_index()
    trans_df = (trans_df.drop_duplicates(subset=['translated_text'])).sort_index()
    trans_df = (trans_df.drop_duplicates(subset=['links'])).sort_index()
    trans_df = trans_df.reset_index(drop=True)

    if len(trans_df) == 0 :
        trans_df = None
# Write recipe outputs

dataset = dataiku.Dataset("translated_data")
dataset.write_with_schema(trans_df)

write_logger_file(logger_folder_name = 'strike_translation_log', log_file_name = translation.logfile_path, final_log_name="strike_translation_log.log")
```

### CLustering
After translating the collected news and dropping duplications base on the text, title and link, there are also some very similar news. We want to cluster the news before extracting information on the each cluster. So we compute the embedding of each text and then apply the hierarchical clustering technique. The image below descibe the clustering process :
![image-2.png](attachment:image-2.png)

```py
import dataiku
import pandas as pd
import numpy as np
from dataiku import pandasutils as pdu
from media.src.embeddings.dataikugoogleembeddings import DataikuGoogleEmbeddings
from media.src.clustering.clustering import Clustering
from media.src.utils.utils import get_api_key
from media.src.utils.utils import write_logger_file
from media.src.utils.utils import copy_log_file


# Read recipe inputs
translated_data = dataiku.Dataset("translated_data")
trans_df = translated_data.get_dataframe()


texts = list(trans_df['translated_text'])

GOOGLE_API_KEY = get_api_key("GOOGLE_API_KEY")

dataiu_embeddings = DataikuGoogleEmbeddings(google_api_key=GOOGLE_API_KEY)
dataiu_embeddings.fit_transform(sentences=texts)

xtrain = dataiu_embeddings.embedded_data


model = Clustering(percentile=10, linkage='average', metric='cosine')

copy_log_file(dataiu_embeddings.logfile_path, model.logfile_path)

model.fit(xtrain, n=500)
ypred = model.predict(xtrain)


trans_df['class'] = ypred


trans_df = trans_df.rename(columns= {'links': 'url', 'dates': 'date'})
rag_data = trans_df[['date', 'cat', 'lang', 'url','translated_title', 'translated_text', 'class']]


rag_data = rag_data.fillna('')


# Write recipe outputs
rag_dataset = dataiku.Dataset("rag_dataset")
rag_dataset.write_with_schema(rag_data)


write_logger_file(logger_folder_name = 'strike_clustering_log', log_file_name = model.logfile_path, final_log_name="strike_clustering_log.log")


```

Clustering resulats :

![image-3.png](attachment:image-3.png)

### RAG : Retreival Augmented Generation 

We used the **RAG** technique in order to extract some information, for instance, companies names, their location (cities and countris where the strike is taking place), the activities sectors(this allow to know if their activities are related to automotive construction), the strike stutus(if the strike is ongoing, upcoming, ended or avoided because no interest for has if the strike is ended or avoider), the naure of the strike(labor strike in this exemple. This allows avoiding some other strike like hunger strike, etc.).  All those information couple with the [**matching process**](#matching_process) allows us to classify a news as relevant or not.

We start RAG process by creating an indexing database or vectorstore as this image shows 

![image-4.png](attachment:image-4.png)

After creating the vectorstore, the RAG process consist of two phases as the image below shows:
![image-5.png](attachment:image-5.png)

To improve information Retrieval process, we extract information iteratively as the iamge shows :
![image-6.png](attachment:image-6.png)
```py
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
from io import StringIO
from datetime import datetime
from media.src.rag.strike_rag import StrikeRAG
from media.src.utils.utils import get_api_key
from media.src.utils.utils import read_dataiku_json
from media.src.utils.utils import write_dataiku_json

from media.src.utils.utils import write_logger_file


#Getting google api key for generative model
GOOGLE_API_KEY = get_api_key('GOOGLE_API_KEY')

# Read recipe inputs
rag_dataset = dataiku.Dataset("rag_dataset")
rag_dataset_df = rag_dataset.get_dataframe()


# Getting rag configuration
conf = read_dataiku_json(folder_name ='configuration_files', file_name='final_config_file_test.json')

# Instanciating StrikeRAG object
strike = StrikeRAG(google_api_key = GOOGLE_API_KEY, vertexai_llm= conf['rag_cong']['vertexai_llm'],
                   vertexai_embedding_name = conf['rag_cong']['vertexai_embedding_name'], 
                   retry = conf['rag_cong']['retry'], # if some error happen during  the processing of a group, we save the group label and we retry those labels.
                   max_doc = conf['rag_cong']['max_doc'], #The maximum number of documents(texts chunks) to retrieve as context
                   chunk_size = conf['rag_cong']['chunk_size'],  #The chunk size
                   chunk_overlap = conf['rag_cong']['chunk_overlap'] 
                  )

strike.retrieve_infos_with_retry(dataframe=rag_dataset_df)


#Save the result
current_date = datetime.now().strftime('%Y-%m-%d')
fname = f"strike_results_{current_date}.json"
write_dataiku_json(folder_name = "rag_output", file_name = fname, json_data = strike.all_results)

write_logger_file(logger_folder_name = 'strike_rag_log', log_file_name = strike.logfile_path, final_log_name="strike_rag_log.log")

```

### Matching <a name="matching_process"></a>

After **RAG**,the processed articles are match with the suppliers dataset. This maching allow as to atteste that our sulier are impacted by a given event (e.g. strike in this enxemple). We have differente lavels of matching.
* level 1 : Only company names are matched without locations. 
* level 2 : The companies names and countries, where the strike is takeing place, are matchedw
* level 3 : The companies names, countries and cities are matched

This matching level allow attesting if a plant in given location will potentially be affected.

```py

import dataiku
import pandas as pd, numpy as np
from media.src.matching.matching import Matching
from datetime import datetime
import json 
from io import StringIO
from media.src.utils.utils import read_dataiku_json
from media.src.utils.utils import write_dataiku_json
from media.src.utils.utils import write_logger_file


# Read recipe inputs
current_date = datetime.now().strftime('%Y-%m-%d')
file_path =  f"strike_results_{current_date}.json"
    
rag_json_oupout = read_dataiku_json(folder_name = "rag_output", file_name = file_path)

suppliers = dataiku.Dataset("suppliers")
suppliers_df = suppliers.get_dataframe()



matching =  Matching()
r = matching.match(set_news = rag_json_oupout, dataframe=suppliers_df)

matching_result_path = f"matching_strike_results_{current_date}.json"


# Write recipe outputs
write_dataiku_json(folder_name = "matching_output", file_name = matching_result_path, json_data = matching.results)
write_logger_file(logger_folder_name = 'strike_matching_log', log_file_name = matching.logfile_path, final_log_name="strike_matching_log.log")

```

### Filtering 

After matching, we filter out the relevant articles. We match first because, detected a company as a supplier is take into account when article is classifier as relevent or not.
Also, during this filtering, use a function which classifier an article as relevant or not. This function take an article wich is a dictionary processed by the **RAG**(for retrieving information) and match with our supplier database. So if a new event like for exemple **fire plant** is treated, one will provide a fucntion that allow classifying a processed news(processed by RAG and matched) as relevant or not. 

```py

import dataiku
import pandas as pd, numpy as np
from media.src.filtering.filtering import Filter
import json
from io import StringIO
from datetime import datetime
from media.src.decision_functions.strike_relevancy import strike_relevancy
from media.src.utils.utils import read_dataiku_json, write_dataiku_json
from media.src.utils.utils import write_logger_file

# Read recipe inputs
config_file_path =  'final_config_file.json'
conf = read_dataiku_json(folder_name = "configuration_files" , file_name = 'final_config_file.json')

current_date = datetime.now().strftime('%Y-%m-%d')
file_path =   f"matching_strike_results_{current_date}.json"
matching_json_oupout = read_dataiku_json(folder_name = "matching_output" , file_name = file_path)

#Filter relevent news
filtre = Filter(empty_companie_name_index=[], decision_function= strike_relevancy, decision_function_args=conf["decision_function_args"], filename=None)
relevant, irrelevant = filtre.filtering( matching_json_oupout)

#Save the result
filtered_result_path = f"filter_strike_results_{current_date}.json"
write_dataiku_json(folder_name = "filtering_output", file_name = filtered_result_path, json_data = relevant)

write_logger_file(logger_folder_name = 'strike_filtering_log', log_file_name = filtre.logfile_path, final_log_name= "strike_filtering_log.log")

```


## Groupping and Geographical coordonnates integration

After Filtering out the relevant news, it can happened that we have a company name twice because we failed to group them during **clustering**. We make a little processing which allow grouping the news. Given that there have been classifier as relevant and there are related to the same event(e.g. **strike** in this exemple), we do not fear grouping articles by mistake.

Also we generate geographical cordonate for each city of each relevant news. For that we use **geopy** librairy. 

```py

import dataiku
import pandas as pd
import numpy as np
from media.src.utils.utils import read_dataiku_json
from media.src.utils.utils import write_dataiku_json
from media.src.utils.utils import groupByName
from media.src.utils.utils import geoloc
from datetime import datetime


current_date = datetime.now().strftime('%Y-%m-%d')

# Read recipe inputs

filtered_result_path = f"filter_strike_results_{current_date}.json"
filtered_results = read_dataiku_json(folder_name = "filtering_output" , file_name = filtered_result_path)

if len(filtered_results) != 0:
    #Groupping news base on the detected companie name 
    groupped_results = groupByName(filtered_results)

    # Adding cities greographical coordonates for the relevant articles
    final_results = geoloc(groupped_results)
else :
    final_results= []
    
# Write recipe outputs
grouping_output = dataiku.Folder("grouping_output")
groupped_result_path = f"groupped_result_{current_date}.json"
write_dataiku_json(folder_name = "grouping_output", file_name = groupped_result_path, json_data = final_results)

```

### Summarization

After groupping relevant articles, we generate a short description for detected relevant news. 
given that we do not have the text for each article after processing them with **RAG** techniques, one have to get the text of each relevant articles in order to propose a summary. Also, the relevant articles are grouped either but clustering or by the custom grouping technique we designed. So we have tho all those goupped articles and then propose a summary of the group. We the the text base on the urls. The text of those article are in **rag_data**. 

```py
import dataiku
import pandas as pd, numpy as np
from media.src.summarization.summarizer import Summarizer
from media.src.utils.utils import get_api_key
from media.src.utils.utils import read_dataiku_json
from media.src.utils.utils import write_dataiku_json
from datetime import datetime
from media.src.utils.utils import write_logger_file




current_date = datetime.now().strftime("%Y-%m-%d")
GOOGLE_API_KEY =get_api_key("GOOGLE_API_KEY")


# Read recipe inputs

summarizer = Summarizer(google_api_key = GOOGLE_API_KEY, max_output_tokens = 50)

# Get the dataset use as input for RAG, the texts to summarize are within
rag_dataset = dataiku.Dataset("fire_rag_data")
rag_data = rag_dataset.get_dataframe()

grouped_result_path = f"fire_groupped_result_{current_date}.json"
grouped_json_data = read_dataiku_json(folder_name = "fire_grouping_ouput", file_name = grouped_result_path)

if len(grouped_json_data) !=0: # Generate summarization only if there are some relevant news.
    results = summarizer.genearate_description(json_data=grouped_json_data, dataframe=rag_data)
else:
    results = []
# Write recipe outputs

result_path =f"fire_final_results_{current_date}.json"
write_dataiku_json(folder_name ="fire_final_results", file_name =result_path, json_data= results)

write_logger_file(logger_folder_name = 'fire_summarizer_log', log_file_name = summarizer.logfile_path, final_log_name="fire_summarizer_log.log")

```


This is an exemple of final results :

![image-7.png](attachment:image-7.png)
