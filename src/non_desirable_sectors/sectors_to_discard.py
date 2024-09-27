
SECTORS_TO_DISCARD = ['hospital', 'health', 'healthcare', 'medical', 'education','school', 'schools', 'media', 
                    'pharmaceutical', 'pharmaceuticals','public transportation','public bus','railroad',
                    'railways','tourism','public service','public services','public administration','medical services',
                    'government','government service','public ddministration','waste management',"social services",'cleaning', 
                    'cleaning services', 'public transport','infrastructure','food delivery', 'food', 'travel','hospitality', 'food', 
                    'hunger','aviation','airport services','hospitality','postal and courier services', 'postal', 'courier services',
                    'airline industry', 'airline','shipping', 'logistics', 'maritime transport', 'logistics and transportation']

#TOD0 : you can add any sector you deem irrelevant. 
#Notice that this file is not use for dataiku pipeline because we set "SECTORS_TO_DISCARD" as an global an global variable so that the user can 
#easyly modify it without gettinf into this code. 