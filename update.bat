@echo off
cd /d %~dp0
git fetch origin
git reset --hard origin/master
python main.py 