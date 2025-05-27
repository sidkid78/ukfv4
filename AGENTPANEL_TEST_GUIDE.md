# Quick Setup and Test Guide for AgentPanel

## 🚀 Setup Steps

### 1. Install Backend Dependencies
```bash
cd backend
pip install -e .
```

### 2. Install Frontend Dependencies  
```bash
cd frontend
npm install
```

### 3. Start Both Servers
```bash
# Use the PowerShell script (from project root)
.\start-servers.ps1

# OR start manually:
# Terminal 1: cd backend && uvicorn main:app --reload
# Terminal 2: cd frontend && npm run dev
```

## 🧪 Testing AgentPanel

### Test Flow:
1. **Open**: http://localhost:3000
2. **Navigate**: Start Simulation → Create a session
3. **Go to Session Page**: You should see the Agent tab
4. **Test Agent Spawning**:
   - Click "Spawn Agent" button
   - Fill: Name="Test Agent", Role="RESEARCHER", Persona="analyst"
   - Click "Spawn Agent"
   - Should see success toast and agent appear in active list

### Expected Results:
- ✅ Agent appears in "Active Agents" section with green dot
- ✅ Shows agent name, role, and persona badge
- ✅ Success toast notification
- ✅ Agent counter updates

### Test Agent Termination:
- Click the trash icon next to an active agent
- Should see success toast and agent moves to "Inactive Agents"

## 🔧 Troubleshooting

### If spawning fails:
1. Check browser DevTools → Network tab for 500 errors
2. Check backend terminal for Python errors
3. Verify backend is running on port 8000

### If no agents show:
1. Check browser DevTools → Console for JavaScript errors
2. Verify API call to `/api/agent/list` succeeds

### Common Issues:
- **CORS errors**: Backend should have CORS middleware enabled
- **404 errors**: Check API endpoints match between frontend/backend
- **Toast not showing**: Verify Toaster component is in providers

## 🎯 What's Fixed:
- ✅ Backend returns full Agent object (not just ID)
- ✅ API endpoints match (`/api/agent/spawn`, `/api/agent/list`, etc.)
- ✅ Agent types synchronized between frontend/backend
- ✅ Proper error handling and toast notifications
- ✅ Agent timestamps and status tracking

## 🔄 Next Steps After AgentPanel Works:
1. **PluginPanel** - KA management interface
2. **TraceLog** - Live trace display
3. **ConfidenceMeter** - Visual confidence scoring
4. **WebSocket Integration** - Real-time updates
5. **Memory Visualization** - 13D memory graph display
