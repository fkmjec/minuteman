# Minuteman
## How to set up
* clone the repository with `--recurse-submodules`
* create an Etherpad API key and put it into `etherpad-lite/APIKEY.txt`
* copy the Etherpad API key into `docker-compose.yml` file
* create a Flask secret key and put it into `docker-compose.yml`
* set env variables in compose to something sensible
* build using docker compose build
* run using docker compose up