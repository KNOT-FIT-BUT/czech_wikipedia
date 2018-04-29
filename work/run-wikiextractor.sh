#!/bin/bash

# Run WikiExtractor.py with all required options for extraction

# Jump to the project root directory if we were launched from this directory
if [ "$PWD" = "*/work" ] ; then cd .. ; fi

# Modify inputs and outputs here:
STARTTIME="`date +%d-%m-%Y--%H:%M`" 
INPUT="cs-wiki-latest-pages-articles.xml"
OUTPUTDIR="preprocessed_dump_$STARTTIME"
TEMPLATES="template_definitions.tmpl"

# Run WikiExtractor.py (see README.md for the options explanation):
./wikiextractor/WikiExtractor.py --html --filter_disambig_pages --templates "$TEMPLATES" --output $OUTPUTDIR $INPUT
