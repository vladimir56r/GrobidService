# -*- coding: utf-8 -*-
import os, logging, re, traceback, sys
import requests
import time
#
import browsercookie
#
import settings
from bs4 import BeautifulSoup
from torrequest import TorRequest

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_path_of_pdfs():
    return sorted(
        [os.path.join(root, filename) for root, dirnames, filenames in os.walk(settings.PDFS_PATH) for filename in
            filenames if filename.endswith('.pdf') and os.path.getsize(os.path.join(root, filename)) > 0])

def get_request(url, att_file = None, using_TOR = False):
    """Send get request & return data"""
    retry = settings.DEFAULT_MAX_RETRIES
    while retry > 0:
        try:
            try:
                if using_TOR:
                    with TorRequest(tor_app=r".\Tor\tor.exe") as tr:
                        response = tr.post(url=url, files = att_file, cookies = browsercookie.chrome(), timeout=settings.DEFAULT_TIMEOUT)
                else:
                    response = requests.post(url=url, files = att_file, cookies = browsercookie.chrome(), timeout=settings.DEFAULT_TIMEOUT)
            except requests.exceptions.Timeout:
                logging.debug("timeout from requests")
                settings.print_message("timeout from requests", 2)
                raise ConnectionError("request timeout after %d seconds" % settings.DEFAULT_TIMEOUT)
            except requests.exceptions.RequestException as e:
                raise ConnectionError("request exception: %s" % e)
            if response.status_code == 200:
                return response.text
            else:
                raise Exception("HTTP %d - %s" % (response.status_code, response.reason))
        except ConnectionError as error:
            retry = retry - 1
            settings.print_message("ran into connection error: '%s'" % error, 2)
            logging.info("ran into connection error: '%s'" % error)
            if retry > 0:
                settings.print_message("retrying in %d seconds" % settings.DEFAULT_SLEEP, 2)
                logging.info("retrying in %d seconds" % settings.DEFAULT_SLEEP)
                time.sleep(settings.DEFAULT_SLEEP)
        else:
            retry = 0

def get_soup(url, using_TOR = False):
    """Return the BeautifulSoup for a page"""
    try:
        request = get_request(url, using_TOR = using_TOR)
        if request == None:
            logger.debug("Request is empty, don't create soup.")
            return None
        soup = BeautifulSoup(request, 'html.parser')
        return soup
    except Exception as error:
        #logger.warn(traceback.format_exc())
        raise
    return None

def get_about_count_results(soup):
    """Shows the approximate number of pages as a result"""
    title = soup.find('div', {'id': 'gs_ab_md'})
    if title:
        title = title.find('div', {'class': 'gs_ab_mdw'})
        if title:
            count_papers = title.text
            if count_papers:
                count_papers = count_papers.split(' ')[1].replace(',', '')
            else:
                count_papers = len(soup.find_all('h3', class_="gs_rt"))
            try:
                int(count_papers)
            except:
                count_papers = title.text.split(' ')[0].replace(',', '')
    else:
        count_papers = len(soup.find_all('h3', class_="gs_rt"))
    return int(count_papers)

def get_count_from_scholar(title, using_TOR = False):
    """ Search publication on Google.scholar and return count of searched papers """
    url = settings.SCHOLAR_SEARCH.format("{}".format(title))
    return get_about_count_results(get_soup(url, using_TOR = using_TOR))