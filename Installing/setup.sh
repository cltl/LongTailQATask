#!/usr/bin/env bash
echo
echo "This script is meant to install a python environment for the long tail QA task"
echo "It will perform checks for this and will try to install external python modules with pip."
echo "If there is any error in one of these steps, the script will exit."

#variable names
cwd=${PWD#*}

function command_check () {

RETVAL=$?
[ $RETVAL -eq 0 ] && echo $succes
[ $RETVAL -ne 0 ] && echo $failure && echo 'exiting...' && exit -1

}
#check if python version is installed
echo
echo "CHECK 1: Checking python version"
python -c 'import sys ; assert sys.version_info.major == 3 and sys.version_info.minor >= 4, 'please install python 3.4 or 3.5 or 3.6 \(you have %s.%s\)' % \(sys.version_info.major, sys.version_info.minor\)'
echo "Succes: correct version of python is installed"


#install external python modules
echo
echo "INSTALL: Installing external python modules"
export succes="Succes: external modules have been installed"
export failure="Fail: please try to install module newspaper3k version 0.1.9"

# installing external module newspaper
python3 -m pip install newspaper3k==0.1.9

# checking if newspaper module can imported
python3 -c "import newspaper; assert newspaper.__version__ == '0.1.9', 'incorrect version of newspaper module is installed: %s (should be 0.1.9' % newspaper.__version__"
command_check

echo ""
echo "You are ready to go!"
