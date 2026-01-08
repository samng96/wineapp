# Debugging in Cursor

## Option 1: Chrome Debugging (Recommended)

### Setup:
1. Make sure your servers are running:
   ```bash
   # Terminal 1 - Flask server
   cd server && python3 app.py
   
   # Terminal 2 - Web server
   cd webclient && python3 -m http.server 8000
   ```

2. In Cursor:
   - Press `F5` or go to **Run and Debug** (Cmd+Shift+D / Ctrl+Shift+D)
   - Select **"Launch Chrome against localhost"** from the dropdown
   - Click the green play button or press `F5`

3. Chrome will open with debugging enabled
   - Set breakpoints by clicking in the gutter (left of line numbers)
   - The debugger will pause at breakpoints
   - Use the debug toolbar:
     - **Continue** (F5)
     - **Step Over** (F10)
     - **Step Into** (F11)
     - **Step Out** (Shift+F11)
     - **Restart** (Cmd+Shift+F5)
     - **Stop** (Shift+F5)

### Setting Breakpoints:
- Click in the gutter (left of line numbers) in `webclient/app.js`
- Red dots indicate breakpoints
- The debugger will pause when execution reaches them

### Inspecting Variables:
- **Variables panel**: Shows local variables, `this`, closures
- **Watch panel**: Add expressions to watch (e.g., `window.app`, `typeof WineApp`)
- **Call Stack**: See the execution path
- **Debug Console**: Type JavaScript expressions to evaluate

## Option 2: Attach to Running Chrome

If Chrome is already running:

1. Start Chrome with debugging enabled:
   ```bash
   # macOS
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   
   # Or add to Chrome shortcut:
   # --remote-debugging-port=9222
   ```

2. In Cursor:
   - Press `F5`
   - Select **"Attach to Chrome"**
   - Click the green play button

## Option 3: Node.js Debugging (for server-side)

For debugging the Flask server:

1. Install Python debugger extension if needed
2. Press `F5`
3. Select **"Debug Flask Server"**
4. Set breakpoints in `server/*.py` files

## Quick Debugging Steps

1. **Set breakpoints** in `webclient/app.js`:
   - Line 8 (constructor start)
   - Line 252 (DOMContentLoaded)
   - Line 260 (before `new WineApp()`)
   - Line 175 (showView method)

2. **Press F5** to start debugging

3. **When paused**:
   - Check **Variables** panel for `window.app`, `WineApp`, etc.
   - Use **Debug Console** to type: `typeof WineApp`, `window.app.showView`
   - Step through with F10/F11

4. **Common things to check**:
   - Is `WineApp` defined? (type in console: `typeof WineApp`)
   - Is `window.app` created? (check Variables panel)
   - Does `window.app.showView` exist? (expand `window.app` in Variables)

## Troubleshooting

- **"Cannot connect to Chrome"**: Make sure Chrome isn't already running, or use "Attach" mode
- **Breakpoints not hitting**: Check that source maps are enabled, or try refreshing
- **Files not showing**: Make sure `webRoot` in launch.json points to the right directory
