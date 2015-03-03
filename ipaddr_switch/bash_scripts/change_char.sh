#!/bin/bash
file=$(find .. -path "../bash_scripts" -a -prune  -o -name "*.py" -print | grep -v "__init__.py")
mkdir -p temp/libs/
for i in $file
do
    newfile=$(echo $i | cut -d / -f 2-3)
    iconv -f utf-8 -t gbk $i > temp/$newfile
    /bin/cp -f temp/$newfile ../$newfile
done
