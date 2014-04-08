import sys
import os.path
import urllib2
from HTMLParser import HTMLParser
import sqlite3
import time
from datetime import date

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
        self.next_page_url = None
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if attrs[0] == ('class', 'b-vacancy-list-link b-marker-link'):
                #print "URL:", attrs[2][1]
                self.urls.append(attrs[2][1])
                self.read_vacancy = 1
            if attrs[0][0] == 'href' and attrs[0][1].find('employer') == 1:
                self.read_employer = 1
            if attrs[0] == ('class', 'b-pager__next-text m-active-arrow HH-Pager-Controls-Next'):
                #print "Next Page attrs:", attrs
                #print "Next Page URL:", attrs[2][1]
                self.next_page_url = 'http://spb.hh.ru' + attrs[2][1]

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


def grabPage(page_url, page_name):
    print 'Getting page %s ... ' % page_name,
    f = urllib2.urlopen(page_url)
    rcode = f.getcode()
    print '%s' % rcode
    if rcode != 200:
        print 'Can\'t reach page\n%s\n... terminating' % page_url
        sys.exit()

    content = f.read()
    dec_content = content.decode('utf-8')
    f.close()

    parser = MyHTMLParser()
    parser.feed(dec_content)
    parser.fetch_result()

    return parser.next_page_url


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


def filterVacancies(silent_mode = False):
    print 'Filtering ...'

    outcomes = []

    for i in range(total_vacancies):
        is_accepted = False
        for keyword in accepted_keywords:
            pos = unfiltered_vac_names[i].find(keyword)
            if pos > -1:
                is_accepted = True
                filtered_vac_names.append(unfiltered_vac_names[i])
                filtered_vac_links.append(unfiltered_vac_links[i])
                filtered_emp_names.append(unfiltered_emp_names[i])
                outcomes.append('Accepted: ' + unfiltered_vac_names[i].encode('utf-8'))
                break
        if is_accepted is False:
            outcomes.append('Rejected: ' + unfiltered_vac_names[i].encode('utf-8'))

    global filtered_vacancies
    filtered_vacancies = len(filtered_vac_names)

    global junk_percent
    junk_percent = int(100 * ( float(total_vacancies - filtered_vacancies) / total_vacancies ))

    if not silent_mode:
        for outcome in outcomes:
            print outcome
        print '\nFiltered Vacacies:\n--------------------'
        for i in range(filtered_vacancies):
            print 'Vacancy   %i' % i
            print 'Name:     %s' % filtered_vac_names[i].encode('utf-8')
            print 'Employer: %s' % filtered_emp_names[i].encode('utf-8')
            print 'URL:      %s' % filtered_vac_links[i]
            print '---'
        print '\nTotal\n    unfiltered: %i vacancies on %i page(s)' % (total_vacancies, total_pages)
        print '    %i of %i vacancies were accepted (%i%% junk)\n' % (filtered_vacancies, total_vacancies, junk_percent)


def isDatabaseOK():
    try:
        if os.path.getsize('vacancies.database') < 4096:
            print '\nDatabase file appears to be too small.' \
                  'Check content of file named \'vacancies.database\', ' \
                  'then run the script with --init option to re-create database.\n'
            return False
    except OSError:
        print '\nDatabase file not found. Run the script with --init option to create a new one.\n'
        return False
    return True


def initDB():
    print 'Resetting DB ...'
    f = open('vacancies.database', 'w')
    f.close()

    print 'Creating tables ...'
    conn = sqlite3.connect("vacancies.database")
    cursor = conn.cursor()

    create_empl_table = """
    CREATE TABLE EMPLOYERS (
        EmployerID INTEGER PRIMARY KEY AUTOINCREMENT,
        EmployerName CHAR(300)
        )
    """

    create_vacancies_table = """
    CREATE TABLE VACANCIES (
        VacancyID INTEGER PRIMARY KEY AUTOINCREMENT,
        EmployerID INTEGER,
        VacancyName CHAR(300),
        VacancyURL CHAR(300),
        VacancyDate CHAR(10),
        VacancyLastUpdated CHAR(10),
        VacancyUpdatesCount INTEGER
        )
    """

    try:
        print 'Creating EMPLOYERS table ...'
        cursor.execute(create_empl_table)
        print 'Creating VACANCIES table ...'
        cursor.execute(create_vacancies_table)
        print 'Done!'
    except Exception as e:
        print 'Ops!\n' + str(e)
        conn.close()
        sys.exit()

    conn.close()


def dumpData():
    print 'Dumping data ...'

    if not isDatabaseOK():
        sys.exit()

    conn = sqlite3.connect("vacancies.database")
    cursor = conn.cursor()

    select_data_cmd = """
        select
              EmployerName,
              VacancyName,
              VacancyURL,
              VacancyDate,
              VacancyLastUpdated,
              VacancyUpdatesCount
        from VACANCIES
        natural join EMPLOYERS
        -- on EmployerID
    """

    try:
        print 'Retrieving data ... ',
        cursor.execute(select_data_cmd)
        print 'done'
    except Exception as e:
        print 'Ops!\n' + str(e)
        conn.close()
        sys.exit()

    dumped_vacancies = cursor.fetchall()

    for vacancy in dumped_vacancies:
        print '---'
        print 'vacancy:    ' + vacancy[1].encode('utf-8')
        print 'employer:   ' + vacancy[0].encode('utf-8')
        print 'url:        ' + vacancy[2]
        print 'placed:     ' + vacancy[3]
        print 'updated:    ' + vacancy[4]
        print 'was updated ' + str(vacancy[5]) + ' times'

    print '\n\n%s vacancies in total'%len(dumped_vacancies)
    conn.close()


def dumpEmployers():
    print 'Dumping data ...'

    if not isDatabaseOK():
        sys.exit()

    conn = sqlite3.connect("vacancies.database")
    cursor = conn.cursor()

    select_data_cmd = """
        select
              EmployerID,
              EmployerName
        from EMPLOYERS
    """

    try:
        print 'Retrieving data ... ',
        cursor.execute(select_data_cmd)
        print 'done'
    except Exception as e:
        print 'Ops!\n' + str(e)
        conn.close()
        sys.exit()

    dumped_employers = cursor.fetchall()

    for employer in dumped_employers:
        print 'id: %3i '%employer[0],
        print 'name: %s'%employer[1].encode('utf-8')

    print '\n\n%s employers in total'%len(dumped_employers)
    conn.close()


def dumpUpdated(min_count=1):
    print 'Dumping data ...'

    if not isDatabaseOK():
        sys.exit()

    conn = sqlite3.connect("vacancies.database")
    cursor = conn.cursor()

    select_data_cmd = """
        select
              EmployerName,
              VacancyName,
              VacancyURL,
              VacancyDate,
              VacancyLastUpdated,
              VacancyUpdatesCount
        from VACANCIES
        natural join EMPLOYERS
        where VacancyUpdatesCount >= ?
        order by VacancyUpdatesCount,
                 VacancyLastUpdated
        -- on EmployerID
    """

    select_vacancies_count = """
        select
             count(*)
        from
            VACANCIES
    """

    try:
        print 'Retrieving data ... ',
        cursor.execute(select_data_cmd,(min_count,))
        updated_vacancies = cursor.fetchall()
        cursor.execute(select_vacancies_count)
        total_db_vacancies = int(cursor.fetchone()[0])
        print 'done'
    except Exception as e:
        print 'Ops!\n' + str(e)
        conn.close()
        sys.exit()

    for vacancy in updated_vacancies:
        print '---'
        print 'vacancy:    ' + vacancy[1].encode('utf-8')
        print 'employer:   ' + vacancy[0].encode('utf-8')
        print 'url:        ' + vacancy[2]
        print 'placed:     ' + vacancy[3]
        print 'updated:    ' + vacancy[4]
        print 'was updated ' + str(vacancy[5]) + ' times'

    updated_percent = int(100 * ( float(len(updated_vacancies)) / total_db_vacancies ) )
    print '\n\n%s of %i vacancies were updated at least %s times (%i%%)'%(len(updated_vacancies), total_db_vacancies, min_count, updated_percent)
    conn.close()


def storeNewVacancies():
    print 'Saving new vacancies into database ...'

    today_date = date.today().isoformat()
    print 'today is ' + today_date

    yesterday_date = date.fromordinal(date.today().toordinal()-1).isoformat()
    print 'yesterday was ' + yesterday_date

    conn = sqlite3.connect("vacancies.database")
    cursor = conn.cursor()

    search_employer = """select
                             EmployerID
                        from EMPLOYERS
                        where EmployerName = ?
                        """
    insert_employer = """insert into EMPLOYERS (EmployerName)
                         values (?)
                         """
    insert_vacancy = """insert into VACANCIES
                        (EmployerID,
                         VacancyName,
                         VacancyURL,
                         VacancyDate,
                         VacancyLastUpdated,
                         VacancyUpdatesCount)
                        values
                        ((select EmployerID from EMPLOYERS where EmployerName = ?),
                        ?,
                        ?,
                        ?,
                        ?,
                        ?)
                        """
    search_vacancy = """select
                            VacancyID
                        from VACANCIES
                        where
                             EmployerID = (select EmployerID from EMPLOYERS where EmployerName = ?)
                        and
                             VacancyName = ?
                        """
    get_update_time =   """select
                               VacancyLastUpdated
                           from VACANCIES
                           where
                               VacancyID = ?
                        """
    get_updates_count = """select
                               VacancyUpdatesCount
                           from VACANCIES
                           where
                               VacancyID = ?
                        """
    update_vacancy = """update VACANCIES
                        set
                            VacancyLastUpdated = ?,
                            VacancyUpdatesCount = ?
                        where
                            VacancyID = ?
                    """


    new_employers = 0
    new_vacancies = 0
    updated_vacancies = 0
    global filtered_vacancies
    for i in range(filtered_vacancies):
        cursor.execute(search_employer, (filtered_emp_names[i],))

        employer_id = cursor.fetchone()
        if employer_id is None:
            print 'New employer: %s' % filtered_emp_names[i].encode('utf-8')
            cursor.execute(insert_employer, (filtered_emp_names[i],))
            conn.commit()
            print '     vacancy: %s' % filtered_vac_names[i].encode('utf-8')
            print '     url:     %s' % filtered_vac_links[i]
            print '-------------'
            cursor.execute(insert_vacancy, (filtered_emp_names[i], filtered_vac_names[i], filtered_vac_links[i], today_date, today_date, 0))
            conn.commit()
            new_employers += 1
            new_vacancies += 1

        else:
            #print('Employer %s found with id %s'%(filtered_emp_names[i],employer_id[0]))
            cursor.execute(search_vacancy, (filtered_emp_names[i], filtered_vac_names[i],))
            vacancy_id = cursor.fetchone()

            if vacancy_id is None:
                print 'New vacancy: %s' % filtered_vac_names[i].encode('utf-8')
                cursor.execute(insert_vacancy, (filtered_emp_names[i], filtered_vac_names[i], filtered_vac_links[i], today_date, today_date, 0))
                conn.commit()
                print '   employer: %s' % filtered_emp_names[i].encode('utf-8')
                print '        url: %s' % filtered_vac_links[i]
                print '------------'
                new_vacancies += 1
            else:
                #print 'Vacancy found: %s of %s'%(filtered_vac_names[i],filtered_emp_names[i])
                cursor.execute(get_update_time, (vacancy_id[0],))
                update_time = cursor.fetchone()[0]
                if update_time != today_date and update_time != yesterday_date:
                    cursor.execute(get_updates_count, (vacancy_id[0],))
                    updates_count = cursor.fetchone()[0]
                    updates_count += 1
                    cursor.execute(update_vacancy, (today_date, updates_count, vacancy_id[0]))
                    conn.commit()
                    updated_vacancies += 1
                    #print 'updates count %i, last updated %s'%(updates_count, update_time)
                else:
                    #print 'already processed today'
                    pass

    conn.close()

    new_percent = int(100 * ( float(new_vacancies) / filtered_vacancies ) )
    junk_percent = int(100 * ( float(total_vacancies - filtered_vacancies) / total_vacancies ))
    updated_percent = int(100 * ( float(updated_vacancies) / filtered_vacancies ) )

    print '\n\n---'
    print 'New employers:     %i' % new_employers
    print 'New vacancies:     %i (%i total, %i accepted, %i%% junk, %i%% of accepted is new)' % \
          (new_vacancies, total_vacancies, filtered_vacancies, junk_percent, new_percent)
    print 'Updated vacancies: %i (%i%% of accepted)' % (updated_vacancies, updated_percent)






if __name__ == '__main__':
    silent_mode = False
    start_time = time.time()
    if len(sys.argv) >= 2:
        if sys.argv[1] == '--init':
            initDB()
            sys.exit()
        if sys.argv[1] == '--dump':
            dumpData()
            sys.exit()
        if sys.argv[1] == '--dump-employers':
            dumpEmployers()
            sys.exit()
        if sys.argv[1] == '--dump-updated':
            if len(sys.argv) == 3:
                dumpUpdated(sys.argv[2])
            else:
                dumpUpdated()
            sys.exit()
        if sys.argv[1] == '-s':
            silent_mode = True
        else:
            print "Usage:"
            print "--init = delete current db and create a new one"
            print "--dump = print vacancies list"
            print "--dump-employers = print employers list"
            print "--dump-updated N = print vacancies updated at least N times"
            sys.exit()

    grabVacancies()
    filterVacancies(silent_mode)

    if isDatabaseOK():
        storeNewVacancies()

    end_time = time.time()
    exec_time = end_time - start_time
    print '\nexecution took %5.1f seconds' % exec_time

