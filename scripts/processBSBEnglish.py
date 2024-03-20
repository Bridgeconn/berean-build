'''Scripts to extract the English Bible contents from the input XLSX/CSV file'''

import re
import pandas as pd
import numpy as np

from utils import book_name_code_map

class ProcessBSBEnglish:
    def __init__(self, filepath, excel_sheet, header_row,output_folder="bsb_usfms"):
        '''Calls all other methods and does complete processing upon init itself'''
        self.bsb_df = pd.read_excel(filepath, sheet_name=excel_sheet, header=header_row)
        self.ref_pattern = re.compile(r'(\d? ?[\w ]+) (\d+):(\d+)')
        self.html_pattern = re.compile(r'\<.*\>')
        self.footnote_span_start_pattern = re.compile(r'\<span class=\|fnv\|\>')
        self.footnote_span_end_pattern = re.compile(r'\</span\>')
        self.null_align_pattern = re.compile(r'\B\-\B') # - without word surrounding it
        self.add_text_pattern = re.compile(r'\[[^\]]+\]') # [] enclosed text
        self.curly_brace_pattern = re.compile(r'\{[^\}]*\}') # {} enclosed text
        self.up_align_pattern = re.compile(r'\. \. \.')
        self.down_align_pattern = re.compile(r'vvv')

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
        '''Special processing as Grk and heb are not given in actual order in excel'''
        for _, row in self.bsb_df.iterrows():
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

    def form_w_marker(self, cell_text, row):
        '''Add a w marker to usfm with strongs and srcloc attributes'''
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


    def handle_bsb_specialnotations(self,row):
        '''Special treatment for notations: - [] {} . . . vvv in BSB Version cell'''
        cell_text = str(row['BSB Version'])
        if re.search(self.null_align_pattern, cell_text):
            self.usfm_str += re.sub(self.null_align_pattern, "", cell_text).strip()
        elif re.search(self.up_align_pattern, cell_text):
            pass
        elif re.search(self.down_align_pattern, cell_text):
            pass
        elif re.search(self.add_text_pattern, cell_text):
            add_entries = re.findall(self.add_text_pattern, cell_text)
            w_entries = re.split(self.add_text_pattern, cell_text)
            while cell_text.strip() != "":
                if w_entries and cell_text.startswith(w_entries[0]):
                    if re.search(r'\w', w_entries[0]):
                        self.form_w_marker(w_entries[0], row)
                    else:
                        self.usfm_str += f"{w_entries[0]} " 
                    cell_text = cell_text.replace(w_entries[0], "", 1)
                    w_entries.pop(0)
                if add_entries and cell_text.startswith(add_entries[0]):
                    self.usfm_str += f"\\add {add_entries[0][1:-1]}\\add* "
                    cell_text = cell_text.replace(add_entries[0], "", 1)
                    add_entries.pop(0)
        elif re.search(self.curly_brace_pattern, cell_text):
            norm_entries = re.findall(self.curly_brace_pattern, cell_text)
            w_entries = re.split(self.curly_brace_pattern, cell_text)
            while cell_text.strip() != "":
                if w_entries and cell_text.startswith(w_entries[0]):
                    if re.search(r'\w', w_entries[0]):
                        self.form_w_marker(w_entries[0], row)
                    else:
                        self.usfm_str += f"{w_entries[0]} " 
                    cell_text = cell_text.replace(w_entries[0], "", 1)
                    w_entries.pop(0)
                if norm_entries and cell_text.startswith(norm_entries[0]):
                    self.usfm_str += f"{norm_entries[0][1:-1]} "
                    cell_text = cell_text.replace(norm_entries[0], "", 1)
                    norm_entries.pop(0)
        else:
            self.form_w_marker(cell_text, row)

    def row2usfm(self, row):
        '''Extract USFM components from each row'''
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
            self.usfm_str += \
                f'\\x + \\xo {self.current_chapter}:{self.current_verse}: \\xt {items} \\x* '
        if not pd.isna(row['BSB Version']):
            self.handle_bsb_specialnotations(row)

        if not pd.isna(row['Footnotes']):
            footnote_text = row['Footnotes'].replace("<i>", '"').replace("</i>", '"')
            footnote_text = re.sub(
                                    self.footnote_span_start_pattern, 
                                    f"({self.current_book}.{self.current_chapter}.", footnote_text)
            footnote_text = re.sub(
                                    self.footnote_span_end_pattern, 
                                    ") ", footnote_text)
            self.usfm_str += \
                f'\\f + \\fr {self.current_chapter}.{self.current_verse} \\ft {footnote_text} \\f* '
    
    def process_verse(self, row):
        '''Upon seeing the start of next verse, process the prev completed one'''
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
            self.usfm_str = \
                f"\\id {book_code} {ref_book} of Berean Study Bible\n\\c {ref_chapter}\n\\p\n"
        elif ref_chapter != self.current_chapter:
            self.usfm_str += f"\n\\c {ref_chapter}\n\\p\n"
            self.current_chapter = ref_chapter
        self.current_verse = ref_verse
        ref_str = f"{self.current_book} {self.current_chapter}:{self.current_verse}"
        self.src_index = self.verse_start_indices[ref_str]
        return f"\\v {ref_verse} "
        
    def save_one_book(self):
        '''Produce a .usfm file from the excel'''
        if self.usfm_str != "":
            with open(
                f'{self.output_folder}/bsb_{self.current_book}.usfm',
                'w', encoding='utf-8') as out_file:
                out_file.write(self.usfm_str)
            print(f"Saves {self.current_book}")

if __name__ == "__main__":
    input_excel = 'input/bsb_tables.xlsx'
    excel_sheet = 'biblosinterlinear96'
    header_row = 1
    output_folder = 'output/bsb_usfms'
    ProcessBSBEnglish(input_excel, excel_sheet, header_row, output_folder)
