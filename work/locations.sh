# Servers, directories, files used in this project
# Can be run through bash to set/load following variables:

if [ -z "$MINERVA1" ] 
then

echo "Sourcing Knotis locations:"

# Storage server:
MINERVA1="xfrune00@minerva1.fit.vutbr.cz"

# Processing server:
ATHENA1="xfrune00@athena1.fit.vutbr.cz"

# Project directory (on minerva1):
PROJ_DIR="/mnt/minerva1/nlp/projects/czech_wikipedia"

# Temp directory for processing (on athena1):
TEST_DIR="/tmp/czech_wikipedia_testing"

echo "MINERVA1=$MINERVA1"
echo "ATHENA1=$ATHENA1"
echo "PROJ_DIR=$PROJ_DIR"
echo "TEST_DIR=$TEST_DIR"

fi
