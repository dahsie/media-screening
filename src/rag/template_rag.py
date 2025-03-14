
import os


from media.src.rag.base_retrieval import *
from media.src.output_parsers.output_parsers import *


from media.src.prompts import template_prompts
from media.src.questions import template_rag_questions

#from media.src.utils.utils import create_logger

"""
In this exemple we will act like we are treating an event which require to answer 5 questions. Given that we have 5 question we must also 
have 5 prompts in the file 'template_prompts' and 5 questions in the file 'template_rag_questions.py'
Notice that somes question can be treated in parallel. For instance the question2, question4 dans question5 because there independant. 
You can treat as many as question in parallel for the moment that there independant. 

"""
class TemplateRAG(RetrivalBase):
    """
    TemplateRAG is a class designed to identify and analyze a "template event" in the automotive industry using a Retrieval-Augmented Generation (RAG) approach. It extends the RetrievalBase class and leverages various prompt templates and parsers to gather and interpret information related to 'template event' affecting the automotive industry.

    ---------------------------------------------------------------------------------
    Attributes:
        parser1 (JsonOutputParser): add any comment you want 
        parser2 (JsonOutputParser): add any comment you want 
        parser3 (JsonOutputParser): add any comment you want 
        parser4 (JsonOutputParser): add any comment you want 
        parser5 (JsonOutputParser): add any comment you want 
        prompt1 (PromptTemplate): add any comment you want 
        prompt2 (PromptTemplate): add any comment you want 
        prompt3 (PromptTemplate): add any comment you want 
        prompt4 (PromptTemplate): add any comment you want 
        prompt5 (PromptTemplate): add any comment you want 
        keys_order (list): The order of keys in the results dictionary.

    ---------------------------------------------------------------------------------
    Methods:
        __init__(vertexai_llm, vertexai_embedding_name, retry, max_doc, chunk_size, chunk_overlap):
            Initializes the TemplateRAG class with specified parameters.

        retrieve_infos(dataframe):
            Retrieves and processes information about 'template event' from a given dataframe.
    """
    
    #This is the order of keys of an treated articles. 
    keys_order = ['key1', 'key2','key3', 'key4','key5', 'key6','key7', 'keys3', '...', '...']  
    
    # Exemple of keys order in cas on are treating 'strike event'
    # Make sure that these keys are in you pydantic parsers field. 
    # You must change the keys to match your pydantic ouparsers fields.
    keys_order = ['strike', 'impacted_company','locations', 'impacted_business_sectors','automotive_industry', 'temporality','description', 'sources']

    
    
    def __init__(self, google_api_key: str, vertexai_llm='gemini-1.5-flash', # The model name
                 vertexai_embedding_name = 'text-embedding-004',
                 retry :int= 2, max_doc : int = 5, chunk_size = 2000,chunk_overlap=10):
        
        super(TemplateRAG, self).__init__(google_api_key = google_api_key, vertexai_llm=vertexai_llm,
                vertexai_embedding_name = vertexai_embedding_name,
                retry = retry, max_doc = max_doc, chunk_size = chunk_size, chunk_overlap=chunk_overlap)
        #Prompts
        self.prompt1, self.prompt2, self.prompt3 = template_prompts.prompt1, template_prompts.prompt2, template_prompts.prompt3
        self.prompt4, self.prompt5 =  template_prompts.prompt4, template_prompts.prompt5
        
        #output parsers
        self.parser1 = JsonOutputParser(pydantic_object = "add the correct Pydantic parser (e.g. AutomotiveSector)")
        self.parser3 = JsonOutputParser(pydantic_object = "add the correct Pydantic parser (e.g. BusinessSectors)")
        self.parser3 = JsonOutputParser(pydantic_object = "add the correct Pydantic parser (e.g.Company)") 
        self.parser4 = JsonOutputParser(pydantic_object = "add the correct Pydantic parser (e.g. Temporality)")
        self.parser5 = JsonOutputParser(pydantic_object = "add the correct Pydantic parser (e.g. LaborStrike)")        
        
        #Exemple
        #self.parser5 = JsonOutputParser(pydantic_object = LaborStrike)

        
        #Chains 
        self.__chain1 = (self.prompt1 | self.llm)
        self.__chain3 = (self.prompt3 | self.llm)
        self.__paralle_chain = RunnableParallel(response2= (self.prompt2 | self.llm) , #chain2
                                                response4 = (self.prompt4 | self.llm), #chain4
                                                response5 = (self.prompt5 | self.llm) # chain5
                                                #You can add as many as chains that can be run in parallel because the questions are independant"
                                                #response_j = (self.prompt_j | self.llm) # chain_j
                                                #response_(j+i) = (self.prompt_(j+i) | self.llm) # chain_(j+i)
                                                # ...
                                               )
        
        # Retrivers
        self.__paralle_retrieve = RunnableParallel(context2 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query2'])),# retrive document for question 2
                                                context4 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query4'])), # retrive document for question 4
                                                context5 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query5'])) # retrive document for question 5                                                context5 = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query5'])) # retrive document for question 5
                                                #context_j = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query_j'])) # retrive document for question j
                                                #context_(j+i) = RunnableLambda(lambda input_dict: self._retrieve(input_dict['query_(j+i)'])) # retrive document for question (j+i)
                                                  )
        self._retriever = None
        
        #Questions
        self.__query1 , self.__query2, self.__query3 = template_rag_questions.query1, template_rag_questions.query2, template_rag_questions.query3
        self.__query4, self.__query5 = template_rag_questions.query4, template_rag_questions.query5
        
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
        for index, label in enumerate(np.unique(dataframe['class'])): # the dataframe wich contains data for rag must have the column 'class'
            result = dict()
            
            print(f"label : {label}")
            
            retrieve = True # The variable indicating if yes or no some documents should be retieve for a given query. At the begining it should ne True because we are complete to retrieve document at the beginning of the processing
                            # But for the remaining questions it will depend of the maximumun  number of documents in the vectores store. It the maximaum number it under self.max_doc so then no document will be retrieve for the remaining queriesfor a given iteration. 
                    
            ## Create a RAG database
            print(f" document creation : {index}")
            data_cat = dataframe.loc[dataframe['class']==label, :]
            docs = self._get_documents_from_dataframe(data_cat,chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
            vectores = self._create_db(docs)
            doc_number =  min(self.max_doc, vectores.index.ntotal) # we compute the number of docs to retrieve for a given question. If want to retrieve for exemple 5 docs
                                                                    # and we have at the same time only 3 docs in our database, we can not get more than 5 docs so the number of docs to retrieve will be 3.
                                                                    # in this case we have less than the desire number of documents we want to retrieve, we will keep the docs we retrieve for
                                                                    # the remaining questions. This means we will not retrieve other docs for a new question given that we have have already retrieve all docs
                                                                    # if we have more than 5 docs, we will only get 5 docs. In this case, we will retrive new docs for new question because the retrival
                                                                    # docuement can less relevant for the new question. 
            self._retriever = vectores.as_retriever(search_kwargs={'k': doc_number})
            
            print("first retrieval")
            
            sources, published_date1,str_doc1 = self._retrieve(self.__query1) # want the retrieval is made, the sources(urls), dates dans the text are parse separately
            
            if str_doc1 is None : # It mean no doc has been deemed relevant for the first question. in this exemple, the first question allow toidentiy the company name. this company name will be used for the 
                                  # remaining questions so there is no need to try the remaining question. So we will continue the loop with new label.
                continue # No ducument are retrieve for the first query so there is no need to continue, we must pass to the next iteration
                print(f" str_doc1 is None : {index}")
            if doc_number < self.max_doc :
                retrieve = False # The document should be retrieve for the remaining queries
                
            response1 = self.__chain1.invoke({'context': str_doc1, 'query' : self.__query1})
            
           
            if response1 == '' : # no company name has been detected so we will not continue with the remaining questions. The loop will continue with the next 'label'
                fail.append(label)
                print('response1 is empty')
                continue # The need to get response for the remaining queries because we do not find the company name which is impacted but the strike
            try: # to be sure that we do not have any trouble during parsing. For exemple if a response is empty then it can be parsed and we do not want the loop to be stopped beacause of a parsing error. 
               
                # In this exemple, the first question is about determining the company name. 
                response1 = self.parser1.parse(response1)
                company = response1['company']
              
                if company is None or company.lower() in self.liste :
                    print('company is None or belongs to self.liste')
                    continue # N need to continue
    
                result['impacted_company'] = company
                result['locations'] = response1['locations']
                
                #The three questions which shoud be processed in parallel need to be completed by the the company name.
                #If there is nothing to be complete a further questions , there is need to write the bellow three lines.
                query2 = self.__query2.format(company = company)
                query4 = self.__query4.format(company = company)
                query5 = self.__query5.format(company = company)
                
            except Exception as e :
                print(f" error parsing response1 {e}")
            
           
            
            if retrieve == True :
                
                input_retrieve = {'query2' : query2, 'query4' : query4, 'query5':query5} # The retrieve in parallel make sure that you have differents queries in "input_retrieve" dict (e.g quiry1, quiry2, ...)

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
           
            
            
            #feel free to add any information in the query to be sure that it is clear enough for the model. But be careful if not you loose some important informations if you are too more specific
            
            #query4 = query4 + f" Keep in mind that the published dates of the current strike are  : {published_date4} and today is :{date.today().strftime('%Y-%m-%d')} ."
            query4 = query4 + f" Keep in mind that the published dates of the current strike are  : {published_date4}. If the context and the published date does not allow you to respond then responde 'unknown'."

            input_chain = {'context2':str_doc2, 'context4':str_doc4 , 'query2' : query2, 'query4' : query4, 'context5':str_doc5 , 'query5' : query5} # combining questions and contexts that will be treated in parallel
            final = self.__paralle_chain.invoke(input_chain) # Answering in parallel
            if final['response2'] != '':
                
                try :
                    response2 = self.parser2.parse(final['response2'])
                   
                    result["impacted_business_sectors"] = response2['business_sectors'] # you can change result key by any keyword
                    business_sectors = ", ".join(response2['business_sectors'])

                    query3 = self.__query3.format(company = company, business_sectors = business_sectors) # for this exemple, we have two information 'company name' and 'business_sectors' to add up to the query3
                          
                except Exception as e :
                    print(f" error parsing response2 : {e}")
                    result["impacted_business_sectors"] = []
            else :
                result["impacted_business_sectors"] = []
                                         
            if final['response4'] != '':
                
                try :
                    response4 = self.parser4.parse(final['response4'])
                    result["temporality"] = response4
                except Exception as e : # it means that the response4 are not well parsed. it is not well parsed because 'response4['temporality']' is an empty string
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

           
            result['sources'] = list(set(sources)) # list of urls
            
            vectores.delete([vectores.index_to_docstore_id[i] for i in range(vectores.index.ntotal)]) # The data of label j are deleted from the vectorstore database.
                                                                                                      # The vectorstore will be fill in the next iteration with the data of label j+1

            tmp_result = {key: result[key] for key in self.keys_order if key in list(result.keys())}
            
            results.append(tmp_result)
            
            print("results :")
            print(tmp_result)
            print('-'*100)
            
            # The two bellow computation are not useful because it compute the token number which are not part of retrieval process. You can keep or remove them. 
            self.number_token = self.number_token + len(self.__query1) + len(query2) + len(query3) + len(query4) + len(query5)
            self.number_token = self.number_token + len(str_doc1) + len(str_doc2) + len(str_doc3) + len(str_doc4) + len(str_doc5)

        self.results = results
        self.failed_labels = fail
