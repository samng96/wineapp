# WineApp Web Client

Web-based frontend for the WineApp wine inventory management system.

## Features

- **Offline Support**: Full functionality when offline using IndexedDB for local storage
- **Automatic Sync**: Syncs changes with server when connection is restored
- **Modern UI**: Clean, responsive design that works on desktop and mobile
- **Real-time Status**: Shows online/offline status and sync capabilities

## Architecture

### Files

- `index.html` - Main HTML structure
- `styles.css` - All styling and responsive design
- `api.js` - API client for communicating with Flask backend
- `storage.js` - IndexedDB wrapper for local data storage
- `sync.js` - Synchronization manager for offline/online sync
- `app.js` - Main application logic and UI rendering

### Data Flow

1. **Online**: Data is fetched from server API and cached locally
2. **Offline**: All operations use local storage (IndexedDB)
3. **Sync**: When back online, local changes are pushed and server changes are pulled

## Setup

1. Make sure the Flask server is running on `http://localhost:5001`

2. Open `index.html` in a web browser, or use a local web server:

```bash
# Using Python's built-in server
cd webclient
python3 -m http.server 8000

# Then open http://localhost:8000 in your browser
```

## Usage

### Adding a Cellar
1. Click on the "Cellars" tab
2. Click "+ Add Cellar"
3. Fill in the form and submit

### Adding a Wine
1. Click on the "Wines" tab
2. Click "+ Add Wine"
3. Fill in required fields (Name, Type, Vintage) and submit

### Offline Mode
- The app automatically detects when you're offline
- All operations work offline and are queued for sync
- When you come back online, click "Sync" or wait for automatic sync

## Browser Compatibility

- Modern browsers with IndexedDB support
- Chrome, Firefox, Safari, Edge (latest versions)
- Mobile browsers supported

## Future Enhancements

- Search and filter functionality
- Detailed views for cellars and wines
- Wine instance management
- Graphical cellar visualization
- Conflict resolution UI
- Image upload for wine labels
