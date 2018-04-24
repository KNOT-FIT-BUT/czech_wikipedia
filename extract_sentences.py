#!/usr/bin/env python3

#########################################################################################################################################
###
#########################################################################################################################################


import argparse
import re
import os.path
import logging
import sys

import requests
from ufal.udpipe import Model, Pipeline, ProcessingError


def extract_sentences(input_file:str, output_file:str, logger) -> None:
	
	logger.info("==== Now performing sentence extraction from paragraphs file ====")
	# UDPipe initliazation
	lang_model = 'lang_models/czech-ud-2.0-170801.udpipe' 
	model = Model.load(lang_model)
	if not model:
		logger.error('Could not load UDPipe language model: ' + lang_model)
	ud_pipeline = Pipeline(model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, '')
	ud_error = ProcessingError()

	sentences_file = open(output_file, "w")
	# reopen paragraphs for reading
	paragraphs_file = open(input_file, "r")
	
	sentences_count = 0

	for p_line in paragraphs_file:
		page_first_sentence = ""
		page_first_paragraph = p_line.split('\t', 1) # use the variable as temporary list

		# If there is a paragraph content
		if len(page_first_paragraph) == 2:
			page_uri = page_first_paragraph[0]
			page_first_paragraph = page_first_paragraph[1]
			# Extract first sentence form paragraph using UDPipe:
			ud_output = ud_pipeline.process(page_first_paragraph, ud_error)
			if ud_error.occurred():
				logger.error('Error occured while extracting sentence using UDPipe: ' + ud_error.message)
				page_first_sentence = ""
			else:
				ud_output = ud_output.split('\n')
				if len(ud_output) >= 4 :
					page_first_sentence = ud_output[3][9:] # assumption about the output format 
				else:
					page_first_sentence = ""
			
			# Write sentence to the file
			sentences_file.write(page_uri + '\t' + page_first_sentence + '\n')
			
			sentences_count += 1
			if sentences_count % 2000 == 0 :
				logger.info("Extracted {} sentences.".format(sentences_count))


	logger.info("Finished extraction of {} sentences.".format(sentences_count))

	paragraphs_file.close()
	sentences_file.close()




def main(argList:list = None) -> None:
	"""Entry point"""

	"""Can be executed on its own (then it takes arguments from the shell), 
	or can be executed in another script, in which case the script
	can pass custom, modified list of arguments"""

	argParser = argparse.ArgumentParser(description="""Script for extracting first sentences using UDPipe. Input is the paragraphs file generated
																	by czechwiki_extractor.py.""")

	argParser.add_argument('-i', '--input', help="""Path to the paragraphs file.""", required=True)
	argParser.add_argument('-o', '--output', help="""Path to an output file.""", required=True)
		
	argParser.add_argument('-l', '--logfile', help="""Write script info messages and error into logfile (by default written only to stderr).""")
	

### Read arguments from terminal/shell or from the main() method argument list, if it's not empty
	if argList == None:
		args = argParser.parse_args()
	else:
		args = argParser.parse_args(argList)


	# Setup module LOGGER
	logger = logging.getLogger(__file__)
	logger.setLevel(logging.INFO)
	
	# handler to the stderr:
	stderrHandler = logging.StreamHandler(sys.stderr)
	stderrHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'))
	logger.addHandler(stderrHandler)

	# write also to logfile if the argument was passed:
	if args.logfile:
		logfileHandler = logging.FileHandler(args.logfile)
		logfileHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'))
		logger.addHandler(logfileHandler)


	logger.info("==== Script started ====")


### For any invalid options, print some error message and then exit.
	optionsValid = True
	
	# TODO: Option validation
	
	if not optionsValid:
		logger.error("==== Script terminating with exit status [1] ====")
		sys.exit(1)
	else: # Perform extraction
		extract_sentences(args.input, args.output, logger)

	logger.info("==== Scrip succesfully finished with exit status [0] ====")
	sys.exit()



if __name__ == '__main__':
	main()
