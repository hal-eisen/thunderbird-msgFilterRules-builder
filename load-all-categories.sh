#!/bin/bash

for category in Travel Life Shopping Jobs Fun Friends
do
  ./load-one-category.sh $category $1
done

