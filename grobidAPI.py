# -*- coding: utf-8 -*-
import os
import requests
import codecs
import logging
from datetime import datetime
import time
#
import settings
import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class GrobidError(Exception): pass

class ConnectionError(Exception): pass

def get_data_from_grobid(command, pdf_file, using_TOR = False):
    """ Send post request to grobid and returned data """
    return utils.get_request("{}{}".format(settings.GROBID_SERVER, command), {'input': pdf_file}, using_TOR)