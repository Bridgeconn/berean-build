'''Scripts to extract the English Bible contents from the input XLSX/CSV file'''

import re
import pandas as pd
import numpy as np

from utils import book_name_code_map

class ProcessBSBEnglish:
    def __init__(self, filepath, excel_sheet, header_row,output_folder="bsb_usfms"):
        self.bsb_df = pd.read_excel(filepath, sheet_name=excel_sheet, header=header_row)
        self.ref_pattern = re.compile(r'(\d? ?[\w ]+) (\d+):(\d+)')
        self.html_pattern = re.compile(r'\<.*\>')
        self.footnote_span_start_pattern = re.compile(r'\<span class=\|fnv\|\>')
        self.footnote_span_end_pattern = re.compile(r'\</span\>')
        self.null_align_pattern = re.compile(r'\B\-\B')
        self.output_folder=output_folder
        self.current_book = ""
        self.current_chapter = ""
        self.current_verse = ""
        self.usfm_str = ""
        self.src_index = 0
        self.verse_start_indices = {}
        self.get_verse_starts()
        self.bsb_df.apply(lambda row: self.row2usfm(row), axis=1)
        self.save_one_book()

    def get_verse_starts(self):
        for index, row in self.bsb_df.iterrows():
            if not pd.isna(row["Grk Sort"]) and row['Grk Sort'] != 0:
                src_index = int(row["Grk Sort"])
            elif not pd.isna(row["Heb Sort"]):
                src_index = int(row["Heb Sort"])
            if not pd.isna(row['Verse']):
                ref_match = re.match(self.ref_pattern, row['Verse'])
                ref_book = ref_match.group(1)
                ref_chapter = ref_match.group(2)
                ref_verse = ref_match.group(3)
                book_code = book_name_code_map[ref_book]
                current_verse = f"{book_code} {ref_chapter}:{ref_verse}"
                self.verse_start_indices[current_verse] = src_index
            if src_index < self.verse_start_indices[current_verse]:
                self.verse_start_indices[current_verse] = src_index

    def handle_bsb_specialnotations(self,row):
        cell_text = str(row['BSB Version'])
        if re.search(self.null_align_pattern, cell_text):
            print(f"Found a null_align_pattern:{cell_text}")
            self.usfm_str += re.sub(self.null_align_pattern, "", cell_text).strip()
        else:
            self.usfm_str += "\\w "
            self.usfm_str += f"{cell_text} |"
            if row['Language'] in ["Hebrew", "Aramaic"]:
                bib = "WLC"
                wrd_index = row['Heb Sort'] - self.src_index + 1
            elif row["Language"] == "Greek":
                bib = "Nestle"
                wrd_index = row['Grk Sort'] - self.src_index + 1
            if not pd.isna(row['Strongs']):
                self.usfm_str += f"strong=\"{int(row['Strongs'])}\" "
            self.usfm_str += f"srcloc=\"{bib}:{self.current_book}.{self.current_chapter}.{self.current_verse}.{int(wrd_index)}\" "
            self.usfm_str += "\\w* "

    def row2usfm(self, row):
        verse_start = ""
        if not pd.isna(row['Verse']):
           verse_start = self.process_verse(row)
        if not pd.isna(row['Heading']):
            sect_heading = row['Heading']
            sect_heading = re.sub(self.html_pattern, "", sect_heading)
            self.usfm_str += f"\n\\s {sect_heading}\n\\p\n"
        if verse_start!="":
            self.usfm_str += verse_start
        if not pd.isna(row['Cross References']):
            items = row['Cross References'].replace('(', '').replace(')', '')
            self.usfm_str += f'\\x + \\xo {self.current_chapter}:{self.current_verse}: \\xt {items} \\x* '
        if row['BSB Version'] is not np.NaN:
            self.handle_bsb_specialnotations(row)

        if row['Footnotes'] is not np.NaN:
            footnote_text = row['Footnotes'].replace("<i>", '"').replace("</i>", '"')
            footnote_text = re.sub(self.footnote_span_start_pattern, f"({self.current_book}.{self.current_chapter}.", footnote_text)
            footnote_text = re.sub(self.footnote_span_end_pattern, f") ", footnote_text)
            self.usfm_str += f'\\f + \\fr {self.current_chapter}.{self.current_verse} \\ft {footnote_text} \\f* '
    
    def process_verse(self, row):
        ref_match = re.match(self.ref_pattern, row['Verse'])
        ref_book = ref_match.group(1)
        ref_chapter = ref_match.group(2)
        ref_verse = ref_match.group(3)
        # print(f"{ref_book=} {ref_chapter=} {ref_verse=}")
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
        ref_str = f"{self.current_book} {self.current_chapter}:{self.current_verse}"
        self.src_index = self.verse_start_indices[ref_str]
        return f"\\v {ref_verse} "
        
    def save_one_book(self):
        if self.usfm_str != "":
            with open(f'{self.output_folder}/bsb_{self.current_book}.usfm', 'w', encoding='utf-8') as out_file:
                out_file.write(self.usfm_str)
            print(f"Saves {self.current_book}")

if __name__ == "__main__":
    input_excel = 'input/bsb_tables.xlsx'
    excel_sheet = 'biblosinterlinear96'
    header_row = 1
    output_folder = 'output/bsb_usfms'
    ProcessBSBEnglish(input_excel, excel_sheet, header_row, output_folder)
