vacancies_checker
=================

Why the script was written?
---------------------------
Everyone loves [HeadHunter.ru] (http://hh.ru/)  
The site holds leading position on job search market in Russia  
Unfortunately search results based on job area (like IT->Testing)  
contain a lot of unrelated vacancies.  
Say, if you are looking for a SW Test Engineer opportunity  
the search result will contain vacancies for developers, DBAs, 
support engineers and so on.  

Moreover, most of vacancies aren't new. Employers just refresh publication date over and over for the same vacancy.  
This renders new vacancies hard to spot.  

What does the the script do?
----------------------------
1. Sends HTTP request for URL stated in  
*vacancy_list_url* variable
2. Extracts information about vacancies from the response
3. Extracts information about subsequent pages (if any)
4. Get the subsequent pages and extract vacancies information from them
5. Filter the vacancies
   If a vacancy name contains one of keywords listed
   in *accepted_keywords* - we accept it.
6. Process the list of 'filtered' vacancies
   If a vacancy is already in database - update LastUpdatedDate
   If a vacancy is not in database - list it as new (and add to db)

What version of Python does it for?
-----------------------------------
2.6+

Will the script work on Windows?
--------------------------------
No.