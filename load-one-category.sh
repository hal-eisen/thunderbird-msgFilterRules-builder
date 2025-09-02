#!/bin/bash

echo file: $1
echo rules: $2

if [ ! -f $1 ]; then
  echo Missing input file $1
fi

if [ ! -f $2 ]; then
  echo Missing output rules file $2
fi

for value in $( cat $1 )
do
  uv run main.py --rule-name $1 --header-field from --file-path $2 --dest-folder imap://USER@imap.example.com/$1 --value $value
done

