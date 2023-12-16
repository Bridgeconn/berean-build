"""Scripts to extract Hebrew Bible contents from the input CSV"""

import re
import pandas as pd
import numpy as np

from utils import book_name_code_map

class ProcessNestleGreek:
    def __init__(self, filepath, excel_sheet, header_row, output_folder="grk_usfms"):
        self.bsb_df = pd.read_excel(filepath, sheet_name=excel_sheet, header=header_row)
        self.ref_pattern = re.compile(r'(\d? ?[\w ]+) (\d+):(\d+)')
        self.output_folder=output_folder
        self.current_book = ""
        self.current_chapter = ""
        self.current_verse = ""
        self.usfm_str = ""
        self.current_ref = ""
        self.bsb_df = self.bsb_df.drop(labels=['Vs'], axis=1)
        self.bsb_df = self.bsb_df.dropna(how='all', axis=0)

        self.bsb_df["Verse"].fillna(method='ffill', inplace=True)
        self.bsb_df = self.bsb_df[self.bsb_df['Language']=="Greek"]
        self.bsb_df.sort_values(by=['Grk Sort'], inplace=True)
        self.bsb_df.apply(lambda row: self.row2usfm(row), axis=1)
        self.save_one_book()

    def row2usfm(self, row):
        verse_start = ""
        if row['Verse'] is not np.NaN:
           verse_start = self.process_verse(row)
        if verse_start!="":
            self.usfm_str += verse_start
        if row['WLC / Nestle Base {TR} ⧼RP⧽ (WH) 〈NE〉 [NA] ‹SBL› [[ECM]]'] is not np.NaN:
            self.usfm_str += f"\\w "
            self.usfm_str += f"{row['WLC / Nestle Base {TR} ⧼RP⧽ (WH) 〈NE〉 [NA] ‹SBL› [[ECM]]']} |"
            if not pd.isna(row['Strongs']):
                self.usfm_str += f"strong=\"{int(row['Strongs'])}\" "
                self.usfm_str += f"link-href=\"./Strongs_dictionary.md#{row['Language'][0].lower()}{int(row['Strongs'])}\" "
            if not pd.isna(row['Parsing']):
                self.usfm_str += f"x-morph=\"{row['Parsing']}\" "
            if not pd.isna(row['Translit']):
                self.usfm_str += f"x-translit=\"{row['Translit']}\""
            self.usfm_str += "\\w*"
            
    def process_verse(self, row):
        if row['Verse'] == self.current_ref:
            return ""
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
            self.usfm_str = f"\\id {book_code} {ref_book} of Nestle Greek Bible\n\\c {ref_chapter}\n\\p\n"
        elif ref_chapter != self.current_chapter:
            self.usfm_str += f"\n\\c {ref_chapter}\n\\p\n"
            self.current_chapter = ref_chapter
        self.current_verse = ref_verse
        self.current_ref = row['Verse']
        return f"\\v {ref_verse} "
        
    def save_one_book(self):
        if self.usfm_str != "":
            with open(f'{self.output_folder}/grk_{self.current_book}.usfm', 'w', encoding='utf-8') as out_file:
                out_file.write(self.usfm_str)
            print(f"Saves {self.current_book}")

if __name__ == "__main__":
    input_excel = 'input/bsb_tables.xlsx'
    excel_sheet = 'biblosinterlinear96'
    header_row = 1
    output_folder = 'output/grk_usfms'
    ProcessNestleGreek(input_excel, excel_sheet, header_row, output_folder)
