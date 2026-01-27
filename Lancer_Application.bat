@echo off
REM Lanceur pour Gestion Commerciale GICA
REM Ce script lance l'application compilée

cd /d "%~dp0dist\GestionCommerciale_GICA"
start "" "GestionCommerciale_GICA.exe"
