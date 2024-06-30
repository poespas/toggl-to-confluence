#!/bin/bash

docker run -it --rm --name python --workdir /var/www/html -v $(pwd):/var/www/html alpine:3 sh /var/www/html/.docker_run.sh

