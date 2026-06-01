# Bybit Account Manager

A desktop app to track and manage Bybit accounts — costs, deposits, withdrawals, and profit/loss — all in one place.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.11-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
[![Build](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build.yml)

## Features

- Add, edit, and delete accounts
- Track KYC cost, selfie cost, deposits, and withdrawals
- Auto-calculated profit/loss per account and overall summary
- Filter by status: In Progress, Done & Eligible, Done (Not Eligible)
- Backup data to a JSON file and restore from backup (merge or replace)
- Settings panel with import/export

## Download

Grab the latest `BytbitManager.exe` from the [Releases](../../releases/latest) page.  
No installation needed — just run the `.exe`.

> **Note:** Windows SmartScreen may warn on first run since the app is unsigned.  
> Click **More info → Run anyway** to proceed.

## Running from Source

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
pip install -r requirements.txt
python native_desktop_app.py
```

## Building the EXE Locally

```bash
pip install -r requirements.txt

# Convert icon
python -c "from PIL import Image; img=Image.open('Bybit.png').convert('RGBA'); img.save('Bybit.ico',format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"

# Build
pyinstaller --onefile --windowed --icon=Bybit.ico --add-data "Bybit.png;." --add-data "Bybit.ico;." --name BytbitManager native_desktop_app.py
```

Output: `dist/BytbitManager.exe`

## Data Storage

Account data is saved to `accounts_data.json` in the same folder as the `.exe`.  
Back it up regularly using the built-in **Settings → Export Backup** feature.

## License

MIT
