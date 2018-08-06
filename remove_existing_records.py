#!/usr/bin/env python3
 
#########################################################################################################################################
###
### Script removes all records in knowledgebase /mnt/minerva1/nlp/projects/czech_wikipedia/results_final/kb_final.txt
### that are already present in existing knowledgebase /mnt/data/nlp/projects/entity_kb_czech3/xplani02/kb_cs.
### If the records have the same wikipedia URl, they are considered equal and removed.
### Script does not modify any of the existing files, new knowledgebase is put in 
### /mnt/minerva1/nlp/projects/czech_wikipedia/results_final/kb_final_filtered.txt.
###
#########################################################################################################################################


import sys
import re
import os.path
import logging


# paths - parameters
kbhead_existing_path = "/mnt/minerva1/nlp/projects/entity_kb_czech3/xplani02/HEAD-KB"
kb_existing_path = "/mnt/data/nlp/projects/entity_kb_czech3/xplani02/kb_cs"
kb_czech_path = "/mnt/minerva1/nlp/projects/czech_wikipedia/results_final/kb_final.txt"
kb_result_path = "/mnt/minerva1/nlp/projects/czech_wikipedia/results_final/kb_final_filtered.txt"


def remove_existing_records(kbhead_wikiurl_map, kb_existing_path_param, kb_czech_path_param, logger):
	"""Removes records that are already present in -kb_existing- from -kb_czech'. """

	kb_existing = open(kb_existing_path_param, "r")
	kb_czech = open(kb_czech_path_param, "r")
	kb_result = open(kb_result_path, "w")

	kb_existing_urls = set()
	kb_czech_lines = []

	for line in kb_existing:
		line_columns = line.split('\t')
		protocol_url = line_columns[kbhead_wikiurl_map[line_columns[0]]].strip().split(':', 1) # normalize URL to format without http(s) => //cs.wikipedia.org/...
		if len(protocol_url) == 2:
			kb_existing_urls.add(protocol_url[1])
	
	for line in kb_czech:
		kb_czech_lines.append(line)

	i = 0
	removed = 0
	last = 0
	while i < len(kb_czech_lines):
		protocol_url = kb_czech_lines[i].split('\t')[1].strip().split(':', 1) # normalize URL to format without http(s) => //cs.wikipedia.org/...

		if len(protocol_url) != 2:
			continue

		url = protocol_url[1]

		if url in kb_existing_urls:
			del kb_czech_lines[i]
			removed += 1
			i = i-1 

		i += 1 
		if i % 20000 == 0 and i != last:
			last = i
			logger.info("==== Processed {} records ====".format(i))



	for entry in kb_czech_lines:
		kb_result.write(entry)

	logger.info("==== Script complete. Records removed: {}. Length of the resulting knowledgebase: {} ====".format(removed, i))


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
		kbhead_existing = open(kbhead_existing_path, "r")
		kbhead_wikiurl_map = {}
		for line in kbhead_existing:
			line_columns = line.split("\t")
			for i, column in enumerate(line_columns):
				if re.match(r"(\{[^\}]*\})?WIKI_URL", column):
					kbhead_wikiurl_map[line_columns[0][1:-1]] = i
					break
		remove_existing_records(kbhead_wikiurl_map, kb_existing_path, kb_czech_path, logger)

	logger.info("==== Scrip succesfully finished with exit status [0] ====")
	sys.exit()



if __name__ == '__main__':
	main()
