#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
#########################################################################################################################################
###
### Script for extracting sentences, paragraphs and full texts or generating knowledgebase 
### from intermediary dump created usign WikiExtractor.py https://github.com/attardi/wikiextractor.
### USAGE: czechwiki_extractor.py -d preprocessed_dump_dir -o results 
### See README.md for instructions on extraction
###
#########################################################################################################################################


import sys
import argparse
import re
import os.path
import html
import logging
import time

from types import SimpleNamespace

import requests
from ufal.udpipe import Model, Pipeline, ProcessingError



def get_dir_name_fulltexts(title:str) -> str:
	"""Little helper method. Returns name of a directory in which the article should be put
	while sorting, based on the title of the article."""
	
	t_numeric = "numeric" #title begins with a number
	t_alphaXX = "alpha_XX" # title has the same two letters at the beginning
	t_others = "others"
	t_alnum = "AlNum" # title begins with letter and number

	if not title: # empty title
		return t_others
	elif title[0].isdigit(): # starts with a digit
		return t_numeric
	elif len(title) >= 2: # at least two character title
		if title[0].isalpha() and title[1].isalpha() and title[0].upper() == title[1].upper():
			return t_alphaXX
		elif title[0].isalpha() and title[1].isalpha() and title[0].upper() != title[1].upper():
			return title[0].upper() + title[1].upper()
		elif title[0].isalpha() and title[1].isdigit():
				return t_alnum
		else:
			return t_others
	else:
		return t_others


def perform_extraction(dumpdir:str, outputdir:str, logger:logging.Logger) -> None:
	"""Entry point for performing extraction from WikiExtractor HTML intermediary dump"""

	paragraphs_file_name = "paragraphs.txt"
	fulltexts_dir_name = "fulltexts"
	knowledgebase_file_name = "incomlete-kb.txt" # incomplete kb
	kb_file_name = "knowledgebase.txt" # complete


	paragraphs_file = open(os.path.join(outputdir, paragraphs_file_name), "w")
	fulltexts_dir = os.path.join(outputdir, fulltexts_dir_name)
	if not os.path.exists(fulltexts_dir):
		os.makedirs(fulltexts_dir)
	knowledgebase_file = open(os.path.join(outputdir, knowledgebase_file_name), "w")


	logger.info("==== Performing extraction ====")

	# variables for logging and progress tracking, begin with 'log_'
	log_totalpagecount = 0
	log_pagechunk = 10000 # display info after processing this many pages


	### WARNING!: iterates over overy file in every subdirectory of 'dumpdir'! 
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
					page_title, page_uri, page_id, page_first_paragraph, page_fulltext = extract_page_info(doc_text)  

					if ' (rozcestník)' in page_title or page_title.lower() == 'hlavní strana':
						continue

					page_title = re.sub(r' \([^\)]*\)$', '', page_title)

					# write data to specific files:
					paragraphs_file.write(page_uri + '\t' + page_first_paragraph + '\n')

					
					# replace '/' in the #title with %2F - its URL escape - because '/' is forbidden in filenames
					escaped_page_title = re.sub(r'/', r'%2F', page_title) 
					temp_filename = "wp_" + escaped_page_title # filename: wp_ (as wikipage) + page title
					temp_dir = os.path.join(fulltexts_dir, "d_" + get_dir_name_fulltexts(escaped_page_title)) # dirname - use first two letters of the page title
					if not os.path.exists(temp_dir):
						os.makedirs(temp_dir)

					temp_fulltext_file = open(os.path.join(temp_dir, temp_filename + '.txt'), "w")
					temp_fulltext_file.write(page_fulltext) 
					temp_fulltext_file.close()
				
					entity_line = "{}\t{}\t{}\t{}".format(page_id, page_uri, page_title, page_first_paragraph)
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
	paragraphs_file.close()
	knowledgebase_file.close()

	logger.info("==== Extraction complete : Pages processed: {} ====".format(log_totalpagecount))



def extract_page_info(doc_text:str) -> (str, str, str, str, str):
	"""Extract following information from HTML preprocesssed wikipage as tuple with this order:
		(title, uri, id, first sentence, first paragraph, full text).
		 This method is called inside perfom_extraction method for each wikipage html it reads from the preprocessed dump."""

	page_title = ''
	page_uri = ''
	page_id = ''
	page_first_paragraph = ''
	page_fulltext = ''
	
	doc_text = html.unescape(doc_text)
	# A little bug-counter - input html contains '&amp;nbsp' instead of '&nbsp', so 
	# after the first html.unescape() strings '&nbsp' are left in the text (and maybe this goes for more html entities)
	doc_text = html.unescape(doc_text)


	# extract title, uri and id:
	pattern_header = re.compile(r'<doc\s+id="(\d+)"\s+url="([^"]+)"\s+title="(.+?)">')
	page_id, page_uri, page_title = pattern_header.findall(doc_text)[0] 
	# URI contains ID, not the title - replace that (in title spaces must be replaced with '_' for this)
	page_uri = re.sub(r'\?.+', r'/{}'.format(re.sub(r' ', r'_', page_title)), page_uri, 1)
	
	# remove opening and ending <doc> elements
	doc_text = re.sub(r'</?doc.*?>', r'', doc_text) 

	# replace links with their plain text representation
	doc_text = re.sub(r'<a href="[^"]+">([^<]+)</a>', r'\1', doc_text)

	# Make copy of the doctext (extraction for fulltext and for sentences, paragraphs, knowledgebase is a little differect)
	page_fulltext = doc_text


	## 1) For paragraphs, knowledgebase:
	
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


	return (page_title, page_uri, page_id, page_first_paragraph, page_fulltext)



## Object 'options' will hold specified arguments 
options = SimpleNamespace(
						datadir='', 
						outputdir='', 
						logfile=''
		)



def main(argList:list = None) -> None:
	"""Entry point"""

	"""Can be executed on its own (then it takes arguments from the shell), 
	or can be executed in another script, in which case the script
	can pass custom, modified list of arguments"""

	argParser = argparse.ArgumentParser(description="""Script for extracting full article texts, first paragraphs of the texts
																	or generating a meta-knowledge base from a predump generated by by WikiExtractor.py.""")

	argParser.add_argument('-d', '--datadir', help="""Path to the directory where WikiExtractor.py preprocessed the data from wikidump 
									(the directory that contains directories 'AA', 'AB', 'AC' ...).""",required=True)
	argParser.add_argument('-o', '--outputdir', help="""Path to a directory where this extractor puts its results.""", required=True)
	argParser.add_argument('-l', '--logfile', help="""Write script info messages and error into logfile (by default written only to stderr).""")
	

### Read arguments from terminal/shell or from the main() method argument list, if it's not empty
	if argList == None:
		args = argParser.parse_args()
	else:
		args = argParser.parse_args(argList)


### Transfer 'args' into the 'options' object, just for readability
	options.datadir = args.datadir
	options.outputdir = args.outputdir
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

	if not os.path.exists(os.path.join(options.outputdir, "fulltexts")):
		try:
			os.makedirs(os.path.join(options.outputdir, "fulltexts"))
		except:
			logger.error("Could not create directory 'fulltexts'.")
			optionsValid = False
	

	if not optionsValid:
		logger.error("==== Script terminating with exit status [1] ====")
		sys.exit(1)
	else: # Perform extraction
		perform_extraction(options.datadir, options.outputdir, logger)

	logger.info("==== Scrip succesfully finished with exit status [0] ====")
	sys.exit()



if __name__ == '__main__':
	main()
