# -*- coding: utf-8 -*-
import argparse
import collections
import os, logging, re, traceback, sys
import json
import time
from datetime import datetime
import re
from torrequest import TorRequest
#
_main_dir = os.path.dirname(__file__)
#

MAX_RETRY = 5

def build_version_string():
    """ This function read current version from version.txt and format version string """
    # MAJOR version when you make incompatible API changes
    __MAJOR_VERSION__ = str()
    # MINOR version when you add functionality in a backwards-compatible manner
    __MINOR_VERSION__ = str()
    # PATCH version when you make backwards-compatible bug fixes
    __PATCH_VERSION__ = str()
    with open('version.txt', 'r') as version_file:
        lines = version_file.readlines()
        for line in lines:
            if line.startswith('__MAJOR_VERSION__'):
                __MAJOR_VERSION__ = re.findall('\d+', line)[0]
            if line.startswith('__MINOR_VERSION__'):
                __MINOR_VERSION__ = re.findall('\d+', line)[0]
            if line.startswith('__PATCH_VERSION__'):
                __PATCH_VERSION__ = re.findall('\d+', line)[0]
    _header = "GrobidServise (v{0}.{1}.{2}) {3}".format(__MAJOR_VERSION__, __MINOR_VERSION__, __PATCH_VERSION__,
                                                      datetime.now().strftime("%B %d %Y, %H:%M:%S"))
    return _header

SCHOLAR_SEARCH = 'https://scholar.google.ru/scholar?q={0}&hl=en'
GROBID_SERVER = 'http://cloud.science-miner.com/grobid/api/'
GROBID_PROCESSED_HEADER_COMMAND = 'processHeaderDocument' # processFulltextDocument processReferences
GROBID_PROCESSED_REFERENCES_COMMAND = 'processReferences' # processFulltextDocument processReferences
DEFAULT_TIMEOUT = 60
DEFAULT_SLEEP = 5
DEFAULT_MAX_RETRIES = 3
USING_TOR_BROWSER = False


PROCESS_HEADER_MODE = 0
PROCESS_REFERENCES_MODE = 1

# Program version
_header = build_version_string()

# system settings
_LOGBOOK_NAME = None
OUTPUT_FILE = None

INFO_FILE = None
LOG_LEVEL = logging.DEBUG
# encoding
OS_ENCODING = "utf-8"
OUTPUT_ENCODING = "utf-8"

# logging

# CONSOLE LOG
cfromat = "[{0}] {1}{2}"
def print_message(message, level=0):
    level_indent = " " * level
    print(cfromat.format(datetime.now(), level_indent, message))
#

# Logging handlers
class InMemoryHandler(logging.Handler):
    def emit(self, record):
        #print(self.format(record))
        IN_MEMORY_LOG.append(self.format(record))

_LOG_HANDLER = InMemoryHandler()
_LOG_FORMAT = "[%(asctime)s %(levelname)s %(name)s] %(message)s"
_LOG_COPY_FORMAT = "%(message)s"
_LOG_HANDLER.setFormatter(logging.Formatter(_LOG_FORMAT))

IN_MEMORY_LOG = []

main_logger = logging.getLogger("")

main_logger.addHandler(_LOG_HANDLER)
main_logger.setLevel(LOG_LEVEL)

logger = logging.getLogger(__name__)

print_message(_header)
logger.info(_header)

# Command line parser
logger.info("Initializing argument parser, version: %s" % argparse.__version__)
_parser = argparse.ArgumentParser()
requiredNamed = _parser.add_argument_group('Required arguments')
requiredNamed.add_argument("-l", "--log", action="store", dest="LOG_FILE_NAME", help="Logbook file", type=str, required=True)
requiredNamed.add_argument("-i", "--inputdir", action="store", dest="INPUT_DIR", help="Dir with PDF's", type=str, required=True)
requiredNamed.add_argument("-o", "--outputfilename", action="store", dest="OUTPUT_FILE", help="Output file", type=str, required=True)
requiredNamed.add_argument("-t", "--tor", action="store_true", dest="USING_TOR", help="Using TOR browser", required=False)
_group = _parser.add_mutually_exclusive_group()
_group.add_argument("-f", action="store_true", dest="ProcessHeader", help="ProcessHeader")
_group.add_argument("-s", action="store_false", dest="ProcessReferences", help="ProcessReferences")

logger.debug("Parse arguments.")
try:
    _command_args = _parser.parse_args()
except:
    print_message("Check promt arguments, exit.")
    sys.exit()
_LOGBOOK_NAME = _command_args.LOG_FILE_NAME
PDFS_PATH = _command_args.INPUT_DIR
OUTPUT_FILE = _command_args.OUTPUT_FILE
MODE = PROCESS_HEADER_MODE if _command_args.ProcessHeader else PROCESS_REFERENCES_MODE
if _command_args.USING_TOR: 
    USING_TOR_BROWSER = True
#    TOR = TorRequest(tor_app=r".\Tor\tor.exe")

logger.info("Initializing logbook.")

# Add file handler
_LOG_F_HANDLER = logging.FileHandler(_LOGBOOK_NAME, encoding = OUTPUT_ENCODING)
_LOG_F_HANDLER.setLevel(LOG_LEVEL)
_LOG_F_FORMATTER = logging.Formatter(_LOG_COPY_FORMAT)
_LOG_F_HANDLER.setFormatter(_LOG_F_FORMATTER)

logger.debug("Copy startlog in logbook.")
main_logger.removeHandler(_LOG_HANDLER)
main_logger.addHandler(_LOG_F_HANDLER)
for record in IN_MEMORY_LOG:
    logger.info(record)

_LOG_F_FORMATTER = logging.Formatter(_LOG_FORMAT)
_LOG_F_HANDLER.setFormatter(_LOG_F_FORMATTER)

