#!/usr/bin/env bash

ssh-keyscan ${BB_SERVER_URL} >> ~/.ssh/known_hosts
echo "${SSH_KEY}" >> /root/.ssh/id_rsa
echo "${SSH_PUB}" >> /root/.ssh/id_rsa.pub
chmod 600 /root/.ssh/id_rsa
chmod 644 /root/.ssh/id_rsa.pub

# 21600 seconds = 6 hours
INTERVAL=${INTERVAL:-21600}

while bbmigrate \
  --server-url  $BB_SERVER_URL \
  --server-user $BB_SERVER_USER \
  --server-pass $BB_SERVER_PASS \
  --workspace   $BB_WORKSPACE \
  --cloud-user  $BB_CLOUD_USER \
  --cloud-pass  $BB_CLOUD_PASS \
  ; do

  echo "Sleeping for ${INTERVAL} seconds..."
  sleep $INTERVAL
done
