import sys
import os

from media.src.rag.base_retrieval import *
from media.src.output_parsers.output_parsers import *


from media.src.prompts import fire_rag_prompts
from media.src.questions import fire_rag_questions


class FireRAG(RetrivalBase):
    
    """
    FireRAG is a specialized retrieval and analysis class designed to process information related to fires at manufacturing plants.
    It uses various prompts and parsers to extract information about impacted companies, business sectors, and the automotive industry.

    ---------------------------------------------------------------------------------
    Attributes:
        auto_parser (JsonOutputParser): Parser for automotive sector information.
        parser_business_sectors (JsonOutputParser): Parser for business sectors information.
        parser_companies_names (JsonOutputParser): Parser for company names.
        fire_plant_parser (JsonOutputParser): Parser for fire plant information.
        
        prompt1 (PromptTemplate): Template to identify companies affected by a fire.
        prompt2 (PromptTemplate): Template to find main sectors of a company.
        prompt3 (PromptTemplate): Template to analyze impact on the car making industry.
        prompt5 (PromptTemplate): Template to determine if a company is a manufacturing company affected by a fire.
        
        keys_order (list): Order of keys for the final result dictionary.
    
    ---------------------------------------------------------------------------------
    Methods:
        __init__(vertexai_llm, vertexai_embedding_name, retry, max_doc, chunk_size, chunk_overlap):
            Initializes the FireRAG instance with the specified parameters and sets up necessary prompts and chains.

        retrieve_infos(dataframe: pd.DataFrame):
            Retrieves and processes information from the given DataFrame with multiple queries and parses the results.
    """

    keys_order = ['fire_plant', 'impacted_company','locations', 'impacted_business_sectors', 'automotive_industry','description', 'sources']
    
    def __init__(self,google_api_key: str, vertexai_llm='gemini-1.5-flash',
                 vertexai_embedding_name ='text-embedding-004',
                 retry :int= 2, max_doc : int = 5, chunk_size: int = 3000, chunk_overlap: int = 10):
        """
        Initializes the FireRAG instance with the specified parameters and sets up necessary prompts and chains.
        
        Args:
            vertexai_llm (str): The language model to use.
            vertexai_embedding_name (str): The embedding model to use.
            retry (int): The number of retry attempts.
            max_doc (int): The maximum number of documents to retrieve.
            chunk_size (int): The size of chunks for document splitting.
            chunk_overlap (int): The overlap between chunks for document splitting.
        """
        
        super(FireRAG, self).__init__(google_api_key = google_api_key, vertexai_llm=vertexai_llm,
                 vertexai_embedding_name = vertexai_embedding_name,
                 retry = retry, max_doc = max_doc ,chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        #Prompts
        self.prompt1, self.prompt2, self.prompt3, self.prompt5 = fire_rag_prompts.prompt1, fire_rag_prompts.prompt2, fire_rag_prompts.prompt3, fire_rag_prompts.prompt5
        #Output parsers 
        self.auto_parser = JsonOutputParser(pydantic_object= AutomotiveSector)
        self.parser_business_sectors = JsonOutputParser(pydantic_object=BusinessSectors)
        self.parser_companies_names = JsonOutputParser(pydantic_object=Company)
        self.fire_plant_parser = JsonOutputParser(pydantic_object=FirePlant)
        
        #Chains
        self.__chain1 = (self.prompt1 | self.llm)
        self.__chain3 = (self.prompt3 | self.llm)
        self.__paralle_chain = RunnableParallel(response2=(self.prompt2 | self.llm), response5 = (self.prompt5 | self.llm))
        
        self.__paralle_retrieve = RunnableParallel(context2 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query2'])),
                                                context5 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query5'])) )
        self._retriever = None
        
        # Questions
        self.__query1, self.__query2, self.__query3, self.__query5 = fire_rag_questions.query1, fire_rag_questions.query2, fire_rag_questions.query3, fire_rag_questions.query5
        
    def retrieve_infos(self, dataframe) :
        """
        Retrieves and processes information from the given DataFrame with multiple queries and parses the results.
        
        Args:
            dataframe (pd.DataFrame): The DataFrame containing the information to be retrieved.
        """
        fail = []
        results = []

        self.number_token = len(self.prompt1.template)+len(self.prompt2.template)+len(self.prompt3.template) + len(self.prompt5.template)
        for index, label in enumerate(np.unique(dataframe['class'])):
            result = dict()

            print(f"label : {label}")

            retrieve = True # The variable indicating if yes or no some documents should be retieve for a given query. At the begining it should ne True because we are complete to retrieve document at the beginning of the processing
                            # But for the remaining questions it will depend of the maximumun  number of documents in the vectores store. It the maximaum number it under self.max_doc so then no document will be retrieve for the remaining queries
                            # for a given iteration. 

            ## Create a RAG database
            print(f" document creation : {index}")
            data_cat = dataframe.loc[dataframe['class']==label, :]
            docs = self._get_documents_from_dataframe(data_cat,chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
            vectores = self._create_db(docs)
            doc_number =  min(self.max_doc, vectores.index.ntotal) # FAISS
            self._retriever = vectores.as_retriever(search_kwargs={'k': doc_number})


            print("first retrieval")

            sources, published_date1,str_doc1 = self._retrieve(self.__query1)

            if str_doc1 is None :
                continue # No ducument are retrieve for the first query so there is no need to continue, we must pass to the next iteration

            if doc_number < self.max_doc :
                retrieve = False # The document should be retrieve for the remaining queries

            response1 = self.__chain1.invoke({'context': str_doc1, 'query' : self.__query1})

            if response1 == '' :
                fail.append(label)
                continue # The need to get response for the remaining queries because we do not find the company name which is impacted but the fire at factory
            try:
                response1 = self.parser_companies_names.parse(response1)
                company = response1['company']

                if company is None or company.lower() in self.liste :
                    continue # N need to continue

                result['impacted_company'] = company
                result['locations'] = response1['locations']

                query2 = self.__query2.format(company = company)
                query5 = self.__query5.format(company = company)


            except Exception as e :
                print(f" error parsing response1 {e}")

            if retrieve == True :

                input_retrieve = {'query2' : query2, 'query5':query5}

                r = self.__paralle_retrieve.invoke(input_retrieve)

                source2, _ ,str_doc2 = r['context2']
                source5, _, str_doc5 = r['context5']
                sources = sources + source2 + source5

                print('second retrieval')

            else :
                str_doc2, str_doc3, str_doc5 = str_doc1, str_doc1, str_doc1
                retrieve = False
                print('no second retrieval')



            input_chain = {'context2':str_doc2, 'company2':company , 'query2' : query2,'context5':str_doc5 , 'company5':company, 'query5' : query5}
            final= self.__paralle_chain.invoke(input_chain)
            if final['response2'] != '':
                try :
                    response2 = self.parser_business_sectors.parse(final['response2'])

                    result["impacted_business_sectors"] = response2['business_sectors']
                    business_sectors = ", ".join(response2['business_sectors'])

                    query3 = self.__query3.format(company = company, business_sectors = business_sectors)

                except Exception as e :
                    print(f" error parsing response2 : {e}")
                    result["impacted_business_sectors"] = []
            else :
                result["impacted_business_sectors"] = []

            if final['response5'] != '':
                try :
                    response5 = self.fire_plant_parser.parse(final['response5'])
                    result["fire_plant"] = response5

                except Exception as e :
                    print(f" error parsing response4 : {e}")
            else :
                result["fire_plant"] = {'fire_plant': {'fire_plant': 'no', 'justification':''}}

            if retrieve == True :
                source3, _ ,str_doc3 = self._retrieve(query3)
                sources += source3
                print('3rd retrieval')

            response3 = self.__chain3.invoke({'context' : str_doc3, 'company':company , 'query' : query3})

            if response3 !='':
                try :
                    response3 = self.auto_parser.parse(response3)
                    result["automotive_industry"] = response3
                except Exception as e :
                    print(f" error parsing response3 : {e}")
                    result["automotive_industry"] = {'concerned' : 'unknow', 'justification' : 'unknown'}

            else :
                result["automotive_industry"] = {'concerned' : 'unknow', 'justification' : 'unknown'}
            result['sources'] = list(set(sources))

            vectores.delete([vectores.index_to_docstore_id[i] for i in range(vectores.index.ntotal)]) # FAISS

            tmp_result = {key: result[key] for key in self.keys_order if key in list(result.keys())}

            results.append(tmp_result)
            print("results :")
            print(tmp_result)
            print('-'*100)

            self.number_token = self.number_token + len(self.__query1) + len(query2) + len(query3) + len(query5)
            self.number_token = self.number_token + len(str_doc1) + len(str_doc2) + len(str_doc3) + len(str_doc5)
            # print(f" token number : {self.number_token}")

            self.results = results
            self.failed_labels = fail