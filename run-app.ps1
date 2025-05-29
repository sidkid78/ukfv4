# PowerShell script to set up and run both backend and frontend

# Activate Python virtual environment (Windows)
Write-Host 'Activating Python virtual environment...'
. ./backend/.venv/Scripts/Activate.ps1

Write-Host 'Installing backend dependencies...'
pip install -r ./backend/requirements.txt

# Start backend (adjust if your backend entrypoint is different)
Write-Host 'Starting backend server...'
Start-Process powershell -ArgumentList '-NoExit','-Command', 'cd backend; uvicorn app.main:app --reload' # Change as needed

# Setup & start frontend
Write-Host 'Setting up frontend dependencies...'
cd frontend
npm install
Write-Host 'Starting frontend dev server...'
npm run dev

# Open the frontend in the default browser (change port if needed)
Start-Process "http://localhost:3000"
