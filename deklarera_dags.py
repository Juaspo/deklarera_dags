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
import re


#logging.getLogger().setLevel(logging_level)

g_DATETIME = None
g_GENERAL_CFG = {}
g_EXAMPLE_CSV = """TAX YEAR,FILE_CLOSING_DATE,CLOSE_DATE,OPENING_TRANSACTION,OPEN_DATE,UNDERLYING_SYMBOL,SECURITY_DESCRIPTION,QUANTITY,PROCEEDS,COST,CODE,GAIN_LOSS_ADJ,TERM,8949_BOX,GAIN_LOSS,CLOSING_TRANSACTION
2020,05/13/21,12/02/20,BTO,11/27/20,PLTR,CALL PLTR   02/19/21    33,1,$00000239.84,$00000946.14, , ,S,B,-$00000706.30,STC
2020,05/13/21,12/02/20,BTO,11/27/20,PLTR,CALL PLTR   03/19/21    35,1,$00000231.84,$00001051.14, , ,S,B,-$00000819.30,STC
2020,05/13/21,12/02/20,BTO,11/27/20,PLTR,CALL PLTR   03/19/21    35,1,$00000231.84,$00001051.13, , ,S,B,-$00000819.29,STC
2020,05/13/21,12/17/20,BTO,11/23/20,LOGI,CALL LOGI   12/18/20    95,1,$00000026.84,$00000046.14, , ,S,B,-$00000019.30,STC
2020,05/13/21,12/02/20,BTO,12/02/20,TSLA,PUT  TSLA   12/18/20   555,1,$00003899.77,$00003841.14, , ,S,B,$00000058.63,STC
"""


@click.command()
@click.option('-c', '--cfg_file', 'cfg_file', default='cfg_deklarera_dags.yml', help='path to config file to us. Defailt is cfg_declare_tax.yml')
@click.option('-l', '--logging_level', 'logging_level', default='INFO', help='set logging severity DEBUG INFO WARNING ERROR CRITICAL. Default INFO')
@click.option('-i', '--input', 'ifile_path', help='input file for parsing')
@click.option('-o', '--output', 'ofile_path', help='set generated file destination. Default ./')


def main(cfg_file: str, logging_level: str, ifile_path: str, ofile_path: str) -> int:

    global g_EXAMPLE_CSV
    input_str = None

    if not sys.stdin.isatty():
        input_str = ""
        input_stream = sys.stdin
        for line in input_stream:
            input_str = input_str + line

    logger = create_logger(logging_level)
    logger.debug("Piped text: %s", g_EXAMPLE_CSV)

    cfg = get_config(logger, cfg_file)

    if not cfg:
        logger.error("missing config exiting")
        sys.exit(os.EX_CONFIG)

    parsed_content = parse_data(logger, cfg, ifile_name=ifile_path, input_stream=input_str)

    for content in parsed_content:
        if "metadata" in parsed_content[content]:
            write_file(logger, parsed_content[content].get("data", ""),
                    parsed_content[content]["metadata"].get("filename", ""),
                    parsed_content[content]["metadata"].get("file_path", ""),
                    parsed_content[content]["metadata"].get("extension", "txt"))

    return 0

def parse_data(logger: Logger, cfg_content: str, ifile_name=None, input_stream=None) -> dict:
    '''
    Creates file templates based on configuration

    input
        logger: Logger
        cfg_content: dict - yaml config content
        ifile_name: str - input filename
        input_stream: str - input stream content

    return
        dict - file template dicts
    '''

    create_file_data = {}
    separator = " "
    identity = None
    csv_list = []
    date_time = ""
    persnr = ""
    presign = ""
    blanketter_dict = None
    

    for config_group in cfg_content:
        logger.debug("config_groups: %s", config_group)

        for post in cfg_content[config_group]:
            logger.debug("post: %s", post)
            if post == "create_file":
                for file_to_create in cfg_content[config_group]['create_file']:
                    data_txt = ""
                    file_cfg = cfg_content[config_group]['create_file'][file_to_create]

                    if file_to_create == "BLANKETTER":
                        blanketter_dict = file_cfg
                    
                    # Check in config if trigger exists otherwise run anyways
                    if file_cfg.get("trigger", True):
                        create_file_data[file_to_create] = {}
                        # Handle metadata from yaml file
                        if "metadata" in file_cfg:
                            create_file_data[file_to_create]["metadata"] = file_cfg["metadata"]
                            separator = file_cfg["metadata"].get("separator", " ")
                            presign = file_cfg["metadata"].get("presign", "**")
                            identity = file_cfg["metadata"].get("identity")

                        # Handle data in yaml config file
                        if "data" in file_cfg:
                            for data_entry in file_cfg["data"]:
                                logger.debug("data_entry: %s", data_entry)
                                value = ""
                                if file_cfg["data"][data_entry]:
                                    # data should be put under "value" key in yaml
                                    value = str(file_cfg["data"][data_entry].get("value", ""))

                                    # Special case handling of data value keys
                                    date_value = file_cfg["data"][data_entry].get("datetime")
                                    if data_entry == "ORGNR":
                                        persnr = value
                                    if (date_value):
                                        date_time = get_datetime(date_value)
                                        value = date_time

                                if value == "" or value is None:
                                    data_txt = data_txt + presign + data_entry + "\n"
                                else:
                                    data_txt = data_txt + presign + data_entry + separator + value +"\n"
                            create_file_data[file_to_create]["data"] = data_txt

                        logger.debug("create_file_data: %s", create_file_data)
                        logger.debug("data_txt: %s", data_txt)

                        # Handle parsing of data from input stream
                        if file_cfg.get("parse_data"):
                            for parse_name in file_cfg["parse_data"]:
                                if parse_name == "config":
                                    csv_delimiter = file_cfg["parse_data"][parse_name].get("delimiter", ",")
                                    #csv_quotechar = file_cfg["parse_data"][parse_name].get("quotechar", "|")

                                    if ifile_name:
                                        csv_list = csv_handler(logger, filename=ifile_name, csv_delimiter=csv_delimiter)
                                    elif input_stream:
                                        csv_list = csv_handler(logger, csv_string=input_stream, csv_delimiter=csv_delimiter)

                                else:
                                    if identity:
                                        blanketter_dict["identity"] = persnr + " " + date_time
                                    blanketter_dict["entryname"] = parse_name
                                    create_file_data["BLANKETTER"]["data"] = create_blankett(logger, csv_list, blanketter_dict)


    return create_file_data

def create_blankett(logger: Logger, csv_list: list, blankett_cfg: dict) -> str:
    '''
    Specific function to handle blankett output.

    input
        logger: Logger
        blankett_cfg: dict - configurations for how to create blankett file

    return
        str - text result of blanketter
    '''

    key_string = ""
    blankett_template = {"amount": 0,
                         "stock": 1,
                         "sell": 2,
                         "cost": 3,
                         "gain": 4,
                         "loss": 5,
                         "sum_sell": 3300,
                         "sum_cost": 3301,
                         "section": 7014
                        }
    format_to_number = ["sell", "cost"]
    entry_template={}
    txt = ""
    separator = " "
    start_number = 3100
    end_number = 3185 # highest entry id allowed
    entry_inc = 10 # increment entry id by this much for each new entry
    exchange_rate = None
    value_extraction = None # regular expression to extract value from csv
    total_sell_sum = 0
    total_cost_sum = 0
    sell_sum = 0
    cost_sum = 0
    presign = ""
    topinfo = ""
    entry_name = None
    blankett = None

    if blankett_cfg is None:
        logger.error("No blankett configuration found!")
        return None

    logger.debug("blankett cfg: %s", blankett_cfg)


    # prepare data for parsing
    if blankett_cfg.get("parse_data"):
        for entry_group in blankett_cfg["parse_data"]:
            if entry_group == "config":
                exchange_rate = blankett_cfg["parse_data"][entry_group].get("exchange_rate", None)
                round_number = blankett_cfg["parse_data"][entry_group].get("round_value", None)
                value_extraction = blankett_cfg["parse_data"][entry_group].get("value_extraction", None)
                if value_extraction:
                    value_extraction = re.compile(value_extraction)

            elif entry_group:
                for entry in blankett_cfg["parse_data"][entry_group]['parse']:
                    key_string = blankett_cfg["parse_data"][entry_group]['parse'][entry]
                    #logger.debug("key string: %s", key_string)
                    for column in csv_list[0]:
                        #logger.debug("csv column: %s", column)
                        if column == key_string:
                            pos = csv_list[0].index(column)
                            entry_template[pos] = blankett_template[entry]
                            logger.debug("%s is %s on %s", entry, column, pos)
    else:
        logger.error("No parse_data configuration found!")
        return None

    # set configuration for blanketter
    if blankett_cfg.get("metadata"):
        presign = blankett_cfg["metadata"].get("presign")
        separator = blankett_cfg["metadata"].get("separator", " ")
        blankett = blankett_cfg["metadata"].get("blankett")
        pers_name = blankett_cfg["metadata"].get("name")

    entry_name = blankett_cfg.get("entryname")
    entry_name = presign + entry_name if entry_name else ""

    # Create information shown at top of Blankett
    if blankett:
        prev_year = int(get_datetime("%Y"))-1
        blankett = presign + "BLANKETT" + separator + blankett + "-" + str(prev_year) + "P4\n"
        topinfo = topinfo + blankett
    identity = blankett_cfg.get("identity", "")
    if identity:
        topinfo = topinfo + presign + "IDENTITET" + separator + identity + "\n"
    if pers_name:
        pers_name = presign + "NAMN" + separator + pers_name + "\n"
        topinfo = topinfo + pers_name

    # do actual parsing and formatting of text
    count = 0

    for i, x in enumerate(format_to_number):
        format_to_number[i] = blankett_template[x]

    newfile = True
    nr_code = start_number
    section_count = 0
    for row in csv_list:
        if count > 0:
            sell = 0
            cost = 0

            if newfile:
                txt = txt + topinfo
                section_count += 1
                sell_sum = cost_sum = 0
                newfile = False

            for column in entry_template:
                id_num = entry_template[column]
                value = row[column]
                if entry_template[column] in format_to_number and value_extraction:
                    regex_match =  re.search(value_extraction, value).group()
                    value = float(regex_match)
                    if exchange_rate:
                        value = value * exchange_rate
                    if round_number is not None:
                        if round_number == 0:
                            value = round(value)
                        else:
                            value = round(value, round_number)

                    if id_num == 2: sell = value
                    elif id_num == 3: cost = value

                entry_id = nr_code + id_num
                txt = txt + entry_name + separator + str(entry_id) + separator + str(value) + "\n"
                #logger.debug("column: %s, value: %s, nr code: %s", column, value, nr_code)

            # calculate and add gain or loss entry
            gain_loss = sell - cost
            sell_sum += sell
            cost_sum += cost
            if gain_loss > 0:
                entry_id = nr_code + blankett_template["gain"]
                txt = txt + entry_name + separator + str(entry_id) + separator + str(gain_loss) + "\n"
            else:
                entry_id = nr_code + blankett_template["loss"]
                txt = txt + entry_name + separator + str(entry_id) + separator + str(abs(gain_loss)) + "\n"
            nr_code = nr_code + entry_inc

        count = count + 1
        if nr_code >= end_number:
            txt = txt + entry_name + separator + str(blankett_template["sum_sell"]) + separator + str(sell_sum) + "\n"
            txt = txt + entry_name + separator + str(blankett_template["sum_cost"]) + separator + str(cost_sum) + "\n"
            txt = txt + entry_name + separator + str(blankett_template["section"]) + separator + str(section_count) + "\n"
            txt = txt + presign + "BLANKETTSLUT" + "\n"
            total_sell_sum += sell_sum
            total_cost_sum += cost_sum
            
            nr_code = start_number
            newfile = True

    txt = txt + presign + "FIL_SLUT"

    sum = total_sell_sum - total_cost_sum
    logger.info("stats for ya:\nTotal sell: %s\nTotal cost: %s\nTotal Sum:  %s", total_sell_sum, total_cost_sum, sum)
    #print(txt)
    #logger.debug("entry template used: %s", entry_template)
    return txt


def csv_handler(logger: Logger, filename: str=None, csv_string=None, csv_delimiter = ',', csv_quotechar = '|'):
    '''
    Converts CSV input to list matrix data
    Takes in either CSV text in string format or filepath
    to a CSV file.

    input
        logger: Logger
        filename: str - filepath of CSV file
        csv_string: str - CSV text in string format
        csv_delimiter: str - CSV column separator
        csv_quotechar: str - CSV quote char
    
    return
        list - a list in list matrix

    '''
    csv_list = []

    if filename:
        with open(filename, newline='') as csvfile:
            csv_content = csv.reader(csvfile, delimiter=csv_delimiter, quotechar=csv_quotechar)
            for row in csv_content:
                csv_list.append(row)
        #logger.debug("returning csv list: %s", csv_list)
        return csv_list

    elif csv_string:
        csv_lines = csv_string.splitlines()
        for line in csv_lines:
            csv_row = line.split(csv_delimiter)
            csv_list.append(csv_row)
        #logger.debug("returning csv list: %s", csv_list)
        return csv_list
    else:
        logger.error("No filename or csv string provided")
        return None

def get_datetime(date_format: str=None) -> datetime:
    '''
    Fetch date and time and return value depending on
    format argument

    input:
        logger: Logger
        date_time: str - String of datetime format code
    return:
        datetime: str
    '''

    global g_DATETIME

    if g_DATETIME is None:
        g_DATETIME = datetime.today()
    
    if date_format:
        return g_DATETIME.strftime(date_format)

    return None

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
            logger.debug("yaml content: %s", cfg)
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
    logger.debug("Content to write: %s", content_str)

    f = open(file_path, 'w')
    f.write(str(content_str))
    f.close()
    logger.info("Created file: %s", file_path)

if __name__ == "__main__":
    exit_code = 0
    #try:
    exit_code = main()
    #except Exception as e:
    #    print(f"Exiting with error {e}...", file=sys.stderr)
    sys.exit(exit_code)
