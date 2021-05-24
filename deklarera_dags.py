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


#logging.getLogger().setLevel(logging_level)

g_GENERAL_CFG = {}

@click.command()
@click.option('-c', '--cfg_file', 'cfg_file', default='cfg_deklarera_dags.yml', help='path to config file to us. Defailt is cfg_declare_tax.yml')
@click.option('-l', '--logging_level', 'logging_level', default='INFO', help='set logging severity DEBUG INFO WARNING ERROR CRITICAL. Default INFO')
@click.option('-o', '--output', 'file_path', default='./', help='set generated file destination. Default ./')


def main(cfg_file: str, logging_level: str, file_path: str) -> int:

    logger = create_logger(logging_level)

    cfg = get_config(logger, cfg_file)

    if not cfg:
        logger.error("missing config exiting")
        sys.exit(os.EX_CONFIG)

    logger.info("printing cfg content")
    #print(cfg)
    parse_data(logger, cfg)



    write_file(logger, cfg, "INFO", file_path, "txt")


    return 0

def parse_data(logger: Logger, cfg_groups: str) -> str:
    '''
    Takes input data 
    '''
    create_file_data = {}

    for config_group in cfg_groups:
        logger.debug("config_groups: %s", config_group)

        for post in cfg_groups[config_group]:
            logger.debug("post: %s", post)
            if post == "create_file":
                create_file_data[config_group]={}
                for file_to_create in cfg_groups[config_group]['create_file']:
                    file_cfg = cfg_groups[config_group]['create_file'][file_to_create]
                    logger.debug("file_cfg: %s", file_cfg)
                    logger.debug("file_to_create: %s", file_to_create)

                    if "metadata" in file_cfg:
                        create_file_data[config_group][file_to_create] = {}
                        if "extension" in file_cfg:
                            create_file_data[config_group][file_to_create]["file_extension"] = file_cfg["extension"]
                        if "date_format" in file_cfg:
                            create_file_data[config_group][file_to_create]["date_format"] = file_cfg["date_format"]


                    for entry in file_cfg:
                        logger.debug("entry: %s", entry)
                    
    
    logger.debug("create_file_data: %s", create_file_data)



def create_logger(logging_level: str) -> Logger:
    '''
    Set up logger for this script
    input:
        logging_level :string
    return:
        logger :Logger
    '''
    #logging.basicConfig(level=getattr(logging, logging_level.upper(), 10))

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

    file_path = os.path.join(file_path, file_name + "." + file_extension)
    logger.debug("File: %s", file_path)
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
