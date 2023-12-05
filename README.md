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
			* Strong (and link-href ?) 
			* Srcloc, indicating alignment to source bible words 

		```
		\w  Paul ,  |strong="3972" srcloc="Nestle:1CO.1.1.1" \w* \w  called [to be]  |strong="2822" srcloc="Nestle:1CO.1.1.2" \w* \w  an apostle  |strong="652" srcloc="Nestle:1CO.1.1.3" \w* 
		```

	* Nestle Greek and WLC Hebrew source bibles in separate USFMs (39 for Heb and 27 for Grk) with following attributes in \w encloded words 

		* Strong (and link-href ?) 

		* x-morph 

		* x-translit 

		```
		\w Πέτρος |strong="4074" x-morph="N-NMS" x-translit="Petros"\w*\w ἀπόστολος |strong="652" x-morph="N-NMS" x-translit="apostolos"\w* 
		```
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
