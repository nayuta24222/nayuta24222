#!/bin/sh
# ゲーム本体を desktop/app/ に同期してからビルドする
cd "$(dirname "$0")"
rm -rf app
mkdir -p app
cp -r ../index.html ../css ../js app/
echo "synced -> desktop/app/"
