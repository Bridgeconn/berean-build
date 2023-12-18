# berean-build

Converting the Berean Study Bible in XLSX format to USFM format.

## Whats in this repo?

* **Input**: The Berean Study Bible content in XLSX format. This is available in [the input folder](./input)

* **Output**: 3 sets of USFMS for the English BSB, Hebrew WLC and Greek Nestle Bibles. Available in [the output folder](./output) 
	* English BSB USFMs (One for each of 66 books) with  
		* English scripture text,  
		* cross-refs (and footnotes -TBD)  
		* section headings.  
		* Phrase level markup using \w with attributes  
			* Strong 
			* Srcloc, indicating alignment to source bible words 

		```
		\w  Paul ,  |strong="3972" srcloc="Nestle:1CO.1.1.1" \w* \w  called [to be]  |strong="2822" srcloc="Nestle:1CO.1.1.2" \w* \w  an apostle  |strong="652" srcloc="Nestle:1CO.1.1.3" \w* 
		```

	* Nestle Greek and WLC Hebrew source bibles in separate USFMs (39 for Heb and 27 for Grk) with following attributes in \w encloded words 

		* Strong and link-href (to the entries in `Strongs_dictionary.md`) 
		* x-morph 
		* x-translit 

		```
		\w Πέτρος |strong="4074" x-morph="N-NMS" x-translit="Petros"\w*\w ἀπόστολος |strong="652" x-morph="N-NMS" x-translit="apostolos"\w* 
		```

	* Word-alignment information provided, extracted as follows:

    	* `bsb_text.txt` with one verse per line
    	* `heb_grk_text.txt` also with one verse per line
    	* `bsb_to_heb_or_grk_alignment.txt` with word alignment between bsb and source Hebrew or Greek in Pharaoh format
    	* `verf.txt` the reference index for the above 3 files

    * Greek and Hebrew Strongs numbers and their description in `Strongs_dictionary.md`


* **Scripts**: Scripts to process the input and generate these outputs are provided in [the scripts folder](./scripts)

## How to run the scripts?

1. Clone this repo
`git clone https://github.com/Bridgeconn/berean-build.git`

2. Install dependecies

```
cd berean-build
python -m venv ENV
source ENV/bin/activate
pip install -r requirements
```
3. Generate the USFMs

```
python scripts/processBSBEnglish.py
python scripts/processWLCHebrew.py
python scripts/processNestleGreek.py 
```

4. Generate Alignment

`python scripts/processAlignment.py`

5. Generate Strongs Dictionary

`python scripts/processDictionary.py`

## Github Actions

Continuous Integration is enabled on this repo for automatically generating outputs via [github actions](./.github/workflows/generate-outputs.yml).

* Upon any change(push) to contents of input folder on the repo, or via manual trigger
* ... the scripts will be run on the inputfile in that branch
* ... generating corresponding output files in the output folder.
* These changes will be committed and pushed back to the same branch.
* The commit message and author will indcate that it is done by bot.
* If the generated files are same as that already present in the repo, commit will fail and no changes will be pushed.(The workflow run will be success though)

If there is a change in the data, just add that new excel file to the input folder under same file name and with same column names inside. If done on github, or pushed to github, it will trigger this workflow and generate the corresponding outputs automatically. The updated outputs will be available in the output folder in the github repo itself. ( :warning: Workflow takes more that 15 minutes to complete.)

