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
        self.null_align_pattern = re.compile(r'\B\-\B') # - without word surrounding it
        self.add_text_pattern = re.compile(r'\[[^\]]+\]') # [] enclosed text
        self.curly_brace_pattern = re.compile(r'\{[^\}]*\}') # {} enclosed text
        self.curly_or_sq_barces = re.compile(r'\[[^\]]+\]|\{[^\}]*\}')
        self.up_align_pattern = re.compile(r'\. \. \.')
        self.down_align_pattern = re.compile(r'vvv')

        self.align_df = pd.DataFrame( columns=["vref","source","target","alignment"])
        self.align_df.set_index('vref', inplace=True)
        
        self.trg_start_indices = {}
        self.get_trg_starts()

        self.current_ref = ""
        self.source_text = []
        self.target_text = {}
        self.src_word_count = 0
        self.alignment = []
        self.prev_src_indices = []
        self.prev_trg_index = []
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
                cell_text = str(row['BSB Version'])
                if re.search(self.null_align_pattern, cell_text):
                    cell_text = re.sub(self.null_align_pattern, "", cell_text).strip()
                    self.add_aligned_text_by_splitting(cell_text, trg_word_count=None)
                elif re.search(self.add_text_pattern, cell_text) or re.search(self.curly_brace_pattern, cell_text):
                    non_align_entries = re.findall(self.curly_or_sq_barces, cell_text)
                    align_entries = re.split(self.curly_or_sq_barces, cell_text)
                    while cell_text.strip() != "":
                        if align_entries and cell_text.startswith(align_entries[0]):
                            self.add_aligned_text_by_splitting(align_entries[0], trg_word_count)
                            cell_text = cell_text.replace(align_entries[0], "", 1)
                            align_entries.pop(0)
                        if non_align_entries and cell_text.startswith(non_align_entries[0]):
                            self.add_aligned_text_by_splitting(non_align_entries[0][1:-1], trg_word_count=None)
                            cell_text = cell_text.replace(non_align_entries[0], "", 1)
                            non_align_entries.pop(0)
                elif re.search(self.up_align_pattern, cell_text):
                    for idx in self.prev_src_indices:
                        self.alignment.append(f"{idx}-{trg_word_count}")
                elif re.search(self.down_align_pattern, cell_text):
                    self.prev_trg_index.append(trg_word_count)
                else:
                    self.add_aligned_text_by_splitting(cell_text, trg_word_count)
        except Exception as exce:
            print(f"Issue at {row=}")
            print(exce)

    def add_aligned_text_by_splitting(self, text, trg_word_count):
        '''BSB cell can have more than one word. Split it to calculate pharaoh alignment'''
        words = text.split(" ")
        prev_src_cleared = False
        for wrd in words:
            if wrd != "":
                if not prev_src_cleared:
                    self.prev_src_indices = []
                    prev_src_cleared = True
                self.source_text.append(wrd)
                self.src_word_count += 1
                self.prev_src_indices.append(self.src_word_count)
                if trg_word_count is not None:
                    self.alignment.append(f"{self.src_word_count}-{trg_word_count}")
                    for idx in self.prev_trg_index:
                        self.alignment.append(f"{self.src_word_count}-{idx}")
        self.prev_trg_index = []

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
