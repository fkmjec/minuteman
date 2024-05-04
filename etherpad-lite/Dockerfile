FROM etherpad/etherpad:1.8.18
COPY ep_minuteman/package.json ./ep_minuteman/package.json
RUN npm install --no-save --legacy-peer-deps ./ep_minuteman
RUN npm install --no-save --legacy-peer-deps ep_disable_chat

COPY APIKEY.txt ./
COPY --chown=etherpad wait-for-it.sh /opt/etherpad-lite
COPY --chown=etherpad entrypoint.sh /opt/etherpad-lite
RUN ["chmod", "+x", "/opt/etherpad-lite/wait-for-it.sh"]
RUN ["chmod", "+x", "/opt/etherpad-lite/entrypoint.sh"]
COPY ep_minuteman ./ep_minuteman

# ENTRYPOINT ["./entrypoint.sh"]
CMD ["node", "src/node/server.js"]
