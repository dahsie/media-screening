from langchain_google_genai import GoogleGenerativeAI


def generate(google_api_key: str, articles : list[list[str]], max_output_tokens=70, model_name: str = 'gemini-1.5-flash'):
    """
    Generates concise summaries for a list of articles using a generative model.

    Args:
    -----------
    articles : list[list[str]]
        A list of lists, where each inner list contains strings representing the content of an article.
    max_output_tokens : int, optional
        The maximum number of tokens for the generated summary, by default 70.

    Returns:
    --------
    str
        A final summarized text combining the summaries of all articles.
    """
    
    # model = GenerativeModel("gemini-1.5-flash-001")
    model = GenerativeAI(model=model_name, temperature=0.0, google_api_key = google_api_key)
    
    generation_config = {
        "max_output_tokens": max_output_tokens,
        "temperature": 0.0,
        "top_p": 0.8,
    }

    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    }
    
    final = []
    
    def generate_content(texts):
        texts_ = ""
        for text in texts:
            texts_ += text
        text = f"""Provide a very consise summary of the following text:{texts_}. The summary tokens must be below or equal to {max_output_tokens} tokens."""
        # text = f"""Provide a very consise summary of the following text:{texts_}. The summary tokens must be below or equal to {max_output_tokens} tokens. The last token must be a dot."""
        
        results = model.generate_content(
          [text], # A single text and not a list of texts
          generation_config=generation_config,
          safety_settings=safety_settings,
          stream=False
        )
        
        return results.candidates[0].content.parts[0].text
    
    for index, item in tqdm(enumerate(articles)):
        # print(index)
        results = generate_content(item)
        final.append(results)
    if len(final) >= 2 :
        print("final summarization ...")
        results = generate_content(final)

    return results    


def generate_description(json_data: list[dict], dataframe: pd.DataFrame, max_output_tokens: int = 100, col_to_summarize: str = 'translated_text') -> list[dict]:

    """
    Generates descriptions for articles marked as relevant in the JSON data by summarizing the texts associated with their corresponding URLs in a DataFrame.

    Args:
        json_data (list[dict]): A list of dictionaries representing the JSON data, where each dictionary contains information about articles, including their relevance.
        dataframe (pd.DataFrame): A Pandas DataFrame containing articles, where each row represents an article and each column contains information about the article.
        max_output_tokens (int, optional): The maximum number of tokens to use for generating the summary. Default is 100 tokens.
        col_to_summarize (str, optional): The name of the DataFrame column to summarize for relevant articles. Default is 'translated_text'.

    Returns:
        list[dict]: The updated JSON data with descriptions added for relevant articles.
    """
    relevant = []
    irrelevant = []

    for index, item in enumerate(json_data):
        
        urls = []
        if item['relevant'] == 'yes':
            print('yes')
            urls += item['sources']
            if 'sub_articles' in item.keys():
                for sub in item['sub_articles']:
                    urls += sub['sources'] if len(sub) != 0 else []
                    
            df = dataframe.loc[dataframe['url'].isin(urls), :]

            data_ = list(df[col_to_summarize])

            splits = split_liste(data_, limit=500000)
            result = generate(splits, max_output_tokens=max_output_tokens)
            
            item['description'] = result
                    
            relevant.append(item)

        else:
            irrelevant.append(item)
    
    results = relevant + irrelevant  
    return results



