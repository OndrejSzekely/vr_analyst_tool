import argparse
import json

def prepareArgsParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf_file', nargs=1, help="JSON file configuration.")
    parser.add_argument('--output_writer', nargs=1, help="Output writer type", default=["console"], choices=["console", "file"])
    return parser

def prepareArgsParserWithNoConf():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_writer', nargs=1, help="Output writer type", default=["console"],
                        choices=["console", "file"])
    return parser

def getArgValues(args):
    conFile = args.conf_file
    if (conFile != None):
        with open(conFile[0]) as file:
            return json.load(file)