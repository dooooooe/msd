@echo off
cd /d %~dp0
git fetch origin
git reset --hard origin/main
python main.py