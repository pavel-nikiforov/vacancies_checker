import sys
import urllib2
from HTMLParser import HTMLParser

vacancy_list_url = "http://spb.hh.ru/applicant/searchvacancyresult.xml?source=&text=&profArea=1&s=1.117&areaId=2&desireableCompensation=&compensationCurrencyCode=RUR&experience=&orderBy=2&searchPeriod=1&itemsOnPage=50"

unfiltered_vac_names = []
unfiltered_emp_names = []
unfiltered_vac_links = []

total_pages = 0
total_vacancies = 0
filtered_vacancies = 0


# create a custom HTML parser
class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.read_vacancy = 0
        self.read_employer = 0
        self.vacancies = []
        self.employers = []
        self.urls = []
        self.nextPageURL = None
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if attrs[0] == ('class', 'b-vacancy-list-link b-marker-link'):
                #print "URL:", attrs[1][1]
                self.urls.append(attrs[1][1])
                self.read_vacancy = 1
            if attrs[0][0] == 'href' and attrs[0][1].find('employer') == 1:
                self.read_employer = 1
            if attrs[0] == ('class', 'b-pager__next-text m-active-arrow HH-Pager-Controls-Next'):
                #print "Next Page URL:", attrs[1][1]
                self.nextPageURL = 'http://spb.hh.ru' + attrs[1][1]

    def handle_data(self, data):
        if self.read_vacancy == 1:
            #print "Vacancy: ", data
            self.vacancies.append(data)
            self.read_vacancy = 0
        if self.read_employer == 1:
            #print "Employer: ", data
            self.employers.append(data)
            self.read_employer = 0

    def fetch_result(self):
        for i in range(len(self.vacancies)):
            unfiltered_vac_names.append(self.vacancies[i])
            unfiltered_emp_names.append(self.employers[i])
            unfiltered_vac_links.append(self.urls[i])


def grabPage(pageURL, pageName):
    print 'Getting page %s ... '%pageName,
    f = urllib2.urlopen(pageURL)
    rcode = f.getcode()
    print '%s'%rcode
    if rcode != 200:
        print 'Can\'t reach page\n%s\n... terminating'%pageURL
        sys.exit()

    content = f.read()
    dec_content = content.decode('utf-8')
    f.close()

    parser = MyHTMLParser()
    parser.feed(dec_content)
    parser.fetch_result()

    return parser.nextPageURL


def grabVacancies():
    nextPageURL = vacancy_list_url
    nextPageName = 1

    while nextPageURL is not None:
        nextPageURL = grabPage(nextPageURL, int(nextPageName))
        nextPageName += 1

    global total_pages
    global total_vacancies
    total_pages = nextPageName - 1
    total_vacancies = len(unfiltered_vac_names)



if __name__ == '__main__':
    grabVacancies()

    print '\nUnfiltered Vacacies:\n--------------------'
    for i in range(len(unfiltered_emp_names)):
        print 'Vacancy   %i'%i
        print 'Name:     %s'%unfiltered_vac_names[i]
        print 'Employer: %s'%unfiltered_emp_names[i]
        print 'URL:      %s'%unfiltered_vac_links[i]
    print '\nTotal unfiltered: %i vacancies on %i page(s)'%(total_vacancies, total_pages)