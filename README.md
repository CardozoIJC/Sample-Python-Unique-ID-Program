# A-Number Processing (Python+Pandas)

`a_number_processing.py` is a single file Python program for replacing A-numbers in Excel documents with UIDs. This program depends on the Pandas library (https://pandas.pydata.org/) for the import, manipulation, and export of Excel documents.  This program has been tested using Python 3.10.8, and you can see `requirements.txt` for a full list of dependencies.

## Usage:

This Python program contains only a single file, and its usage can be queried using the following command,

`python ./a_number_processing.py --help`

The intended workflow for processing Excel documents is to:
1. At the command-line, use this program to convert the A-numbers in an Excel document to UIDs, for example:

`python ./a_number_processing /path/to/file_to_process.xlsx -s /path/to/a_number_to_uid.json -cn 0 2`

## Design:

To be able be able to consistently replace A-numbers across multiple files, the program loads on start-up, and saves on successful termination a dictionary from A-numbers to UID which it updates during running. The location and name of this file can be provided at program invokation. If the file is not present, then a program creates a new empty dictionary at start-up. This file is saved in the human-readable format JSON.
