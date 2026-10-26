# Blockchain Expense Tracker

A college-level Python project using Streamlit and a custom educational blockchain.

## Features
- Add income and expense transactions
- Each transaction is stored in a block with a timestamp, previous hash, and SHA-256 hash
- Validate stored block hashes and chain links
- View income, expenses, net balance, category chart, and transaction history
- Export transactions as CSV and the chain as JSON
- Persist the chain locally in `blockchain_data.json`

## Requirements
- Python 3.10 or newer recommended
- pip

## Run on Windows
1. Extract the project ZIP.
2. Open Command Prompt or PowerShell in this folder.
3. Create a virtual environment (recommended):
   `python -m venv .venv`
4. Activate it:
   PowerShell: `.\.venv\Scripts\Activate.ps1`
   Command Prompt: `.venv\Scripts\activate.bat`
5. Install packages:
   `pip install -r requirements.txt`
6. Start the app:
   `streamlit run app.py`
7. Open the local URL printed in the terminal (usually http://localhost:8501).

## Data
The app creates `blockchain_data.json` in its working directory. Back it up before deleting or moving it.

## Important limitations
This is a teaching prototype, not a public blockchain. It uses a single local JSON file, has no distributed consensus, no login system, and no encryption at rest. A local attacker who can rewrite all blocks and hashes may be able to alter history. Hash validation is tamper-evidence, not a guarantee of absolute immutability.
