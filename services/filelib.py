import csv
import os
import time
import logging
import traceback
from subprocess import call
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import xml.etree.cElementTree as ET
from xml.dom import minidom # used for pretty printing


logger = logging.getLogger(__name__)


class FileService(object):
    """Contains helpful functions related to working with files"""

    def __init__(self):
        logger.debug("Creating the FileService")

    @staticmethod
    def ensure_dir(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def get_basename(path):
        return os.path.basename(path)

    @staticmethod
    def get_first_and_last_column(filename, separator):
        with file(filename, 'rb') as file_obj:
            for line in csv.reader(file_obj,
                delimiter=separator,    # Your custom delimiter.
                skipinitialspace=True): # Strips whitespace after delimiter.
                if line: # Make sure there's at least one entry.
                    yield line[0], line[-1]

    # useful for building novus load files
    @staticmethod
    def jar_files_in_dir(directory):
        for f in os.listdir(directory):
            if f.endswith(".gz"):
                no_ext=f[:-3]
                new_filename=no_ext+".jar"
                call('jar cvfM {} {}'.format(new_filename, f), shell=True)

    @staticmethod
    def write_to_file(filename, text):
        logger.info("Writing the file: "+filename)
        file = open(filename, "w")
        for line in text:
            file.write(line+"\n")
        file.write("\n")
        file.close()

    @staticmethod
    def write_raw_text_to_file(filename, text):
        logger.info("Writing the file: "+filename)
        file = open(filename, "w")
        for line in text:
            file.write(line)
        file.close()

    @staticmethod
    def read_a_file(filename):
        logger.info("Reading the file: "+filename)
        file = open(filename, 'r')
        for line in file:
            logger.debug(line)


class XmlService(object):

    def __init__(self):
        logger.debug("Creating the XmlService")

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString('<root>'+rough_string+'</root>')
        return reparsed.toprettyxml(indent="\t")

    def find_in_tree(self, tree, node):
        found = tree.find(node)
        if found == None:
            print "No %s in file" % node
            found = []
        return found

    def write_out_to_xml(self, root, output_file):
        #root = ET.Element("root")
        fs = FileService()
        fs.write_raw_text_to_file(output_file, root)

    def evaluate_xpath(self, root, xpath):
        return root.findall(xpath)

    def get_text(self, root):
        for page in list(root):
            title = page.find('title').text
            content = page.find('content').text
            print('title: %s; content: %s' % (title, content))


class EmailService(object):
    """Contains helpful functions related to working with emails"""

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s %(message)s')
        self.fs = FileService()
        logger.info("Init for EmailService")

    def create_text_email(self, filename, msg_subject, msg_body):
        logger.info("Creating a plain text email file. ")
        # subject format: time subject from_server_info
        subject = 'subject: {} {} {}'.format(time.asctime(), msg_subject.upper(), "orangeshovel")
        text = []
        text.append(subject)
        for line in msg_body:
            text.append(line)
        self.fs.write_to_file(filename, text)

    def build_html_email(self, from_email, to_email, subject, text, html, images, output_email_file):
        logger.info("Creating an html email file. ")
        # Create message container - the correct MIME type is multipart/alternative.
        msg_root = MIMEMultipart('alternative')
        msg_root['Subject'] = subject.encode('utf-8')
        msg_root['From'] = from_email.encode('utf-8')
        msg_root['To'] = to_email.encode('utf-8')

        # Record the MIME types of both parts - text/plain and text/html.
        plain_text = MIMEText(text.encode('utf-8'), 'plain')
        html_text = MIMEText(html.encode('utf-8'), 'html')
        logger.info("Added headers. ")

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg_root.attach(plain_text)
        msg_root.attach(html_text)
        logger.info("Added body. ")

        for image_id in images:
            logger.info("Added image: {} ".format(image_id))
            # This example assumes the image is in the current directory
            image_path = images[image_id]
            try:
                fp = open(image_path, 'rb')
                msg_image = MIMEImage(fp.read())
                fp.close()
            except:
                logger.error("Could not attach image file {}".format(image_path))
                logger.error(traceback.format_exc())

            # Define the image's ID as referenced above
            msg_image.add_header('Content-ID', '<{}>'.format(image_id))
            msg_root.attach(msg_image)

        self.fs.write_raw_text_to_file(output_email_file, msg_root.as_string())

    @staticmethod
    def send_email_file(email_file, to_email_address):
        logger.info("Send email message to: "+to_email_address)
        call('sendmail -v {} < {}'.format(to_email_address, email_file), shell=True)
