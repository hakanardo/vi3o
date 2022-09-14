#!/bin/sh

if [ ! -z "`git diff`" ]; then 
    echo Please commit first
    exit
fi
TAG=v`PYTHONPATH=. python -c 'import vi3o; print (vi3o.__version__)' 2>/dev/null | tail -1`
REF=$(echo $TAG | sed -e 's/\./-/g')
gh release create $TAG --title $TAG --notes "See https://vi3o.readthedocs.io/en/stable/#$REF" || exit

git checkout stable || exit
git pull
git merge master || exit
git push
git push --tags
git checkout master
git push
