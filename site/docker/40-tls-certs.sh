#!/bin/sh
# 有已启用证书则用卷内 PEM；否则用仓库自带的本机占位证书，保证 nginx 能 listen 443。
mkdir -p /etc/nginx/certs
if [ -f /tls/cert.pem ] && [ -f /tls/key.pem ]; then
  cp /tls/cert.pem /etc/nginx/certs/cert.pem
  cp /tls/key.pem /etc/nginx/certs/key.pem
elif [ -f /etc/nginx/dummy/cert.pem ] && [ -f /etc/nginx/dummy/key.pem ]; then
  cp /etc/nginx/dummy/cert.pem /etc/nginx/certs/cert.pem
  cp /etc/nginx/dummy/key.pem /etc/nginx/certs/key.pem
fi
