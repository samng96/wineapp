# Debugging the Wine App

## Using Browser Developer Tools

### 1. Open Developer Tools
- **Chrome/Edge**: Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
- **Firefox**: Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
- **Safari**: Enable Developer menu first (Preferences → Advanced → Show Develop menu), then `Cmd+Option+I`

### 2. Set Breakpoints

1. Go to the **Sources** tab (Chrome) or **Debugger** tab (Firefox)
2. In the file tree on the left, navigate to:
   - `webclient/app.js`
   - `webclient/cellarManager.js`
   - `webclient/debug.js`

3. Click on the line number where you want to pause:
   - Line 8 in `app.js` (inside WineApp constructor)
   - Line 238 in `app.js` (DOMContentLoaded handler)
   - Line 241 in `app.js` (where `new WineApp()` is called)

### 3. Step Through Code

Once paused at a breakpoint:
- **F10** or **Step Over**: Execute current line, don't go into functions
- **F11** or **Step Into**: Go into function calls
- **Shift+F11** or **Step Out**: Exit current function
- **F8** or **Resume**: Continue execution

### 4. Inspect Variables

While paused:
- Hover over variables to see their values
- Use the **Console** tab to type variable names
- Check the **Scope** panel to see all available variables
- Use `console.log()` in the console to inspect values

### 5. Watch Expressions

1. In the **Sources/Debugger** tab, find the **Watch** panel
2. Click **+** to add a watch expression
3. Add expressions like:
   - `window.app`
   - `typeof WineApp`
   - `window.app.showView`

### 6. Check for Errors

1. Go to the **Console** tab
2. Look for red error messages
3. Click on errors to see the stack trace
4. Check the **Network** tab to see if files are loading (status 200)

## Quick Debugging Steps

1. **Open the app** at `http://localhost:8000`
2. **Open DevTools** (F12)
3. **Go to Sources tab**
4. **Set a breakpoint** at line 241 in `app.js` (where `new WineApp()` is called)
5. **Refresh the page** - it should pause at the breakpoint
6. **Step through** (F10) to see what happens
7. **Inspect** `WineApp` variable - is it defined?
8. **Step into** (F11) the `new WineApp()` call
9. **Check** if the constructor is called
10. **Inspect** `window.app` after it's created

## Common Issues to Check

- **Module not loading**: Check Network tab for 404 errors
- **Import errors**: Look for red errors in Console
- **Class not defined**: Check if `typeof WineApp === 'function'`
- **Object empty**: Check if constructor threw an error
- **Stale code after refresh**: Browser caching issue - see "Caching Issues" below

## Caching Issues

If you're not seeing your latest code changes after refreshing:

### Quick Solutions:
1. **Hard Refresh** (recommended):
   - Mac: `Cmd + Shift + R`
   - Windows/Linux: `Ctrl + Shift + R`

2. **Disable Cache in DevTools**:
   - Open DevTools (F12)
   - Go to **Network** tab
   - Check **"Disable cache"** checkbox
   - Keep DevTools open while developing

3. **Use the Development Server**:
   - The `dev_server.py` script sends no-cache headers automatically
   - Run: `python3 webclient/dev_server.py webclient`
   - Or use `start_servers.sh` which uses the dev server

4. **Clear Browser Cache**:
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Or: Right-click refresh button → "Empty Cache and Hard Reload"

## Using Console Commands

While debugging, you can type these in the Console:

```javascript
// Check if WineApp is defined
typeof WineApp

// Check if app exists
window.app

// Check app's methods
Object.getOwnPropertyNames(Object.getPrototypeOf(window.app))

// Try calling showView directly
window.app.showView('cellar')

// Check for errors
window.onerror
```

## Debugging the Flask Server

### 1. Flask Debug Mode (Already Enabled)

The server runs with `debug=True`, which provides:
- **Interactive Debugger**: When an error occurs, you'll see a stack trace with an interactive debugger in the browser
- **Auto-reload**: Code changes automatically restart the server (currently disabled with `use_reloader=False`)

### 2. Using Python Debugger (pdb)

Add breakpoints in your Python code:

```python
import pdb; pdb.set_trace()  # Add this line where you want to break
```

Example in `server/cellars.py`:
```python
@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def delete_cellar(cellar_id: str):
    import pdb; pdb.set_trace()  # Breaks here
    cellar = find_cellar_by_id(cellar_id)
    # ... rest of code
```

**Debugger Commands**:
- `n` (next): Execute next line
- `s` (step): Step into function calls
- `c` (continue): Continue execution
- `p variable_name`: Print variable value
- `l` (list): Show code around current line
- `q` (quit): Quit debugger
- `h` (help): Show help

### 3. Adding Print Statements / Logging

Add `print()` statements to see what's happening:

```python
@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def delete_cellar(cellar_id: str):
    print(f"DELETE request for cellar: {cellar_id}")
    cellar = find_cellar_by_id(cellar_id)
    print(f"Found cellar: {cellar}")
    # ... rest of code
```

Or use Python's logging module:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def delete_cellar(cellar_id: str):
    logger.debug(f"DELETE request for cellar: {cellar_id}")
    cellar = find_cellar_by_id(cellar_id)
    logger.debug(f"Found cellar: {cellar}")
```

### 4. Debugging with VS Code

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/server/app.py",
            "console": "integratedTerminal",
            "env": {
                "FLASK_APP": "server/app.py",
                "FLASK_ENV": "development"
            },
            "justMyCode": true
        }
    ]
}
```

Then:
1. Set breakpoints by clicking left of line numbers
2. Press F5 to start debugging
3. Execution will pause at breakpoints
4. Use debug panel to inspect variables, step through code, etc.

### 5. Viewing Server Logs

The Flask server prints logs to the terminal where you started it. Watch for:
- Request logs: `127.0.0.1 - - [TIMESTAMP] "GET /cellars HTTP/1.1" 200`
- Error messages: Stack traces and error details
- Print statements: Any `print()` output appears here

### 6. Testing API Endpoints

Use `curl` to test endpoints directly:

```bash
# Test GET all cellars
curl http://localhost:5001/cellars

# Test DELETE a cellar
curl -X DELETE http://localhost:5001/cellars/{cellar_id}

# Test with verbose output
curl -v -X DELETE http://localhost:5001/cellars/{cellar_id}
```

### 7. Common Server Debugging Scenarios

**Error 500 (Internal Server Error)**:
- Check terminal output for Python stack trace
- The Flask debugger page shows the error and stack trace
- Look for the PIN code at the top to access interactive debugger

**Error 404 (Not Found)**:
- Verify the route is registered: Check `app.register_blueprint()` calls
- Verify the route path matches the request URL
- Check that the blueprint prefix is correct

**Error 405 (Method Not Allowed)**:
- Check that the HTTP method matches: `@route(..., methods=['DELETE'])`
- Verify you're using the correct HTTP method in the request

**Data Not Saving**:
- Check file permissions on data files
- Verify JSON file paths are correct
- Check for JSON serialization errors

### 8. Enabling Auto-reload (Optional)

To automatically reload on code changes, change in `server/app.py`:

```python
app.run(debug=True, port=5001, host='127.0.0.1', use_reloader=True)
```

**Note**: This can cause issues during debugging, so it's currently disabled.
