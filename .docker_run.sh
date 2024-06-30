#!/bin/bash

set -e

apk add --update git bash python3 py-pip sshpass

pip install --break-system-packages -r requirements.txt

python main.py
