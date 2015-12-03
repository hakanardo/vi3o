#!/bin/sh

if [ ! -z "`git diff`" ]; then 
    echo Please commit first
    exit
fi
git tag v`PYTHONPATH=. python -c 'import vi3o; print vi3o.__version__' 2>/dev/null | tail -1` || exit
git checkout stable || exit
git pull
git merge master || exit
git push 
git push --tags
git checkout master
git push 
