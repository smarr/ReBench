#!/bin/sh
nosetests-2.7 --with-coverage --cover-inclusive --cover-branches --cover-html --cover-html-dir=cover-results --cover-package=rebench --cover-erase --cover-tests
