import sys
import urllib2
from HTMLParser import HTMLParser

vacancy_list_url = "http://spb.hh.ru/applicant/searchvacancyresult.xml?source=&text=&profArea=1&s=1.117&areaId=2&desireableCompensation=&compensationCurrencyCode=RUR&experience=&orderBy=2&searchPeriod=1&itemsOnPage=50"


# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.read_vacancy = 0
        self.read_employer = 0
        self.vacancies = []
        self.employers = []
        self.urls = []
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if attrs[0] == ('class', 'b-vacancy-list-link b-marker-link'):
                print "URL:", attrs[1][1]
                self.urls.append(attrs[1][1])
                self.read_vacancy = 1
            if attrs[0][0] == 'href' and attrs[0][1].find('employer') == 1:
                self.read_employer = 1
    #def handle_endtag(self, tag):
    #    print "Encountered an end tag :", tag
    def handle_data(self, data):
        if self.read_vacancy == 1:
            print "Vacancy: ", data
            self.vacancies.append(data)
            self.read_vacancy = 0
        if self.read_employer == 1:
            print "Employer: ", data
            self.employers.append(data)
            self.read_employer = 0


def grabVacancies():
    print 'Getting the first page ... ',
    f = urllib2.urlopen(vacancy_list_url)
    rcode = f.getcode()
    print '%s'%rcode
    if rcode != 200:
        print 'Can\'t reach firs page, terminating'
        sys.exit()

    content = f.read()
    #print content
    dec_content = content.decode('utf-8')

    parser = MyHTMLParser()
    parser.feed(dec_content)



if __name__ == '__main__':
    grabVacancies()