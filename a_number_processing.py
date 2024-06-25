from copy import copy
import argparse
import re
import json
import pathlib
import pandas as pd
import zlib

A_NUMBER_PATTERN = r'[aA]?((?<=[aA])[-\t ])?#?((?<=#)[-\t ])?[0-9]{2,3}[- ]?[0-9]{3}[- ]?[0-9]{3}\b'
A_NUMBER_PATTERN_SIMPLE = r'[0-9]{2,3}[- ]?[0-9]{3}[- ]?[0-9]{3}\b'
A_NUMBER_REGEX = re.compile(A_NUMBER_PATTERN)
MODIFIED_FILE_SUFFIX = '_redacted'
COMPRESSED_SERIALIZATION = True
REPLACEMENT_UID_PREFIX = 'UID-'
READ_ALL_SHEETS = None
ALL_COLUMN_NUMBERS = slice(None)

class UIDGenerator:
    def __init__(self, current_largest_uid = -1):
        self.next_uid = current_largest_uid + 1
    
    def get_next_uid(self):
        next_uid = copy(self.next_uid)
        self.next_uid += 1
        return next_uid

def load_a_number_to_uid_map(serialization_path):
    try:
        if COMPRESSED_SERIALIZATION:
            with open(serialization_path, 'rb') as f:
                compressed_data = f.read()
            json_bytes = zlib.decompress(compressed_data)
            a_number_to_uid = json.loads(json_bytes.decode('utf-8'))
        else:
            with open(serialization_path, 'r') as f:
                a_number_to_uid = json.load(f)
        return a_number_to_uid
    except FileNotFoundError:
        print(f"Couldn't open serialization file, {serialization_path}. Creating a new a-number to UID map.")
        return {}

def save_a_number_to_uid_map(serialization_path, a_number_to_uid):
    if COMPRESSED_SERIALIZATION:
        json_bytes = json.dumps(a_number_to_uid).encode('utf-8')
        compressed_data = zlib.compress(json_bytes)
        with open(serialization_path, 'wb') as f:
            f.write(compressed_data)
    else:
        with open(serialization_path, 'w') as f:
            json.dump(a_number_to_uid, f)

def canonicalize(a_number):
    result = a_number.lower()
    result = re.sub(r'[a\-# ]', '', result)
    if len(result) == 8:
        result = '0' + result
    return result

def replace_text_a_numbers(a_number_to_uid, uid_generator, text):
    def replace(raw_match):
        a_number = canonicalize(raw_match.group(0))
        assert(len(a_number) == 9)
        if a_number not in a_number_to_uid:
            a_number_to_uid[a_number] = uid_generator.get_next_uid()
        return REPLACEMENT_UID_PREFIX + str(a_number_to_uid[a_number])

    return A_NUMBER_REGEX.sub(replace, text)

def replace_number_a_numbers(a_number_to_uid, uid_generator, number):
    if 0 <= number and number <= 999999999:
        a_number = str(number).zfill(9)
        if a_number not in a_number_to_uid:
            a_number_to_uid[a_number] = uid_generator.get_next_uid()
        return a_number_to_uid[a_number]
    else:
        return number;

def replace_document_a_numbers(a_number_to_uid, uid_generator, input_file_path, selected_column_numbers):
    input_file_extension = input_file_path.suffix
    output_file_path = f"{input_file_path.stem}{MODIFIED_FILE_SUFFIX}{input_file_extension}"

    if input_file_extension == '.xlsx':
        sheets = pd.read_excel(input_file_path, sheet_name=READ_ALL_SHEETS, header=None)
        
        for (sheet_name, sheet) in sheets.items():

            columns_to_select = ALL_COLUMN_NUMBERS if not selected_column_numbers else selected_column_numbers
            selected_columns = sheet.loc[:, columns_to_select]

            for (column_name, column_data) in selected_columns.items():
                for (row_number, cell_contents) in column_data.items():
                    if isinstance(cell_contents, str):
                        sheet.at[row_number, column_name] = replace_text_a_numbers(a_number_to_uid, uid_generator,
                                                                                   cell_contents)
                    if isinstance(cell_contents, int):
                        sheet.at[row_number, column_name] = replace_number_a_numbers(a_number_to_uid, uid_generator,
                                                                                     cell_contents)
        
        with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
            for (sheet_name, sheet) in sheets.items():
                sheet.to_excel(writer, sheet_name=sheet_name, index=False, header=None)
        
    else:
        print(f"ERROR: file format, \'{input_file_extension}\', is not supported.")

class ParseFileColumns(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        files = {}
        for value in values:
            filepath_and_columns = value.split(':')
            assert(len(filepath_and_columns) == 1 or len(filepath_and_columns) == 2)
            filepath = pathlib.Path(filepath_and_columns[0])
            columns = []
            if len(filepath_and_columns) == 2:
                columns = filepath_and_columns[1]
                columns = columns.split(',')
            files[filepath] = [int(column) for column in columns if column != '']
        setattr(namespace, self.dest, files)

def main():
    parser = argparse.ArgumentParser(prog='a_number_processing',
                                     description='Replaces A-numbers with UIDs.')
    parser.add_argument('-s', '--serialization_path', type=pathlib.Path, default=None,
                        help=f'The file path to load/save the a-number-to-uid map, '\
                             f'if no path is provided then no file is saved.')
    parser.add_argument('-f', '--files', nargs='+', action=ParseFileColumns,
                        help='Provide a list of the xlsx files to process. For each file the default behaviour '\
                             'is to process all columns, however, on a per file basis one can optionally identify '\
                             'the specfic columns to process using the format, \'filepath:col1,col2,...\' where'\
                             'col1, col2, etc are integers.'\
                             'Example: --files filepath1:col1 filepath2:col2,col3 ...')
    args = parser.parse_args()

    if args.serialization_path is not None:
        a_number_to_uid = load_a_number_to_uid_map(args.serialization_path)
    else:
        a_number_to_uid = {}

    current_largest_uid = -1 if not a_number_to_uid else max(a_number_to_uid.values())
    uid_generator = UIDGenerator(current_largest_uid)

    for file_to_process, column_numbers in args.files.items():
        replace_document_a_numbers(a_number_to_uid, uid_generator, file_to_process, column_numbers)

    if args.serialization_path is not None:
        save_a_number_to_uid_map(args.serialization_path, a_number_to_uid)

if __name__ == "__main__":
    main()
