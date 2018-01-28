# -*- coding: utf-8 -*-
import sys, traceback
import requests
import os
from datetime import datetime
import time
import json
import collections
import logging
from bs4 import BeautifulSoup
#
import argparse
import progressbar as pb
#
import settings
import grobidAPI
import tei2dict
import csv
import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def processHeaderDocument():
    pdfs = utils.get_path_of_pdfs();
    with open(settings.OUTPUT_FILE, 'w', encoding='UTF-8', newline='') as output_file:
        wr = csv.writer(output_file, quoting=csv.QUOTE_ALL)
        for i, pdf in enumerate(pdfs):
            try:
                logger.debug("Process file #{} (total {}): '{}'".format(i + 1, len(pdfs), os.path.split(pdf)[1]))
                settings.print_message("Process file #{} (total {}): '{}'".format(i + 1, len(pdfs), os.path.split(pdf)[1]))
                settings.print_message("Send to grobid service..", 2)
                data = grobidAPI.get_data_from_grobid(settings.GROBID_PROCESSED_HEADER_COMMAND, open(pdf, 'rb'), settings.USING_TOR_BROWSER)
                settings.print_message("Check data", 2)
                logger.debug("Check data")
                if not data: raise Exception("Empty data")
                settings.print_message("Processing TEI data", 2)
                logger.debug("Convert tei to dictionary")
                dictData = tei2dict.tei_to_dict(data)
                logger.debug("Convert completed: {}".format(json.dumps(dictData)))
                authors = set(dictData["authors"]) if "authors" in dictData else []
                msg = "RESULT: has title:{:^3}has date:{:^3}has DOI:{:^3}has abstract:{:^3}authors:{:^4}has start page:{:^3}has end page:{:^3}has publisher:{:^3}".format(
                    "title" in dictData,
                    "pubdate" in dictData,
                    "DOI" in dictData,
                    "abstract" in dictData,
                    len(authors),
                    "start_page" in dictData,
                    "end_page" in dictData,
                    "publisher" in dictData
                    )
                settings.print_message(msg, 2)
                logger.debug(msg)
                row = list()
                row.append(os.path.split(pdf)[1])
                row.append(dictData["title"].strip() if "title" in dictData else "")
                row.append(dictData["pubdate"] if "pubdate" in dictData else "")
                row.append(dictData["DOI"] if "DOI" in dictData else "")
                row.append(dictData["abstract"].strip() if "abstract" in dictData else "")
                for author in authors: row.append(author)
                logger.debug("Write in file {}".format(json.dumps(row)))
                wr.writerow(row)
            except:
                settings.print_message(traceback.format_exc())
                logger.error(traceback.format_exc())


def processReferencesDocument():
    pdfs = utils.get_path_of_pdfs();
    with open(settings.OUTPUT_FILE, 'w', encoding='UTF-8', newline='') as output_file:
        wr = csv.writer(output_file, quoting=csv.QUOTE_ALL)
        for i, pdf in enumerate(pdfs):
            try:
                logger.debug("Process file #{} (total {}): '{}'".format(i + 1, len(pdfs), os.path.split(pdf)[1]))
                settings.print_message("Process file #{} (total {}): '{}'".format(i + 1, len(pdfs), os.path.split(pdf)[1]))
                settings.print_message("Send to grobid service..", 2)
                data = grobidAPI.get_data_from_grobid(settings.GROBID_PROCESSED_REFERENCES_COMMAND, open(pdf, 'rb'), settings.USING_TOR_BROWSER)
                settings.print_message("Check data", 2)
                logger.debug("Check data")
                if not data: raise Exception("Empty data")
                settings.print_message("Processing TEI data", 2)
                logger.debug("Convert tei to dictionary")
                dictData = tei2dict.tei_to_dict(data)
                logger.debug("Convert completed: {}".format(json.dumps(dictData)))
                for i, reference in enumerate(dictData["references"]):
                    try:
                        if not reference["ref_title"] and not "journal_title" in reference["journal_pubnote"]:
                            settings.print_message("Ref #{} (total {}) has not title, skip".format(i, len(dictData["references"])))
                            logger.debug("Ref #{} (total {}) has not title, skip".format(i, len(dictData["references"])))
                            continue
                        authors = set(reference["authors"]) if "authors" in reference else []
                        count_publications_on_scholar = utils.get_count_from_scholar(reference["ref_title"].strip() if reference["ref_title"] else 
                                   reference["journal_pubnote"]["journal_title"].strip() if "journal_title" in reference["journal_pubnote"] else "", settings.USING_TOR_BROWSER)
                        msg = "Ref #{} (total {}): has title:{:^3}has date:{:^3}Has DOI:{:^3}authors:{:^4}has start page:{:^3}has end page:{:^3}has publisher:{:^3}publications on scholar:{}".format(
                            i,
                            len(dictData["references"]),
                            reference["ref_title"] != None or "journal_title" in reference["journal_pubnote"],
                            "year" in reference["journal_pubnote"],
                            "doi" in reference["journal_pubnote"],
                            len(authors),
                            "start_page" in reference["journal_pubnote"],
                            "end_page" in reference["journal_pubnote"],
                            "journal_title" in reference["journal_pubnote"],
                            count_publications_on_scholar
                            )
                        settings.print_message(msg, 2)
                        logger.debug(msg)
                        row = list()
                        row.append(os.path.split(pdf)[1])
                        row.append(reference["ref_title"] if reference["ref_title"] else 
                                   reference["journal_pubnote"]["journal_title"] if "journal_title" in reference["journal_pubnote"] else "")
                        row.append(reference["journal_pubnote"]["year"] if "year" in reference["journal_pubnote"] else "")
                        row.append(reference["journal_pubnote"]["doi"] if "doi" in reference["journal_pubnote"] else "")
                        row.append(reference["journal_pubnote"]["start_page"] if "start_page" in reference["journal_pubnote"] else "")
                        row.append(reference["journal_pubnote"]["end_page"] if "end_page" in reference["journal_pubnote"] else "")
                        row.append(count_publications_on_scholar)
                        for author in authors: row.append(author)
                        logger.debug("Write in file {}".format(json.dumps(row)))
                        wr.writerow(row)
                    except:
                        settings.print_message(traceback.format_exc())
                        logger.error(traceback.format_exc())
            except:
                settings.print_message(traceback.format_exc())
                logger.error(traceback.format_exc())

def main():
    settings.print_message("Command: process headers" if settings.MODE == settings.PROCESS_HEADER_MODE else "Command: process references")
    settings.print_message("PDFs dir: {}".format(settings.PDFS_PATH))
    settings.print_message("Output file: {}".format(settings.OUTPUT_FILE))
    settings.print_message("Using TOR: {}".format(settings.USING_TOR_BROWSER))
    start_time = datetime.now()
    if settings.MODE == settings.PROCESS_HEADER_MODE:
        processHeaderDocument()
    else:
        processReferencesDocument()
    end_time = datetime.now()
    settings.print_message("Run began on {0}".format(start_time))
    settings.print_message("Run ended on {0}".format(end_time))
    settings.print_message("Elapsed time was: {0}".format(end_time - start_time))

if __name__ == "__main__":
    main()