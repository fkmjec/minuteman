FROM etherpad/etherpad:latest

COPY ep_minuteman ./ep_minuteman
RUN npm install --no-save --legacy-peer-deps ./ep_minuteman
# TODO: remove the installed ballast?
