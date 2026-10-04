#!/bin/sh
# 在任意目录运行：生成公开文件，保持已有数据库和命名卷，切换本地服务。
set -eu
site_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in
  "") build_flag=--build ;;
  --no-build) build_flag=--no-build ;;
  *) echo "Usage: sh site/preview.sh [--no-build]" >&2; exit 2 ;;
esac
python3 "$site_dir/scripts/build_site.py"
docker compose -f "$site_dir/docker-compose.yml" up -d "$build_flag" --wait kb-api
# 发布器整体替换 www；重新创建 Web 容器，避免 bind mount 仍指向上一目录 inode。
docker compose -f "$site_dir/docker-compose.yml" up -d --no-deps --force-recreate --wait web
