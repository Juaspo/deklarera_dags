#!/usr/bin/env python3

__all__     = []
__version__ = 0.1
__date__    = "2021-05-18"
__author__  = "juaspo"
__status__  = "development"


import sys
import yaml
import click
import logging
from logging import Logger
import os
from datetime import datetime
import csv


#logging.getLogger().setLevel(logging_level)

g_GENERAL_CFG = {}
g_EXAMPLE_CSV = """TAX YEAR,FILE_CLOSING_DATE,CLOSE_DATE,OPENING_TRANSACTION,OPEN_DATE,UNDERLYING_SYMBOL,SECURITY_DESCRIPTION,QUANTITY,PROCEEDS,COST,CODE,GAIN_LOSS_ADJ,TERM,8949_BOX,GAIN_LOSS,CLOSING_TRANSACTION
2020,05/13/21,12/02/20,BTO,11/27/20,PLTR,CALL PLTR   02/19/21    33,1,$00000239.84,$00000946.14, , ,S,B,-$00000706.30,STC
2020,05/13/21,12/02/20,BTO,11/27/20,PLTR,CALL PLTR   03/19/21    35,1,$00000231.84,$00001051.14, , ,S,B,-$00000819.30,STC
2020,05/13/21,12/02/20,BTO,11/27/20,PLTR,CALL PLTR   03/19/21    35,1,$00000231.84,$00001051.13, , ,S,B,-$00000819.29,STC
2020,05/13/21,12/17/20,BTO,11/23/20,LOGI,CALL LOGI   12/18/20    95,1,$00000026.84,$00000046.14, , ,S,B,-$00000019.30,STC
2020,05/13/21,12/02/20,BTO,12/02/20,TSLA,PUT  TSLA   12/18/20   555,1,$00003899.77,$00003841.14, , ,S,B,$00000058.63,STC
"""

g_BLANKETT_DATA = {
    "antal": 0,
    "aktie": 1,
    "sell": 2,
    "cost": 3
}

@click.command()
@click.option('-c', '--cfg_file', 'cfg_file', default='cfg_deklarera_dags.yml', help='path to config file to us. Defailt is cfg_declare_tax.yml')
@click.option('-l', '--logging_level', 'logging_level', default='INFO', help='set logging severity DEBUG INFO WARNING ERROR CRITICAL. Default INFO')
@click.option('-i', '--input', 'ifile_path', help='input file for parsing')
@click.option('-o', '--output', 'ofile_path', help='set generated file destination. Default ./')


def main(cfg_file: str, logging_level: str, ifile_path: str, ofile_path: str) -> int:

    global g_EXAMPLE_CSV

    if not sys.stdin.isatty():
        global g_EXAMPLE_CSV
        g_EXAMPLE_CSV = ""
        input_stream = sys.stdin
        for line in input_stream:
            g_EXAMPLE_CSV = g_EXAMPLE_CSV + line

    logger = create_logger(logging_level)
    logger.debug("Piped text: %s", g_EXAMPLE_CSV)

    cfg = get_config(logger, cfg_file)
    if not cfg:
        logger.error("missing config exiting")
        sys.exit(os.EX_CONFIG)
    #logger.info("printing cfg content")

    parsed_content = parse_data(logger, cfg, ifile_name=ifile_path, input_stream=g_EXAMPLE_CSV)

    for content in parsed_content:
        if "metadata" in parsed_content[content]:
            write_file(logger, parsed_content[content].get("data", ""),
                    parsed_content[content]["metadata"].get("filename", ""),
                    parsed_content[content]["metadata"].get("file_path", ""),
                    parsed_content[content]["metadata"].get("extension", "txt"))

    #write_file(logger, g_EXAMPLE_CSV, "csv", ofile_path, "txt")

    return 0

def parse_data(logger: Logger, cfg_groups: str, ifile_name=None, input_stream=None) -> str:
    '''
    Takes input data 
    '''
    create_file_data = {}
    separator = " "
    identiet = ""
    csv_list = []
    

    for config_group in cfg_groups:
        logger.debug("config_groups: %s", config_group)

        for post in cfg_groups[config_group]:
            logger.debug("post: %s", post)
            if post == "create_file":
                for file_to_create in cfg_groups[config_group]['create_file']:
                    data_txt = ""
                    file_cfg = cfg_groups[config_group]['create_file'][file_to_create]
                    logger.debug("file_cfg: %s", file_cfg)
                    logger.debug("file_to_create: %s", file_to_create)
                    create_file_data[file_to_create] = {}
                    
                    # Check in config if trigger exists otherwise run anyways
                    if file_cfg.get("trigger", True):
                        # Handle metadata from yaml file
                        if "metadata" in file_cfg:
                            create_file_data[file_to_create]["metadata"] = file_cfg["metadata"]
                            separator = file_cfg["metadata"].get("separator", " ")

                        # Handle data in yaml config file
                        if "data" in file_cfg:
                            for data_entry in file_cfg["data"]:
                                logger.debug("data_entry: %s", data_entry)
                                value = ""
                                if file_cfg["data"][data_entry]:
                                    value = str(file_cfg["data"][data_entry].get("value", ""))
                                    date_value = file_cfg["data"][data_entry].get("datetime")
                                    if value == "ORGNR":
                                        identiet = value

                                    if (date_value):
                                        value = get_datetime(logger, date_value)
                                        identiet = identiet + " " + value

                                if value == "":
                                    data_txt = data_txt + data_entry + "\n"
                                else:
                                    data_txt = data_txt + data_entry + separator + value +"\n"
                            create_file_data[file_to_create]["data"] = data_txt

                        logger.info("create_file_data: %s", create_file_data)
                        logger.debug("data_txt: %s", data_txt)

                        # Handle parsing of data from input stream
                        if "parse_data" in file_cfg:
                            for parse_name in file_cfg["parse_data"]:
                                if parse_name == "config":
                                    csv_delimiter = file_cfg["parse_data"][parse_name].get("delimiter", ",")
                                    csv_quotechar = file_cfg["parse_data"][parse_name].get("quotechar", "|")
                                    
                                    if ifile_name:
                                        csv_list = csv_handler(logger, filename=ifile_name, csv_delimiter=csv_delimiter)
                                    elif input_stream:
                                        csv_list = csv_handler(logger, csv_string=input_stream, csv_delimiter=csv_delimiter)

                                    
                                else:
                                    for parse_entry_value in file_cfg["parse_data"][parse_name]:
                                        logger.debug("parse_entry: %s", parse_entry_value)
                                        
                                        #continue with parsing of data values


    return create_file_data

def csv_handler(logger: Logger, filename = None, csv_string=None, csv_delimiter = ',', csv_quotechar = '|'):
    '''
    TODO write info

    '''
    csv_list = []


    if filename:
        with open(filename, newline='') as csvfile:
            csv_content = csv.reader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            for row in csv_content:
                csv_list.append(row)
        logger.debug("returning csv list: %s", csv_list)
        return csv_list

    elif csv_string:
        csv_lines = csv_string.splitlines()
        for line in csv_lines:
            csv_row = line.split(csv_delimiter)
            csv_list.append(csv_row)
        logger.debug("returning csv list: %s", csv_list)
        return csv_list
    else:
        logger.error("No filename or csv string provided")
        return None

def get_datetime(logger: Logger, date_format: str) -> datetime:
    '''
    Fetch date and time and return value depending on
    format argument

    input:
        logger: Logger
        date_time: str - String of datetime format code
    return:
        datetime: str
    '''

    date_now = datetime.today().strftime(date_format)
    #logger.debug("date format: %s, converted to date: %s", date_format, date_now)
    return date_now

def create_logger(logging_level: str) -> Logger:
    '''
    Set up logger for this script
    input:
        logging_level :string
    return:
        logger :Logger
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_level.upper(), 10))
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',  datefmt='%Y-%m-%d:%H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger

def get_config(logger: Logger, cfg_file: str) -> dict:
    '''
    Fetch YAML configuration
    reads and returns YAML configuration
    input:
        cfg_file :str
    return:
        dict
    '''
    try:
        with open(cfg_file, 'r') as file:
            cfg = yaml.safe_load(file)
            #global g_GENERAL_CFG = cfg["general"]
            return cfg["config_groups"]
    except yaml.YAMLError as e:
        logger.error(f"YAML file error: {e}")
    except FileNotFoundError as e:
        logger.error(f"config file error: {e}")
    return False

def write_file(logger: Logger, content_str: str, file_name: str, file_path="", file_extension=""):
    '''
    Formats the filepath and filename for writing file
    input:
        logger: Logger
        content_str: str - Content to write to file
        file_name: str - Name of file without path
        file_path: str - Path of file without filename
        file_extension: str - file extension (without dot)
    return:
        -
    '''
    
    if not file_path:
        file_path = ""

    file_path = os.path.join(file_path, file_name + "." + file_extension)
    logger.info("Creating file: %s", file_path)
    #logger.debug("Content to write: %s", content_str)

    f = open(file_path, 'w')
    f.write(str(content_str))
    f.close()

if __name__ == "__main__":
    exit_code = 0
    #try:
    exit_code = main()
    #except Exception as e:
    #    print(f"Exiting with error {e}...", file=sys.stderr)
    sys.exit(exit_code)
