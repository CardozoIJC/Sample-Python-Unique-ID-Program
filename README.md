# A-Number Processing (Python+Pandas)

`a_number_processing.py` is a single file Python program for replacing A-numbers in Excel documents with UIDs. This program depends on the Pandas library (https://pandas.pydata.org/) for the import, manipulation, and export of Excel documents.  This program has been tested using Python 3.10.8, and you can see `requirements.txt` for a full list of dependencies.

## Usage:

This Python program contains only a single file, and its usage can be queried using the following command,

`python ./a_number_processing.py --help`

The intended workflow for processing Excel documents is to:
1. At the command-line, use this program to convert the A-numbers in an Excel document to UIDs, for example:

`python ./a_number_processing --files filepath_A:col_A1,col_A2 filepath_B:col_B1 ...`

## Design:

The program is able to consistently able to replace A-Numbers across multiple files in one go. Optionally, it has the ability to replaces A-Numbers across multiple files over the course of more than one use of the program, by providing functionality to save and load the internal A-Number to Unique ID map that is created/used during program executation. To enable this feature, one simply has to provide a location of where they want to save and load from. If during loading the file cannot be found (which is the case when using the feature for the first time, then the program starts with an empty A-Number to Unique ID map).

`python ./a_number_processing --files filepath_A:col_A1,col_A2 filepath_B:col_B1 ... --serialization_path /location/to/store/a-number-to-uid-map.zlib`
