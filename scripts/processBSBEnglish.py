'''Scripts to extract the English Bible contents from the input XLSX/CSV file'''

import re
import pandas as pd
import numpy as np

from utils import book_name_code_map

class ProcessBSBEnglish:
    def __init__(self, filepath, output_folder="bsb_usfms"):
        self.bsb_df = pd.read_csv(filepath, delimiter='\t')
        self.ref_pattern = re.compile(r'(\d? ?[\w ]+) (\d+):(\d+)')
        self.output_folder=output_folder
        self.current_book = ""
        self.current_chapter = ""
        self.current_verse = ""
        self.usfm_str = ""
        self.heb_index = 0
        self.grk_index = 0
        self.bsb_df.apply(lambda row: self.row2usfm(row), axis=1)
        self.save_one_book()

    def row2usfm(self, row):
        verse_start = ""
        if not pd.isna(row['Verse']):
           verse_start = self.process_verse(row)
        if not pd.isna(row['Heading']):
            self.usfm_str += f"\n\\s {row['Heading']}\n\\p\n"
        if verse_start!="":
            self.usfm_str += verse_start
        if not pd.isna(row['Cross References']):
            items = row['Cross References'].replace('(', '').replace(')', '')
            self.usfm_str += f'\\x + \\xo {self.current_chapter}:{self.current_verse}: \\xt {items} \\x* '
        if row['BSB Version'] is not np.NaN:
            self.usfm_str += "\\w "
            self.usfm_str += f"{row['BSB Version']} |"
            if row['Language'] in ["Hebrew", "Aramaic"]:
                bib = "WLC"
                wrd_index = row['Heb Sort'] - self.heb_index + 1
            elif row["Language"] == "Greek":
                bib = "Nestle"
                wrd_index = row['Grk Sort'] - self.grk_index + 1
            if not pd.isna(row['Strongs']):
                self.usfm_str += f"strong=\"{int(row['Strongs'])}\" "
            self.usfm_str += f"srcloc=\"{bib}:{self.current_book}.{self.current_chapter}.{self.current_verse}.{int(wrd_index)}\" "
            self.usfm_str += "\\w* "
    
    def process_verse(self, row):
        ref_match = re.match(self.ref_pattern, row['Verse'])
        ref_book = ref_match.group(1)
        ref_chapter = ref_match.group(2)
        ref_verse = ref_match.group(3)
        print(f"{ref_book=} {ref_chapter=} {ref_verse=}")
        book_code = book_name_code_map[ref_book]
        if book_code != self.current_book:
            self.save_one_book()
            self.current_book = book_code
            self.current_chapter = ref_chapter
            self.usfm_str = f"\\id {book_code} {ref_book} of Berean Study Bible\n\\c {ref_chapter}\n\\p\n"
        elif ref_chapter != self.current_chapter:
            self.usfm_str += f"\n\\c {ref_chapter}\n\\p\n"
            self.current_chapter = ref_chapter
        self.current_verse = ref_verse
        self.heb_index = row['Heb Sort']
        self.grk_index = row['Grk Sort']
        return f"\\v {ref_verse} "
        
    def save_one_book(self):
        if self.usfm_str != "":
            with open(f'{self.output_folder}/bsb_{self.current_book}.usfm', 'w', encoding='utf-8') as out_file:
                out_file.write(self.usfm_str)

if __name__ == "__main__":
    input_csv = 'input/bsb_tables.csv'
    output_folder = 'output/bsb_usfms'
    ProcessBSBEnglish(input_csv, output_folder)
