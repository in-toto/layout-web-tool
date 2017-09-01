#!/bin/bash

mkdir -p /data/db
mongod &
mkdir instance
echo 'DEBUG=False' >> instance/config.py
echo "SECRET_KEY='?\xbf,\xb4\x8d\xa3<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'" >> instance/config.py
python wizard.py
