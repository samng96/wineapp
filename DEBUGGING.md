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
