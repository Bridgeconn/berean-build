'''Scripts to extract the Alignment data from the input XLSX/CSV file in pharaoh format'''

import re
import glob
import pandas as pd
import numpy as np

from utils import book_name_code_map

target_col = 'WLC / Nestle Base {TR} ⧼RP⧽ (WH) 〈NE〉 [NA] ‹SBL› [[ECM]]'

class ProcessAlignment:
    def __init__(self,
                 filepath, excel_sheet, header_row,output_folder="berean-build/output"):
        self.bsb_df = pd.read_excel(filepath, sheet_name=excel_sheet, header=header_row)
        self.ref_pattern = re.compile(r'(\d? ?[\w ]+) (\d+):(\d+)')
        self.null_align_pattern = re.compile(r'\B\-\B')


        self.align_df = pd.DataFrame( columns=["vref","source","target","alignment"])
        self.align_df.set_index('vref', inplace=True)
        
        self.trg_start_indices = {}
        self.get_trg_starts()

        self.current_ref = ""
        self.source_text = []
        self.target_text = {}
        self.src_word_count = 0
        self.alignment = []
        self.bsb_df.apply(lambda row: self.row2alignment(row), axis=1)
        
        self.save_output_files(output_folder)

    def row2alignment(self, row):
        try:
            if not pd.isna(row['Verse']):
                if self.current_ref != "":
                    self.align_df.at[self.current_ref, "source"] = " ".join(self.source_text)
                    self.target_text = dict(sorted(self.target_text.items()))
                    target_text = " ".join(self.target_text.values())
                    self.align_df.at[self.current_ref, "target"] = target_text
                    self.align_df.at[self.current_ref, "alignment"] = " ".join(self.alignment)
                    self.source_text = []
                    self.target_text = {}
                    self.alignment = []
                    self.src_word_count = 0    
                ref_match = re.match(self.ref_pattern, row['Verse'])
                ref_book = ref_match.group(1)
                ref_chapter = ref_match.group(2)
                ref_verse = ref_match.group(3)
                book_code = book_name_code_map[ref_book]
                self.current_ref = f"{book_code} {ref_chapter}:{ref_verse}" 
            
            trg_word_count = None
            if not pd.isna(row[target_col]):
                if row['Grk Sort'] != 0:
                    self.target_text[row['Grk Sort']] = row[target_col]
                    target_index = int(row['Grk Sort'])
                elif row['Heb Sort'] != 999999:
                    self.target_text[row['Heb Sort']] = row[target_col]
                    target_index = int(row['Heb Sort'])
                trg_word_count = target_index - self.trg_start_indices[self.current_ref] + 1
    
            if not pd.isna(row["BSB Version"]):
                if re.search(self.null_align_pattern, str(row['BSB Version'])):
                    cell_text = re.sub(self.null_align_pattern, "", str(row['BSB Version'])).strip()
                    if cell_text != "":
                        self.source_text.append(cell_text)
                else:
                    self.source_text.append(str(row["BSB Version"]).strip())
                    self.src_word_count += 1
                    if trg_word_count is not None:
                        self.alignment.append(f"{self.src_word_count}-{trg_word_count}")
        except Exception as exce:
            print(f"Issue at {row=}")
            print(exce)

    def get_trg_starts(self):
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
                self.trg_start_indices[current_verse] = src_index
            if src_index < self.trg_start_indices[current_verse]:
                self.trg_start_indices[current_verse] = src_index

    def save_output_files(self, data_folder):
        with open(f"{data_folder}/bsb_text.txt", 'w', encoding='utf-8') as src_text_file:
            src_text_file.write("\n".join(self.align_df['source']))
        with open(f"{data_folder}/heb_grk_text.txt", 'w', encoding='utf-8') as trg_text_file:
            trg_text_file.write("\n".join(self.align_df['target']))
        with open(f"{data_folder}/bsb_to_heb_or_grk_alignment.txt", 'w', encoding='utf-8') as align_file:
            align_file.write("\n".join(self.align_df['alignment']))
        with open(f"{data_folder}/vref.txt", 'w', encoding='utf-8') as vref_file:
            vref_file.write("\n".join(self.align_df.index))

if __name__== '__main__':
    input_excel = 'input/bsb_tables.xlsx'
    excel_sheet = 'biblosinterlinear96'
    header_row = 1
    output_folder = 'output/'
    ProcessAlignment(input_excel, excel_sheet, header_row, output_folder)
