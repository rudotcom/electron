#!/bin/bash

# First we will check if postgres has been installed or not
# by this command it will print postgres version if installed or not
# to stdout and stderr

# Next we will check if venv is there or not
# cd django3-ecommerce-v2
ls | grep "venv" > /dev/null 2>&1
if [ $? == 0 ]
then
  echo "Python venv is already available. Activating..."
  source venv/bin/activate
  pip3 install -r requirements.txt
else
  virtualenv -p python venv
  source venv/bin/activate
#  pip3 install -r requirements.txt
  echo "Python venv has been installed with reqirements.txt"
fi


# Next we will migrate the changes
python3 manage.py makemigrations
python3 manage.py migrate
touch /home/gitlab-runner/IntrovertProject/Introvert/settings.py


# Next we will start the server
nohup python3 manage.py runserver > /dev/null 2>&1 &
