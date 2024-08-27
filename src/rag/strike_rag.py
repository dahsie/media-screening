
import sys
import os


sys.path.append("../src/outpout_parsers")
sys.path.append("../src/prompts")
sys.path.append("../src/questions")

from base_retrieval import *
from output_parsers import *
import strike_rag_prompts
import strike_rag_questions

class StrikeRAG(RetrivalBase):
    """
    StrikeRAG is a class designed to identify and analyze strikes in the automotive industry using a Retrieval-Augmented Generation (RAG) approach. It extends the RetrievalBase class and leverages various prompt templates and parsers to gather and interpret information related to labor strikes affecting companies, business sectors, and the automotive industry.

    ---------------------------------------------------------------------------------
    Attributes:
        auto_parser (JsonOutputParser): A parser for the automotive sector.
        parser_business_sectors (JsonOutputParser): A parser for business sectors.
        parser_companies_names (JsonOutputParser): A parser for company names.
        tmp_parser (JsonOutputParser): A parser for temporal data related to strikes.
        labor_strike_parser (JsonOutputParser): A parser for labor strike information.
        prompt1 (PromptTemplate): Template for identifying companies experiencing strikes.
        prompt2 (PromptTemplate): Template for finding main sectors of a company.
        prompt3 (PromptTemplate): Template for analyzing the impact of strikes on the car-making industry.
        prompt4 (PromptTemplate): Template for analyzing the temporality of strikes.
        prompt5 (PromptTemplate): Template for determining if a strike is a labor strike.
        keys_order (list): The order of keys in the results dictionary.

    ---------------------------------------------------------------------------------
    Methods:
        __init__(vertexai_llm, vertexai_embedding_name, retry, max_doc, chunk_size, chunk_overlap):
            Initializes the StrikeRAG class with specified parameters.

        retrieve_infos(dataframe):
            Retrieves and processes information about strikes from a given dataframe.
    """
    
    keys_order = ['strike', 'impacted_company','locations', 'impacted_business_sectors','automotive_industry', 'temporality','description', 'sources']
    
    
    def __init__(self, vertexai_llm='gemini-1.5-flash',
                 vertexai_embedding_name = 'text-embedding-004',
                 retry :int= 2, max_doc : int = 5, chunk_size = 2000,chunk_overlap=10):
        
        super(StrikeRAG, self).__init__(vertexai_llm=vertexai_llm,
                vertexai_embedding_name = vertexai_embedding_name,
                retry = retry, max_doc = max_doc, chunk_size = chunk_size, chunk_overlap=chunk_overlap)
        #Prompts
        self.prompt1, self.prompt2, self.prompt3 = strike_rag_prompts.prompt1, strike_rag_prompts.prompt2, strike_rag_prompts.prompt3
        self.prompt4, self.prompt5 =  strike_rag_prompts.prompt4, strike_rag_prompts.prompt5
        
        #output parsers
        self.auto_parser = JsonOutputParser(pydantic_object = AutomotiveSector)
        self.parser_business_sectors = JsonOutputParser(pydantic_object = BusinessSectors)
        self.parser_companies_names = JsonOutputParser(pydantic_object = Company)
        self.tmp_parser = JsonOutputParser(pydantic_object = Temporality)
        self.labor_strike_parser = JsonOutputParser(pydantic_object = LaborStrike)
        
        #Chains 
        self.__chain1 = (self.prompt1 | self.llm)
        self.__chain3 = (self.prompt3 | self.llm)
        self.__paralle_chain = RunnableParallel(response2= (self.prompt2 | self.llm) ,response4 = (self.prompt4 | self.llm), response5 = (self.prompt5 | self.llm) )
        
        # Retrivers
        self.__paralle_retrieve = RunnableParallel(context2 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query2'])),
                                                context4 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query4'])),
                                                context5 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query5'])) )
        self._retriever = None
        
        #Questions
        self.__query1 , self.__query2, self.__query3 = strike_rag_questions.query1, strike_rag_questions.query2, strike_rag_questions.query3
        self.__query4, self.__query5 = strike_rag_questions.query4, strike_rag_questions.query5
        
    def retrieve_infos(self, dataframe) :
        """
        Initializes the StrikeRAG instance with specified parameters.

        Args:
            vertexai_llm (str): The name of the language model to use.
            vertexai_embedding_name (str): The name of the embedding model to use.
            retry (int): The number of retries for operations.
            max_doc (int): The maximum number of documents to retrieve.
            chunk_size (int): The size of each document chunk.
            chunk_overlap (int): The overlap between document chunks.
        """
        fail = []
        results = []
        self.number_token = len(self.prompt1.template)+len(self.prompt2.template)+len(self.prompt3.template) + len(self.prompt4.template) + len(self.prompt5.template)
        for index, label in enumerate(np.unique(dataframe['class'])):
            result = dict()
            
            print(f"label : {label}")
            
            retrieve = True # The variable indicating if yes or no some documents should be retieve for a given query. At the begining it should ne True because we are complete to retrieve document at the beginning of the processing
                            # But for the remaining questions it will depend of the maximumun  number of documents in the vectores store. It the maximaum number it under self.max_doc so then no document will be retrieve for the remaining queriesfor a given iteration. 
                    
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
                print(f" str_doc1 is None : {index}")
            if doc_number < self.max_doc :
                retrieve = False # The document should be retrieve for the remaining queries
                
            response1 = self.__chain1.invoke({'context': str_doc1, 'query' : self.__query1})
            
           
            if response1 == '' :
                fail.append(label)
                print('response1 is empty')
                continue # The need to get response for the remaining queries because we do not find the company name which is impacted but the strike
            try:
               
                response1 = self.parser_companies_names.parse(response1)
                company = response1['company']
              
                if company is None or company.lower() in self.liste :
                    print('company is None or belongs to self.liste')
                    continue # N need to continue
    
                result['impacted_company'] = company
                result['locations'] = response1['locations']
                
                query2 = self.__query2.format(company = company)
                query4 = self.__query4.format(company = company)
                query5 = self.__query5.format(company = company)
                
            except Exception as e :
                print(f" error parsing response1 {e}")
            
           
            
            if retrieve == True :
                
                input_retrieve = {'query2' : query2, 'query4' : query4, 'query5':query5}

                r = self.__paralle_retrieve.invoke(input_retrieve)
               
                source2, _ ,str_doc2 = r['context2']
                source4, published_date4 ,str_doc4 = r['context4']
                source5, _, str_doc5 = r['context5']
                sources = sources + source2 + source4 + source5
                print('second retrieval')
            else :
                str_doc2, str_doc4, str_doc3, str_doc5 = str_doc1, str_doc1, str_doc1, str_doc1
                published_date4 = published_date1
                retrieve = False
                print('no second retrieval')
           
            query4 = query4 + f" Keep in mind that the published dates of the current strike are  : {published_date4} and today is :{date.today().strftime('%Y-%m-%d')} ."
            input_chain = {'context2':str_doc2, 'context4':str_doc4 , 'query2' : query2, 'query4' : query4, 'context5':str_doc5 , 'query5' : query5}
            final = self.__paralle_chain.invoke(input_chain)
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
                                         
            if final['response4'] != '':
                
                try :
                    response4 = self.tmp_parser.parse(final['response4'])
                    result["temporality"] = response4
                except Exception as e :
                    print(f" error parsing response4 : {e}")
                    result["temporality"] = {"strike_status" : "unknown", "justification" : ""}
            else :
                result["temporality"] = {"strike_status" : "unknown", "justification" : ""}
                
            if final['response5'] != '':
                
                try :
                    response5 = self.labor_strike_parser.parse(final['response5'])
                    result["strike"] = response5
                except Exception as e :
                    print(f" error parsing response4 : {e}")
                    result["strike"] = {"labor_strike": "no", "justification":""}
            else:
                result["strike"] = {"labor_strike": "no", "justification":""}
                
            
            if retrieve == True :
                source3, _ ,str_doc3 = self._retrieve(query3)
                sources += source3
                print('3rd retrieval')
            
            response3 = self.__chain3.invoke({'context' : str_doc3, 'query' : query3})
            
            if response3 !='':
                try :
                    response3 = self.auto_parser.parse(response3)
                    result["automotive_industry"] = response3
                    
        
                except Exception as e :
                    print(f" error parsing response3 : {e}")
                    result["automotive_industry"] = {'concerned' : 'unknow', 'justification' : ""}
            else : 
                result["automotive_industry"] = {'concerned' : 'unknow', 'justification' : ""}

           
            result['sources'] = list(set(sources))
            
            vectores.delete([vectores.index_to_docstore_id[i] for i in range(vectores.index.ntotal)]) # FAISS

            tmp_result = {key: result[key] for key in self.keys_order if key in list(result.keys())}
            
            results.append(tmp_result)
            
            print("results :")
            print(tmp_result)
            print('-'*100)
            
            self.number_token = self.number_token + len(self.__query1) + len(query2) + len(query3) + len(query4) + len(query5)
            self.number_token = self.number_token + len(str_doc1) + len(str_doc2) + len(str_doc3) + len(str_doc4) + len(str_doc5)

        self.results = results
        self.failed_labels = fail
