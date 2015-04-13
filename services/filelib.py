import csv
import os
import time
import logging
from subprocess import call

logger = logging.getLogger(__name__)


class FileService(object):
    'Contains helpful functions related to working with files'

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s %(message)s')

    def ensure_dir(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def get_basename(self, path):
        return os.path.basename(path)

    def get_first_and_last_column(filename, separator):
        with file(filename, 'rb') as file_obj:
            for line in csv.reader(file_obj,
                delimiter=separator,    # Your custom delimiter.
                skipinitialspace=True): # Strips whitespace after delimiter.
                if line: # Make sure there's at least one entry.
                    yield line[0], line[-1]

    # useful for building novus load files
    def jar_files_in_dir(self, directory):
        for f in os.listdir(directory):
            if f.endswith(".gz"):
                no_ext=f[:-3]
                new_filename=no_ext+".jar"
                call('jar cvfM {} {}'.format(new_filename, f), shell=True)

    def write_to_file(self, filename, text):
        logger.info("Writing the file: "+filename)
        file = open(filename, "w")
        for line in text:
            file.write(line+"\n")
        file.write("\n")
        file.close()

    def write_raw_text_to_file(self, filename, text):
        logger.info("Writing the file: "+filename)
        file = open(filename, "w")
        for line in text:
            file.write(line)
        file.close()

    def read_a_file(self, filename):
        logger.info("Reading the file: "+filename)
        file = open(filename, 'r')
        for line in file:
            logger.debug(line)

    def create_email_file(self, filename, msg_subject, msg_body):
        logger.info("Creating an email file ")
        # subject format: time subject from_server_info
        subject = 'subject: {} {} {}'.format(time.asctime(), msg_subject.upper(), "orangeshovel")
        text=[]
        text.append(subject)
        for line in msg_body:
            text.append(line)
        self.write_to_file(filename,text)

    def send_email_file(self, emailfile, to_email_address):
        logger.info("Send email message to: "+to_email_address)
        call('sendmail -v {} < {}'.format(to_email_address, emailfile), shell=True)