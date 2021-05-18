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

@click.command()
@click.option('-c', '--cfg_file', 'cfg_file', default='cfg_deklarera_dags.yml', help='path to config file to us. Defailt is cfg_declare_tax.yml')
@click.option('-l', '--logging_level', 'logging_level', default='INFO', help='set logging severity DEBUG INFO WARNING ERROR CRITICAL. Default INFO')


def main(cfg_file: str, logging_level: str) -> int:

    logger = create_logger(logging_level)

    logger.debug("testing debug")
    logger.info("testing info")
    logger.error("testing error")
    logger.critical("testing critical")

    cfg = get_config(logger, cfg_file)

    if not cfg:
        logger.error("missing config exiting")
        sys.exit(os.EX_CONFIG)

    logger.info("printing cfg content")
    print(cfg)


    return 0

def create_logger(logging_level: str) -> Logger:
    '''
    Set up logger for this script
    input:
        logging_level :string
    return:
        Logger :object
    '''

    #logging.basicConfig(level=getattr(logging, logging_level.upper(), 10))
    
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_level.upper(), 10))
    
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',  datefmt='%Y-%m-%d:%H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger    


def get_config(logger: Logger, cfg_file: str) -> str:
    '''
    Fetch YAML configuration
    reads and returns YAML configuration
    input:
        cfg_file :str
    return:
        str
    '''
    try:
        with open(cfg_file, 'r') as file:
            cfg = yaml.safe_load(file)
            return cfg
    except yaml.YAMLError as e:
        logger.error(f"YAML file error: {e}")
    except FileNotFoundError as e:
        logger.error(f"config file error: {e}")
    return False


if __name__ == "__main__":
    exit_code = 0
    try:
        exit_code = main()
    except Exception as e:
        print(f"Exiting with error {e}...", file=sys.stderr)
    sys.exit(exit_code)
    