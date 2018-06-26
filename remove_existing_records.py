#!/usr/bin/env python3
 
#########################################################################################################################################
###
#########################################################################################################################################


import sys
import re
import os.path
import logging


# paths - parameters
kb_existing_path = "/mnt/data/nlp/projects/entity_kb_czech3/xplani02/kb_cs" 
kb_czech_path = "/mnt/minerva1/nlp/projects/czech_wikipedia/results_final/kb_final.txt"
kb_result_path = "/mnt/minerva1/nlp/projects/czech_wikipedia/results_final/kb_final_filtered.txt"


def remove_existing_records(kb_existing_path_param, kb_czech_path_param):
	"""Removes records that are already present in -kb_existing- from -kb_czech'. """

	kb_existing = open(kb_existing_path_param, "r")
	kb_czech = open(kb_czech_path_param, "r")
	kb_result = open(kb_result_path, "w")

	kb_existing_urls = []
	kb_czech_lines = []

	for line in kb_existing:
		kb_existing_urls.append('\t'.split(line)[-1])
	
	for line in kb_czech:
		kb_czech_lines.append(line)

	i = 0
	while i < len(kb_czech_lines):
		url = '\t'.split(kb_czech_lines[i])[1]
		
		for existing_url in kb_existing_urls:
			if existing_url.strip() == url:
				del kb_czech_lines[i]
				i = i-1 
				break

		i = i+1
		if i % 10000 == 0:
			print(i)
			



	for entry in kb_czech_lines:
		kb_result.write(entry)


def main():

	# Setup module LOGGER
	logger = logging.getLogger(__file__)
	logger.setLevel(logging.INFO)
	
	# handler to the stderr:
	stderrHandler = logging.StreamHandler(sys.stderr)
	stderrHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s'))
	logger.addHandler(stderrHandler)

	logger.info("==== Script started ====")

	optionsValid = True

	if not os.path.exists(kb_existing_path):
		logger.error("Could not find existing knowledgebase {}.\n".format(kb_existing_path))
		optionsValid = False

	if not os.path.exists(kb_czech_path):
		logger.error("Could not find data directory {}.\n".format(kb_czech_path))
		optionsValid = False


	if not optionsValid:
		logger.error("==== Script terminating with exit status [1] ====")
		sys.exit(1)
	else:
		remove_existing_records(kb_existing_path, kb_czech_path)

	logger.info("==== Scrip succesfully finished with exit status [0] ====")
	sys.exit()



if __name__ == '__main__':
	main()
