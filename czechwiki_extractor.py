#!/usr/bin/env python3
 
#########################################################################################################################################
###
### Script for extracting sentences, paragraphs and full texts or generating knowledgebase 
### from intermediary dump created usign WikiExtractor.py https://github.com/attardi/wikiextractor.
### Usage:
### See README.md for instructions on extraction
#########################################################################################################################################


import pdb
import sys
import argparse
import re
import os.path
import html
import logging
import nltk
from types import SimpleNamespace



def perform_extraction(dumpdir:str, outputdir:str, extract_sentences:bool, extract_paragraphs:bool, extract_fulltexts:bool, generate_knowledgebase:bool, logger:logging.Logger) -> None:
	"""Entry point for performing extraction from WikiExtractor HTML intermediary dump"""

	if extract_sentences: # overwrite or create files / dirs
		sentences_file = open(os.path.join(outputdir, "sentences.txt"), "w")
	if extract_paragraphs:
		paragraphs_file = open(os.path.join(outputdir, "paragraphs.txt"), "w")
	fulltexts_dir = os.path.join(outputdir, "fulltexts")
	if extract_fulltexts and not os.path.exists(fulltexts_dir):
		os.makedirs(fulltexts_dir)
	if generate_knowledgebase:
		knowledgebase_file = open(os.path.join(outputdir, "knowledgebase.txt"), "w")


	logger.info("==== Performing extraction ====")

	# variables for logging and progress tracking, begin with 'log_'
	log_totalpagecount = 0
	log_pagechunk = 10000 # display info after processing this many pages


	### WARNING!: iterates over overy file in every subdirectory of 'dumdir'! 
	### Make sure no other subdirectories or files are in there
	for subdir in [os.path.join(dumpdir,node) for node in os.listdir(dumpdir) if os.path.isdir(os.path.join(dumpdir, node))]:
		for file_path in [os.path.join(subdir, node) for node in os.listdir(subdir) if os.path.isfile(os.path.join(subdir, node))]:
			html_file = open(file_path, "r")
			while True:
				line = html_file.readline()
				
				# Found beginning of a wiki page
				if line.strip().startswith('<doc'): # process page
					doc_lines = []
					doc_lines.append(line.strip())
					
					# Read all lines of wikipage ( <doc ...> * </doc> )
					while True:
						next_line = html_file.readline().strip()
						if not next_line == '': # discard blank lines
							doc_lines.append(next_line)
						if next_line == "</doc>":
							break
					
					# join by newline (which separates paragraphs in the html file) - 
					# reading separate lines and then str.join() is faster than gradual concatenation)
					doc_text = "\n".join(doc_lines)
					# Html text of wiki page (from <doc ...> to </doc>) is in doc_text. Now convert into plain text and extract info
					page_title, page_uri, page_id, page_first_sentence, page_first_paragraph, page_fulltext, file_uris = extract_page_info(doc_text)  
					
					# because of the simplistic paragraph and sentence extraction patterns, some special wikipages produce
					# paragraphs or sentences with a newline - get rid of those for now - replace them with spaces
					#(probably upgrade to using some third party sentence extractor later):
					page_first_sentence = re.sub(r'\n', r' ', page_first_sentence)
					page_first_paragraph = re.sub(r'\n', r' ', page_first_paragraph)
					
					
					# write data to specific files:
					if extract_sentences:
						sentences_file.write(page_uri + '\t' + page_first_sentence + '\n')
					if extract_paragraphs:
						paragraphs_file.write(page_uri + '\t' + page_first_paragraph + '\n')

					
					if extract_fulltexts: 
						# replace '/' in the #title with %2F - its URL escape - because '/' is forbidden in filenames
						escaped_page_title = re.sub(r'/', r'%2F', page_title) 
						temp_filename = "wp_" + escaped_page_title # filename: wp_ (as wikipage) + page title
						temp_dir = os.path.join(fulltexts_dir, "d_" + escaped_page_title[0:2]) # dirname - use first two letters of the page title
						if not os.path.exists(temp_dir):
							os.makedirs(temp_dir)

						temp_fulltext_file = open(os.path.join(temp_dir, temp_filename + '.txt'), "w")
						temp_fulltext_file.write(page_fulltext) 
						temp_fulltext_file.close()
				
					if generate_knowledgebase:
						entity_line = "{}\t{}\t{}\t{}\t{}".format(page_title, page_uri, page_id, page_first_paragraph, '|'.join(file_uris))
						knowledgebase_file.write(entity_line + '\n')

					log_totalpagecount += 1
					# logging
					if log_totalpagecount % log_pagechunk == 0:
						logger.info("Processed {} pages".format(log_totalpagecount))


				elif line == "": # end of file reached
					break
				else:
					continue

	# Close opened files:
	if extract_sentences:
		sentences_file.close()
	if extract_paragraphs:
		paragraphs_file.close()
	if generate_knowledgebase:
		knowledgebase_file.close()

	logger.info("==== Extraction complete : Pages processed: {} ====".format(log_totalpagecount))





def extract_page_info(doc_text:str) -> (str, str, str, str, str, str, list):
	"""Extract following information from HTML preprocesssed wikipage as tuple with this order:
		(title, uri, id, first sentence, first paragraph, full text, list of file uris in the wikipage).
		 This method is called inside perfom_extraction method for each wikipage html it reads from the preprocessed dump."""


	page_title = ''
	page_uri = ''
	page_id = ''
	page_first_sentence = ''
	page_first_paragraph = ''
	page_fulltext = ''
	page_file_uris = []

	
	doc_text = html.unescape(doc_text)
	# A little bug-counter - input html contains '&amp;nbsp' instead of '&nbsp', so 
	# after the first html.unescape() strings '&nbsp' are left in the text (and maybe this goes for more html entities)
	doc_text = html.unescape(doc_text)


	# extract Files (images etc.):
	page_file_uris = re.findall(r'<a href="Soubor%3A([^"]+)">.*?</a>', doc_text)
	doc_text = re.sub(r'<a href="Soubor%3A([^"]+)">.*?</a>', r'', doc_text)


	# extract title, uri and id:
	pattern_header = re.compile(r'<doc\s+id="(\d+)"\s+url="([^"]+)"\s+title="(.+?)">')
	page_id, page_uri, page_title = pattern_header.findall(doc_text)[0] 
	# URI contains ID, not the title - replace that (in title spaces must be replaced with '_' for this)
	page_uri = re.sub(r'\?.+', r'/{}'.format(re.sub(r' ', r'_', page_title)), page_uri, 1)
	
	# remove opening and ending <doc> elements
	doc_text = re.sub(r'</?doc.*?>', r'', doc_text) 

	# replace links with their plain text representation
	doc_text = re.sub(r'<a href="[^"]+">([^<]+)</a>', r'\1', doc_text)

	# make file uris complete:
	for i in range(len(page_file_uris)):
		page_file_uris[i] = "cs.wikipedia.org/wiki/{}#/media/File:{}".format(re.sub(r' ', r'_', page_title), re.sub(r'%20', r'_', page_file_uris[i]))

	# Make copy of the doctext (extraction for fulltext and for sentences, paragraphs, knowledgebase is a little differect)
	page_fulltext = doc_text


	## 1) For paragraphs, sentences, knowledgebase:
	
	# remove all headings
	doc_text = re.sub(r'<h\d>.*?</h\d>', r'', doc_text) 
	
	# remove all remainign html tags	
	doc_text = re.sub(r'</?[\w]+>', r'', doc_text)

	# collapse multiple newlines into one newline (<=> delete empty lines)
	doc_text = re.sub(r'\n+', r'\n', doc_text)
	# remove ending and trailing if there are any
	doc_text = doc_text.strip()

	# Extract first paragraph (this makes assumptions about the input format - 
	# each paragraph seems to be on a separate line)
	split_paragraphs = doc_text.split("\n")
	page_first_paragraph = split_paragraphs[0] if len(split_paragraphs) >= 1 else ""

	# Old, but kind of working solution to sentence extraction.
	# re.split returns array with empty string if the paragraph is empty string:
	page_first_sentence = re.split(r'\s+(?<=[.?!]\s)(?![a-zěščřžýáíéúůďťň])', page_first_paragraph)[0]


	## 2) For full texts:
	# Apply some formatting:

	# replace headings with respective number of '='
	for n in range(1, 7):
		page_fulltext = re.sub('</?h{}>'.format(n), ' ' + '='*n + ' ', page_fulltext)
	
	# make <br> into newlines
	page_fulltext = page_fulltext.replace('<br>', '\n')

	# recreate ordered and unordered lists into simple lists with "* " at each item:
	page_fulltext = re.sub(r'</?[ou]l>', r'', page_fulltext)
	page_fulltext = re.sub(r'<li>', r'* ', page_fulltext)
	page_fulltext = re.sub(r'</li>', r'', page_fulltext)

	# recreate description lists with "* " at items, " `-> " at descriptions:
	page_fulltext = re.sub(r'</?dl>', r'', page_fulltext)
	page_fulltext = re.sub(r'<dt>', r'* ', page_fulltext)
	page_fulltext = re.sub(r'<dd>', r" `-> ", page_fulltext)
	page_fulltext = re.sub(r'</d[td]>', r'', page_fulltext)



	# remove all remainign html tags	
	page_fulltext = re.sub(r'</?[\w]+>', r'', page_fulltext)
	
	# collapse multiple newlines into one newline (<=> delete empty lines)
	page_fulltext = re.sub(r'\n+', r'\n', page_fulltext)
	# remove ending and trailing if there are any
	page_fulltext = page_fulltext.strip()


	return (page_title, page_uri, page_id, page_first_sentence, page_first_paragraph, page_fulltext, page_file_uris)



## Object 'options' will hold specified arguments 
options = SimpleNamespace(
						datadir='', 
						outputdir='', 
						extract_sentences=False, 
						extract_paragraphs=False, 
						extract_fulltexts=False,
						generate_knowledgebase=False,
						logfile=''
		)



def main(argList:list = None) -> None:
	"""Entry point"""

	"""Can be executed on its own (then it takes arguments from the shell), 
	or can be executed in another script, in which case the script
	can pass custom, modified list of arguments"""

	argParser = argparse.ArgumentParser(description="""Script for extracting first sentences, first paragraphs, full texts or 
													generating knowledgebase for wikipages from predump by WikiExtractor.py.""",
										epilog="""Using all extract options (-s, -p, -f, --kb) at once 
												is the most efficient way to extract the data, because once read, all the data are processed anyway.
												These flags just decide whether the data are written to the result files.""")

	argParser.add_argument('-d', '--datadir', help="""Path to the directory where WikiExtractor.py preprocessed the data from wikidump 
									(the directory that contains directories 'AA', 'AB', 'AC' ...).""",
									required=True)
	argParser.add_argument('-o', '--outputdir', help="""Path to a directory where this extractor puts its results 
										(see options '-s', '-p' and '-f').""",
										required=True)
	argParser.add_argument('-s', help="""Extract first sentences into 'outputdir/sentences.txt'.""", action="store_true")
	argParser.add_argument('-p', help="""Extract first paragraps into 'outputdir/paragraphs.txt'""", action="store_true")
	argParser.add_argument('-f', help="""Extract full text of each wikipage into separate files 'outputdir/fulltexts/<pagetitle>.txt'.""", action="store_true")
		
	argParser.add_argument('--kb', help="""Generate knowledgebase of each wikipage into file 'outputdir/knowledgebase.txt'. 
										Each line for one page formatted as: 'Title URI pageID firstParagraph listOfFiles', 
										each entity separated by tabulators, files separated by pipes ('|').""", action="store_true")
	argParser.add_argument('-l', '--logfile', help="""Write script info messages and error into logfile (by default written only to stderr).""")
	

### Read arguments from terminal/shell or from the main() method argument list, if it's not empty
	if argList == None:
		args = argParser.parse_args()
	else:
		args = argParser.parse_args(argList)


### Transfer 'args' into the 'options' object, just for readability
	options.datadir = args.datadir
	options.outputdir = args.outputdir
	options.extract_sentences = args.s
	options.extract_paragraphs =  args.p
	options.extract_fulltexts = args.f
	options.generate_knowledgebase = args.kb
	options.logfile = args.logfile

	# Setup module LOGGER
	logger = logging.getLogger(__file__)
	logger.setLevel(logging.INFO)
	
	# handler to the stderr:
	stderrHandler = logging.StreamHandler(sys.stderr)
	stderrHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'))
	logger.addHandler(stderrHandler)

	# write also to logfile if the argument was passed:
	if options.logfile:
		logfileHandler = logging.FileHandler(options.logfile)
		logfileHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'))
		logger.addHandler(logfileHandler)


	logger.info("==== Script started ====")


### Check options validity, create output directory if it does not exist
### For any invalid options, print some error message and then exit.
	
	optionsValid = True
	
	if not os.path.exists(options.datadir):
		logger.error("Could not find data directory {}.\n".format(options.datadir))
		optionsValid = False
	
	if not os.path.exists(options.outputdir):
		try:
			os.makedirs(options.outputdir)
		except:
			logger.error("Cannot create output directory {}.\n".format(options.outputdir))
			optionsValid = False
	
	if not (options.extract_sentences or options.extract_paragraphs or options.extract_fulltexts or options.generate_knowledgebase):
		logger.error("You haven't specified any of the extraction options (-s, -p, -f, --kb). What am i supposed to do?\n")
		optionsValid = False

	if options.extract_fulltexts and not os.path.exists(os.path.join(options.outputdir, "fulltexts")):
		try:
			os.makedirs(os.path.join(options.outputdir, "fulltexts"))
		except:
			logger.error("Could not create directory 'fulltexts'.")
			optionsValid = False
	

	if not optionsValid:
		logger.error("==== Script terminating with exit status [1] ====")
		sys.exit(1)
	else: # Perform extraction
		perform_extraction(options.datadir, 
				options.outputdir, 
				options.extract_sentences, 
				options.extract_paragraphs, 
				options.extract_fulltexts,
				options.generate_knowledgebase,
				logger)

	logger.info("==== Scrip succesfully finished with exit status [0] ====")
	sys.exit()



if __name__ == '__main__':
	main()
