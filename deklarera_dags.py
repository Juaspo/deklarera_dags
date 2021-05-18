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


#logging.getLogger().setLevel(logging_level)

@click.command()
@click.option('-c', '--cfg_file', 'cfg_file', default='cfg_deklarera_dags.yml', help='path to config file to us. Defailt is cfg_declare_tax.yml')
@click.option('-l', '--logging_level', 'logging_level', default='INFO', help='set logging severity DEBUG INFO WARNING ERROR CRITICAL. Default INFO')


def main(cfg_file: str, logging_level: str):
    
    logging.basicConfig(level=getattr(logging, logging_level.upper(), 10))
    logger = logging.getLogger()

    logger.debug("testing debug")
    logger.info("testing info")
    logger.error("testing error")
    logger.critical("testing critical")

    print("Runing")
    print("following arguments passed:", cfg_file)
    cfg = get_config(cfg_file)

    if not cfg:
        logger.error(f"missing config {cfg_file}")
        return 1
    print(cfg)
    


    return 0


def get_config(cfg_file: str) -> str:
    with open(cfg_file, 'r') as file:
        try:
            cfg = yaml.safe_load(file)
            return cfg
        except yaml.YAMLError as e:
            print(e)
    return False


if __name__ == "__main__":
    exit_code = main()
    