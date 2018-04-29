#!/bin/bash

# Run czechwiki_exctractor.py with all necessary options

# Jump to the project root directory if this was launched from within this directory
if [ "$PWD" = "*/work" ] ; then cd .. ; fi

# Modify inputs and outputs here:
STARTTIME="`date +%d-%m-%Y--%H:%M`"
INPUTDIR="preprocessed_dump_*"
OUTPUTDIR="results_$STARTTIME"
LOGFILE="czechwiki_extractor.log"

# Run czechwiki_extractor.py (see README.md for the option explanation)
./czechwiki_extractor.py --datadir $INPUTDIR --output $OUTPUTDIR
