FROM etherpad/etherpad:1.8.18
COPY ep_minuteman/package.json ./ep_minuteman/package.json
RUN npm install --no-save --legacy-peer-deps ./ep_minuteman

# FIXME: create APIKEY in one place
RUN echo "10de317b2865d6f9fe8aa6704fa530f301582e8c65ee6b590c280c974cda13db" > APIKEY.txt
COPY ep_minuteman ./ep_minuteman

# TODO: remove the installed ballast?
