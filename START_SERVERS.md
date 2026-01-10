# Starting the Wine App Servers

## 1. Start the Flask Backend Server

Open a terminal and run from the **project root**:
```bash
cd /Users/samng/Docs/src/WineApp
PYTHONPATH=. python3 server/app.py
```

Or with debugpy enabled (for debugging):
```bash
cd /Users/samng/Docs/src/WineApp
DEBUGPY=1 PYTHONPATH=. python3 server/app.py
```

**Important:** You must run from the project root (not from the `server/` directory) and set `PYTHONPATH=.` because the code uses `from server.utils import ...` style imports.

The server will start on **port 5001** (not 5000).

You should see:
```
Loading wine references into registry on startup...
Loaded X wine references into registry
Debugpy listening on port 5678. Attach debugger now.  (only if DEBUGPY=1)
 * Running on http://127.0.0.1:5001
```

## 2. Start the Frontend Web Server

Open a **second terminal** and run:
```bash
cd /Users/samng/Docs/src/WineApp
python3 webclient/dev_server.py webclient
```

**Note:** We use a custom development server (`dev_server.py`) that sends no-cache headers to prevent browser caching issues. If you see stale code after refreshing, use:
- **Hard refresh**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)
- Or use the development server which prevents caching automatically

The frontend will be available at:
```
http://localhost:8000
```

## 3. Access the App

Open your browser and go to:
```
http://localhost:8000
```

## Troubleshooting

- If you see JavaScript errors in the browser console, check that all files are loading
- Make sure both servers are running in separate terminals
- The Flask server must be on port 5001 (the API will need to be updated to match)
