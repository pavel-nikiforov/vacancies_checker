import sys
import urllib2
from HTMLParser import HTMLParser

vacancy_list_url = "http://spb.hh.ru/applicant/searchvacancyresult.xml?source=&text=&profArea=1&s=1.117&areaId=2&desireableCompensation=&compensationCurrencyCode=RUR&experience=&orderBy=2&searchPeriod=1&itemsOnPage=50"
accepted_keywords = ['QA', 'test', 'Test', 'quality','Quality', u'\u0442\u0435\u0441\u0442', u'\u0422\u0435\u0441\u0442', u'\u043A\u0430\u0447\u0435\u0441\u0442\u0432']

unfiltered_vac_names = []
unfiltered_emp_names = []
unfiltered_vac_links = []

filtered_vac_names = []
filtered_emp_names = []
filtered_vac_links = []

total_pages = 0
total_vacancies = 0
filtered_vacancies = 0

junk_percent = 0
new_percent = 0


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
    next_page_url = vacancy_list_url
    next_page_name = 1

    while next_page_url is not None:
        next_page_url = grabPage(next_page_url, int(next_page_name))
        next_page_name += 1

    global total_pages
    global total_vacancies
    total_pages = next_page_name - 1
    total_vacancies = len(unfiltered_vac_names)


def filterVacancies():
    print 'Filtering ...'

    for i in range(total_vacancies):
        is_accepted = False
        for keyword in accepted_keywords:
            pos = unfiltered_vac_names[i].find(keyword)
            if pos > -1:
                is_accepted = True
                filtered_vac_names.append(unfiltered_vac_names[i])
                filtered_vac_links.append(unfiltered_vac_links[i])
                filtered_emp_names.append(unfiltered_emp_names[i])
                print 'Accepted: ' + unfiltered_vac_names[i]
                break
        if is_accepted is False:
            print 'Rejected: ' + unfiltered_vac_names[i]

    global filtered_vacancies
    filtered_vacancies = len(filtered_vac_names)

    global junk_percent
    junk_percent = int(100 * ( float(total_vacancies - filtered_vacancies) / total_vacancies ))




if __name__ == '__main__':
    grabVacancies()
    filterVacancies()

    print '\nFiltered Vacacies:\n--------------------'
    for i in range(filtered_vacancies):
        print 'Vacancy   %i'%i
        print 'Name:     %s'%filtered_vac_names[i]
        print 'Employer: %s'%filtered_emp_names[i]
        print 'URL:      %s'%filtered_vac_links[i]
        print '---'
    print '\nTotal\n    unfiltered: %i vacancies on %i page(s)'%(total_vacancies, total_pages)
    print '    %i of %i vacancies were accepted (%i%% junk)' % (filtered_vacancies, total_vacancies, junk_percent)
