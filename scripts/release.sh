#!/bin/sh

if [ ! -z "`git diff`" ]; then 
    echo Please commit first
    exit
fi
git tag v`PYTHONPATH=. python -c 'import vi3o; print vi3o.__version__' 2>/dev/null | tail -1` || exit
git checkout stable || exit
tsocks git pull
git merge master || exit
tsocks git push
tsocks git push --tags
git checkout master
tsocks git push
