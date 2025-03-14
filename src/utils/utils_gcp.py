import logging
import pandas as pd
from tqdm import tqdm
from geopy.geocoders import Nominatim
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
    
logger, logfile_path = create_logger(__name__, 'utils.log')

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

def chunk_text(text: str, limit: int, separators: list[str] = ['.', '!', '?', '\n', '\n\n']):
    """ Return the first limit characters"""
    
    length_text, chunk = len(text), text
    if length_text > limit :
        pos = limit
        while pos > 0 and text[pos] not in separators:
            pos -= 1
        pos += 1 #One include the ponctuation sign within the sub-string
        chunk = text[:pos]
    return chunk

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
        
        text = chunk_text(text = text, limit = limit , separators = separators)
        length_text = len(text)
        logger.warning(f"The text has {length_text} tokens, which exceeds the limit of {limit} tokens. It is troncated to {len(text)} token")

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
