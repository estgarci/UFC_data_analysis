
'''extraction of data from ufc website
extracts all information for each fighter '''

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup, SoupStrainer
from numpy import NaN
import pandas as pd
import json
import string


def website_soup(url, segment):
    """
    requests website's content and then converts
    an HTML segment into a beautifulSoup object
    Parameters
    ----------
    url : str
        website link
    segment : str
        html tag in which the desired information is stored
    Returns
    -------
    beautifulSoup object parsed from the desired segment
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        strainer = SoupStrainer(segment)
        soup = BeautifulSoup(response.content, 'lxml', parse_only=strainer)
        return soup
    except HTTPError:
        print("HTTP error occured")
    except Exception as err:
        print("Other error occured")


class UrlExtractor(object):
    base_site = 'http://ufcstats.com/statistics/fighters?char=a&page=all'

    def __init__(self):
        """Initializing the UrlExtractor will automatically download all the fighter urls"""
        self.all_fighter_urls = self.get_all_fighter_urls()

    @staticmethod
    def alphabetize_urls(url, var_index):
        """
        Generator of a list of alphabatized urls. Replaces 1 letter
        in the base URL with every lower-case letter of the alphabet (a-z)
        Parameters
        ----------
        url: str
            the full URL of ANY version of the parent website
        var_index: int
            index of the varying letter in the URL
        Yields:
        ------
        generator
            27 alphabetized urls (a-z)
        """
        for letter in string.ascii_lowercase:
            new_url = url[:var_index] + letter + url[var_index + 1:]
            yield new_url

    @staticmethod
    def get_children_urls(url):
        """
        parses fighter's urls from the given website
        Parameters
        ----------
        url : str
            alphabetical url
            for example; http://ufcstats.com/statistics/fighters?char=a&page=all
            which contains all fighters with who's name start with the letter a
        Yields
        -------
        str
            list of fighter urls in the given alphabetical url
        """
        container = website_soup(url, 'tbody')
        tags = container.find_all('a')
        for tag in tags:
            yield tag.get('href')

    def get_all_fighter_urls(self):
        """
        Creates a list of ALL the fighter urls in the ufcstats.com website.
        Returns:
        ---------
        list[str]
            list of all fighter's url in the http://ufcstats.com website
            with no duplicates
        """
        all_urls = []
        for url in self.alphabetize_urls(self.base_site, -10):
            all_urls.extend(self.get_children_urls(url))

        return list(dict.fromkeys(all_urls))


class UfcScraper(UrlExtractor):

    def __init__(self):
        super().__init__()

    def export_fights_and_fighters(self):
        self.export_fighters()
        self.export_fights()

    def export_fights(self):
        """
        dumps all fighter statistics into a json file
        Writes:
        -----
        json file
            json file containing all scraped fighters and their fights
        """
        with open('fights.json', 'w') as outfile:
            fights_contenders = []

            for i, link in enumerate(self.all_fighter_urls):
                fights = self.get_fights_information(website_soup(link,'section'))
                for fight in fights:
                    contenders = fight['contenders']
                    fights_contenders.append(contenders)
                    #filter out duplicates
                    condition1 = [fight['contenders'][0], fight['contenders'][1]] in fights_contenders
                    condition2 = [fight['contenders'][1], fight['contenders'][0]] in fights_contenders
                    if condition1 or condition2:
                        #writting unique fights to file
                        json.dump(fight, outfile)
                        outfile.write('\n')

                print(i / len(self.all_fighter_urls) * 100, '% complete')

    def export_fighters(self):
        """
        dumps all fighter statistics into a json file
        Writes:
        -----
        json file
            json file containing all scraped fighters without their fights
        """
        with open('fighters.json', 'w') as outfile:
            for i, link in enumerate(self.all_fighter_urls):
                print(link)
                fighter = self.get_fighter_statistics(link)
                json.dump(fighter, outfile)
                outfile.write('\n')
                print(i / len(self.all_fighter_urls) * 100, '% complete')

    def get_fighter_statistics(self, www):
        """
        Creates a list of all the fighter's url in the ufc website.
        Returns:
        -----
        list[str]
            list of all of fighter urls in the http://ufcstats.com website
            with no duplicates
        """

        wb_soup = website_soup(www, 'section')
        '''Parsing fighter's name and record'''
        name, record = self.get_name_and_record(wb_soup)
        wins, losses, draws = self.clean_record(record)
        '''Parsing remaining attributes'''
        tags = wb_soup.find_all("li", "b-list__box-list-item b-list__box-list-item_type_block")
        fighter_stats = [item.text.split() for item in tags]

        for i, stat in enumerate(fighter_stats):
            if i is 0:
                height = self.clean_height(' '.join(stat[1:4]))
            elif i is 1:
                weight = self.clean_data(stat[1])
            elif i is 2:
                reach = self.clean_data(stat[1])
            elif i is 3:
                try:
                    stance = str(stat[1])
                except:
                    stance = NaN
            elif i is 4:
                dob = self.clean_date(stat)
            elif i is 5:
                slpm = self.clean_data(stat[1])
            elif i is 6:
                stracc = self.clean_data(stat[2])
            elif i is 7:
                sapm = self.clean_data(stat[1])
            elif i is 8:
                strdef = self.clean_data(stat[2])
            elif i is 9:
                continue
            elif i is 10:
                tdavg = self.clean_data(stat[2])
            elif i is 11:
                tdacc = self.clean_data(stat[2])
            elif i is 12:
                tddef = self.clean_data(stat[2])
            elif i is 13:
                subavg = self.clean_data(stat[2])

        fighter_dict = dict(url=www, name=name, wins=wins, draws=draws,
                            losses=losses, height=height, weight=weight, reach=reach,
                            stance=stance, dob=dob, slpm=slpm, stracc=stracc, sapm=sapm,
                            strdef=strdef, tdavg=tdavg, tdacc=tdacc, tddef=tddef, subavg=subavg,
                            )

        return fighter_dict

    @staticmethod
    def get_fights_information(section_soup):
        """
        Scrapes match history for a particular fighter. 
        Parameters
        ----------
        section_soup: BeautifulSoup
            object containing the strained version of the fighter's website soup. The strained
            version represents the 'section' html tag  previously parsed from a fighter's HTML.
            straining can be done with the BeautifuSoup built in class called 'SoupStrainer'
        Returns
        ---------
        list[dictionary]
           list of dictionaries containing contenders, result, method time and statistics about each fight
        """
        fights_tags = section_soup.tbody.find_all('tr')[1:]
        all_fights = []
        for fight_tag in fights_tags:
            raw_fight_attributes = fight_tag.find_all('p')
            fight_attributes = [attribute.text.strip() for attribute in raw_fight_attributes]
            #only extract the tag if the box contains a previous match.
            #sometimes a box might contain information about a future match, we do not want to save that
            #information, yet... in the future we will.
            if len(fight_attributes) == 17:
                match = {
                            'contenders': [fight_attributes[1], fight_attributes[2]],
                            'result': fight_attributes[0],
                            'method': fight_attributes[13],
                            'time': fight_attributes[16],
                            'fight_stats': [
                                            dict(name=fight_attributes[1],
                                                 st=fight_attributes[3],
                                                 td=fight_attributes[5],
                                                 sub=fight_attributes[7],
                                                 pss=fight_attributes[9]),
                                            dict(name=fight_attributes[2],
                                                 st=fight_attributes[4],
                                                 td=fight_attributes[6],
                                                 sub=fight_attributes[8],
                                                 pss=fight_attributes[10])
                                            ]
                           }
                
                all_fights.append(match)
        return all_fights

    @staticmethod
    def clean_height(data):
        """
        cleans height data coming from the ufcstats website and converts
        the string representation of height into a float
        Parameters
        ----------
        data : str
            data contained in the ufcstats website
        Returns
        -------
        type
            beautifulSoup object parsed from the desired segment
        """
        try:
            cleaned_data = [integer for integer in data if integer.isnumeric()]
            feet = cleaned_data[0]
            inches = ''.join(cleaned_data[1:])
            height_feet = float(feet) + float(inches) / 12.0
            return round(height_feet, 3)
        except:
            return NaN

    @staticmethod
    def clean_data(data):
        """
        cleans the string and converts it into an int
        Parameters
        ----------
        data : str
            data scraped from the website
        Returns
        -------
        int
            string that has been converted into an float
        """
        '''cleans data from '%' and '/' and converts unicode data to a float'''
        digits = [integer for integer in data if integer.isnumeric() or '.' in integer]

        if len(digits):
            cleaned_digits = ''.join(digits)
            return float(cleaned_digits)
        else:
            return NaN

    def clean_date(self, date):
        """
        converts the date string into a hyphened date ie: (month-day-year) 
        Parameters
        ----------
        date : str
            date given in the website in the form of "Jan 16, 1992"
        Returns
        -------
        str
            (mon-day-year) string format
        """
        stringDate = ''.join(date[1:4])
        if '--' not in stringDate:

            month = self.get_month(stringDate)
            day = stringDate[3:5]
            year = stringDate[6:10]

            date = '{}-{}-{}'.format(month, day, year)

            return date
        else:
            return None

    @staticmethod
    def get_month(month):
        #this method can be replaced bu the datetime package
        """
        converts month's first 3 letters into a numerical month
        Parameters
        ----------
        month : str
            3 letter representation of the month
        Returns
        -------
        str
            (mon-day-year) string format
        """
        if 'Jan' in month:
            return 1
        elif 'Feb' in month:
            return 2
        elif 'Mar' in month:
            return 3
        elif 'Apr' in month:
            return 4
        elif 'May' in month:
            return 5
        elif 'Jun' in month:
            return 6
        elif 'Jul' in month:
            return 7
        elif 'Aug' in month:
            return 8
        elif 'Sep' in month:
            return 9
        elif 'oct' in month:
            return 10
        elif 'Nov' in month:
            return 11
        elif 'Dec' in month:
            return 12

    @staticmethod
    def get_name_and_record(soup):
        """
        extracts the fighter's name and match history from a string
        Parameters
        ----------
        soup : BeautifulSoup
            beautifulSoup object representation of the fighter's ufc website
        Returns
        -------
        str, str
            name and record represented as strings
        """
        container = soup.h2.text.split()
        record_index = [i for i, attribute in enumerate(container) if attribute == 'Record:'][0]
        name = ' '.join(container[0:record_index])
        record = container[record_index + 1:][0]

        return name, record

    @staticmethod
    def clean_record(record):
        """
        separates a string in the format (#-#-#) into 3 separate numbers
        Parameters
        ----------
        record : str
            string in the format of (#-#-#)
        Returns
        -------
        int,int,int
            wins losses and draws
        """
        wins_draws_losses = record.split('-')
        wins = wins_draws_losses[0]
        losses = wins_draws_losses[1]
        draws = wins_draws_losses[2]

        return wins, losses, draws


if __name__ == '__main__':
    '''use export_fighters() to scrape and export fighter statistics'''
    #UfcScraper().export_fighters()

    '''use export_fights() to scrape and export the match history of every fighter'''

    UfcScraper().export_fights()
    
