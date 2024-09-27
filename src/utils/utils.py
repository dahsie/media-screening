import logging
import pandas as pd
from tqdm import tqdm
from geopy.geocoders import Nominatim
import dataiku
from io import StringIO
import json
import sys
import os


def create_logger(name: str, file_name: str):
    """
    Creates a logger with a specified name and configures it to log messages to a file.
    Ensures handlers are not duplicated.

    Args:
        name (str): The name of the logger.
        file_name (str): The name of the file where the log messages will be saved.

    Returns:
        logging.Logger: The configured logger instance.
        str: The path to the log file.
    """
    logger = logging.getLogger(name)

    # Reset existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] -- [%(funcName)s()] : %(message)s')

    # Create a file handler
    file_handler = logging.FileHandler(file_name, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger, file_handler.baseFilename

def copy_log_file(source_file: str, destination_file: str) -> None:
    """
    Copies the contents of the source log file to the destination log file without erasing its current content.

    Args:
        source_file (str): The path to the source log file.
        destination_file (str): The path to the destination log file.

    Returns:
        None
    """
    with open(source_file, 'r') as src:
        content = src.read()  # Read the entire content of the source file
    
    with open(destination_file, 'a') as dest:  # Open in append mode
        dest.write(content)  # Append the content to the destination file

def write_logger_file(logger_folder_name: str, log_file_name: str, final_log_name: str) -> None:
    """
    Uploads a log file to a specified folder in Dataiku.

    This function opens a log file and uploads its content to a folder in Dataiku.
    The log file is uploaded using its base file name (without the full path).

    Args:
        logger_folder_name (str): The identifier of the Dataiku managed folder where the log file will be uploaded.
        log_file_name (str): The full path to the log file that will be uploaded.

    Returns:
        None: This function does not return any value.
    """
    log_folder = dataiku.Folder(logger_folder_name)
    
    with open(log_file_name, "r") as file:
        #log_file = os.path.basename(log_file_name)
        log_folder.upload_stream(final_log_name, file.read().encode('utf-8'))
        
#def create_logger(name, file_name : str):
#    """
#    Creates a logger with a specified name and configures it to log messages to a file.
#
#    Args:
#        name (str): The name of the logger.
#        file_name (str): The name of the file where the log messages will be saved.
#
#    Returns:
#        logging.Logger: The configured logger instance.
#    """
#    logger = logging.getLogger(name)
#    logger.setLevel(logging.INFO)

#    # Create a file handle
#    file_handler = logging.FileHandler(file_name)
#    file_handler.setLevel(logging.INFO)
#
#    # Create a formatter and set it for the handler
#    formatter = logging.Formatter('%(asctime)s [%(levelname)s] -- [%(funcName)s()] : %(message)s')
#    file_handler.setFormatter(formatter)
#
#    # Add the file handler to the logger
#    logger.addHandler(file_handler)
#    
#    return logger
    
logger, logfile_path = create_logger(__name__, 'utils.log')


def get_global_variables() :
    """
    Retrieves the global variables of the default project in Dataiku.

    This function uses the Dataiku API to connect to the client, get the default project, and obtain the associated global variables.

    Returns:
        dict: A dictionary containing the project's global variables.
    """
    client = dataiku.api_client()
    project = client.get_default_project()
    var_intern = project.get_variables()

    return var_intern

def read_dataiku_json(folder_name: str, file_name: str) -> dict:
    """
    Reads a JSON file from a Dataiku folder.

    Parameters:
        folder_name (str): The name of the Dataiku folder containing the file.
        file_name (str): The name of the JSON file to be read. Must end with '.json'.

    Returns:
        dict: The parsed JSON data as a Python dictionary.

    Raises:
        ValueError: If the provided file is not a JSON file.

    Note:
        This function reads a JSON file from a Dataiku folder, checks if the file extension is '.json',
        and returns the content as a dictionary. If the file extension is incorrect, it raises a ValueError.
    """
    
    if not file_name.endswith('.json') :
        logger.error(f"The file {file_name} to read is not a JSON file. Only JSON files can be read with this function.")
        raise ValueError("The file {file_name} to read is not a JSON file. Only JSON files can be read with this function.")
        
    folder = dataiku.Folder(folder_name)  
    with folder.get_download_stream(file_name) as file :
        file_ = file.read()
        #my_json =config.decode('utf8').replace("'", '"')
        my_json =file_.decode('utf8')
        json_data = json.loads(my_json)
    return json_data


def write_dataiku_json(folder_name: str, file_name: str, json_data: dict) -> None:
    """
    Writes a Python dictionary as a JSON file to a Dataiku folder.

    Parameters:
        folder_name (str): The name of the Dataiku folder where the file will be written.
        file_name (str): The name of the file to write. Must end with '.json'.
        json_data (dict): The dictionary data to be saved as JSON.

    Raises:
        ValueError: If the provided file is not a JSON file.

    Note:
        This function serializes a Python dictionary to a JSON file and uploads it to a Dataiku folder.
        If the file extension is not '.json', it raises a ValueError.
    """
    if not file_name.endswith('.json') :
        logger.error(f"The file {file_name} to write is not a JSON file. Only JSON files can be written with this function.")
        raise ValueError("The file {file_name} to write is not a JSON file. Only JSON files can be written with this function.")
        
    folder  = dataiku.Folder(folder_name)
    folder.upload_stream(file_name, StringIO(json.dumps(json_data, indent = 4)))

def display(x: list, y: list, ax, label: str, xlabel : str, ylabel: str, title = None) :
    """
    Plots data on a given axis and customizes the plot's labels and title.

    Args:
        x (list): The x-axis data.
        y (list): The y-axis data.
        ax: The axis on which to plot the data.
        label (str): The label for the plot.
        xlabel (str): The label for the x-axis.
        ylabel (str): The label for the y-axis.
        title (str, optional): The title of the plot. Defaults to None.

    Returns:
        None
    """
    ax.plot(x, y, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    if title is not None:
        ax.set_title(title)

def split_liste(texts : list[str], limit : int , separators: list[str] = ['.', '!', '?', '\n', '\n\n'])-> list[list[str]]:
    """
    Splits a list of texts into sub-lists based on a token limit, using specified separators.

    Args:
        texts (list[str]): The texts to split.
        limit (int): The token limit for each sub-list.
        separators (list[str], optional): The list of separators to use for splitting the texts. Defaults to ['.', '!', '?', '\n', '\n\n'].

    Returns:
        list[list[str]]: A list of sub-lists containing the split texts.

    Raises:
        ValueError: If a single text exceeds the token limit after splitting.
    """
    # logger.info("Splitting texts into sub-lists with a limit of %d tokens", limit)

    sub_list = []
    liste = []
    cpt = 0
    for text in texts :

        length_text = len(text)

        if length_text > limit :
            pos = limit

            while pos > 0 and text[pos] not in separators:
                pos -= 1
            pos += 1 #One include the ponctuation sign within the sub-string
            text = text[:pos]
            length_text = len(text)
            logger.warning(f"The text has {length_text} tokens, which exceeds the limit of {limit} tokens. It is troncated to {len(text)} token")

        # else :
        cpt += length_text

        if cpt < limit:
            sub_list.append(text)

        else :
            liste.append(sub_list)
            cpt, sub_list = length_text, []
            sub_list.append(text)

    liste.append(sub_list)
    logger.info("Texts successfully split into sub-lists.")
    return liste
    
    
    
def groupByName(json_data : list[dict])-> list[dict]:
    """
    Groups articles by impacted company and core company names, identifying duplicates and associating them as sub-articles.

    args:
    ----
    json_data : list[dict]
        A list of dictionaries containing article data. Each dictionary should have the keys 'impacted_company' and 'core_company'.

    Returns:
    --------
    list[dict]
        A list of dictionaries where each dictionary represents an article with sub-articles grouped under the 'sub_articles' key.
    """
    
    for i in  range(len(json_data)):
        json_data[i]['duplicated'] = "no"
    liste = []

    for i in  range(len(json_data) -1):

        sub_list = []

        if len(json_data[i]['impacted_company']) != 0:

            name = json_data[i]['impacted_company']
            core_name = json_data[i]['core_company']
            relevant = json_data[i]['relevant']


            for j  in range(i+1, len(json_data)):

                if len(json_data[j]['impacted_company']) != 0 :
                    name1 = json_data[j]['impacted_company']
                    core_name1 = json_data[j]['core_company']
                    relevant1 = json_data[j]['relevant']

                    if (name1.lower().strip() == name.lower().strip() or core_name1.lower().strip() == core_name.lower().strip()) and json_data[j]['duplicated'] == "no" and relevant == relevant1:

                        json_data[j]['duplicated'] = "yes"
                        sub_list.append(json_data[j])

        if len(sub_list) !=0 :
            json_data[i]['sub_articles'] = sub_list
            liste.append(json_data[i])
        elif  len(sub_list) ==0 and json_data[i]['duplicated'] == "no": 
            json_data[i]['sub_articles'] = []
            liste.append(json_data[i])
        elif len(json_data[i]['impacted_company']) == 0 :
            json_data[i]['sub_articles'] = []
            liste.append(json_data[i])
    if json_data[len(json_data) -1]['duplicated'] == "no" :
        json_data[len(json_data) -1]['sub_articles'] = []
        liste.append(json_data[len(json_data) -1])
    return liste   



# def generate(articles : list[list[str]], max_output_tokens=70):
#     """
#     Generates concise summaries for a list of articles using a generative model.

#     Args:
#     -----------
#     articles : list[list[str]]
#         A list of lists, where each inner list contains strings representing the content of an article.
#     max_output_tokens : int, optional
#         The maximum number of tokens for the generated summary, by default 70.

#     Returns:
#     --------
#     str
#         A final summarized text combining the summaries of all articles.
#     """
#     vertexai.init(project="irn-67050-lab-65", location="europe-west4")
#     model = GenerativeModel("gemini-1.5-flash-001")
    
#     generation_config = {
#         "max_output_tokens": max_output_tokens,
#         "temperature": 0.0,
#         "top_p": 0.8,
#     }

#     safety_settings = {
#         generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
#         generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
#         generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
#         generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
#     }
    
#     final = []
    
#     def generate_content(texts):
#         texts_ = ""
#         for text in texts:
#             texts_ += text
#         text = f"""Provide a very consise summary of the following text:{texts_}. The summary tokens must be below or equal to {max_output_tokens} tokens. The last token must be a dot."""
        
#         results = model.generate_content(
#           [text], # A single text and not a list of texts
#           generation_config=generation_config,
#           safety_settings=safety_settings,
#           stream=False
#         )
        
#         return results.candidates[0].content.parts[0].text
    
#     for index, item in tqdm(enumerate(articles)):
#         # print(index)
#         results = generate_content(item)
#         final.append(results)
#     if len(final) >= 2 :
#         print("final summarization ...")
#         results = generate_content(final)

#     return results    


# def generate_description(json_data: list[dict], dataframe: pd.DataFrame, max_output_tokens: int = 100, col_to_summarize: str = 'translated_text') -> list[dict]:

#     """
#     Generates descriptions for articles marked as relevant in the JSON data by summarizing the texts associated with their corresponding URLs in a DataFrame.

#     Args:
#         json_data (list[dict]): A list of dictionaries representing the JSON data, where each dictionary contains information about articles, including their relevance.
#         dataframe (pd.DataFrame): A Pandas DataFrame containing articles, where each row represents an article and each column contains information about the article.
#         max_output_tokens (int, optional): The maximum number of tokens to use for generating the summary. Default is 100 tokens.
#         col_to_summarize (str, optional): The name of the DataFrame column to summarize for relevant articles. Default is 'translated_text'.

#     Returns:
#         list[dict]: The updated JSON data with descriptions added for relevant articles.
#     """
#     relevant = []
#     irrelevant = []

#     for index, item in enumerate(json_data):
        
#         urls = []
#         if item['relevant'] == 'yes':
#             print('yes')
#             urls += item['sources']
#             if 'sub_articles' in item.keys():
#                 for sub in item['sub_articles']:
#                     urls += sub['sources'] if len(sub) != 0 else []
                    
#             df = dataframe.loc[dataframe['url'].isin(urls), :]

#             data_ = list(df[col_to_summarize])

#             splits = split_liste(data_, limit=500000)
#             result = generate(splits, max_output_tokens=max_output_tokens)
            
#             item['description'] = result
                    
#             relevant.append(item)

#         else:
#             irrelevant.append(item)
    
#     results = relevant + irrelevant  
#     return results


def geoloc(json_data: list[dict]) -> list[dict]:
    """
    Adds geographical coordinates (latitude and longitude) to locations in relevant articles in the JSON data.

    Args:
        json_data (list[dict]): A list of dictionaries representing the JSON data, where each dictionary contains information about articles, including locations.

    Returns:
        list[dict]: The updated JSON data with geographical coordinates added to locations in relevant articles.
    """
    geolocator = Nominatim(user_agent='Entreprise')

    for index, item in enumerate(json_data):
        if item['relevant'] == 'yes':
            for index2, location in enumerate(item['locations']):
                if isinstance(location, dict) and location['city'] != '':
                    loc = geolocator.geocode(location['city'])
                    if loc is None or loc == '':
                        continue
                    json_data[index]['locations'][index2]['latitude'] = loc.latitude
                    json_data[index]['locations'][index2]['longitude'] = loc.longitude         

    return json_data


def get_api_key(name:str)->str:
    """
    This function allow to get the API keys that are stocked in personnal secrets
    """
    
    client = dataiku.api_client()
    auth_info = client.get_auth_info(with_secrets=True)

    # retrieve the secret named "credential-for-my-api"
    secret_value = None
    for secret in auth_info["secrets"]:
        if secret["key"] == name:
                secret_value = secret["value"]
                break
                    
    return secret_value
