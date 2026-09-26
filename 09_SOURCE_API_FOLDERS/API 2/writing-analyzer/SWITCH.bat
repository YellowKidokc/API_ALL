@echo off
:: ============================================================
::  Switch Corpus  —  Change which series you're analysing
::  Double-click, pick a number, done.
:: ============================================================
title Switch Corpus
cd /d "%~dp0"
python "%~dp0switch_corpus.py"
