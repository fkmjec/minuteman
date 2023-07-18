FROM etherpad/etherpad:1.8.18
COPY ep_minuteman/package.json ./ep_minuteman/package.json
RUN npm install --no-save --legacy-peer-deps ./ep_minuteman

COPY flask/APIKEY.txt ./APIKEY.txt
COPY ep_minuteman ./ep_minuteman

