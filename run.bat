@echo off
REM Script de lancement pour le visualiseur EPUB/PDF

echo ========================================
echo Visualiseur de couvertures EPUB et PDF
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Lancer l'application
python main.py

REM Désactiver l'environnement virtuel à la fin
deactivate
