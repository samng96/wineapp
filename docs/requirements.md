# WineApp Requirements

## Overview
WineApp is a personal wine inventory management system that allows users to track, organize, and manage their wine collection.

## Functional Requirements

### 1. Cellar Management
#### 1.1 Add Cellar
The user should be able to add multiple cellars to their app. A cellar needs to have:
- Rows
    - Each row must be able to specify how many bottles per row, and whether the row is just one-sided or if there is front and back
- Cellar would ideally be able to also specify metadata like:
    - Temperature
    - Capacity

#### 1.2 Delete Cellar
The user should be able to delete a cellar if they no longer have it. Any wines in the cellar deleted will be added to an unshelved list, which is also where all newly scanned wines will go.

#### 1.3 View Cellar
The user should be able to view their cellar graphically. The view should show each row, and the label for each wine on each row. Clicking on individual wines will bring up the wine view for the selected wine.

### 2. Wine Management
#### 2.1 Add Wine
Users should be able to add new wines to their inventory. They should be able to do this by scanning the label of the wine, having the app look up the wine online (via InVintory or TotalWine or some other service) to auto-populate the wine's details.
- When we add a wine, user should be able to determine if they've purchased the wine before; if so, we should refer to the same instance and have it keep tally of each purchase/consumption date.
- This likely means we need a singleton that tracks each wine reference, and then a separate entity for instances.

Reference:
- Required fields:
    - Name
    - Type (Red, White, Rosé, Sparkling, etc.)
    - Vintage (year)
- Optional fields:
    - Producer/Winery
    - Varietal(s)
    - Region
    - Country
    - Rating (1-5 stars)
    - Tasting Notes
    - Label Image (URL to blob storage location)
Instance
- ID to the reference
- Location (where stored) - this should allow the user to pull up the location in the cellar (which cellar, which row)
- Drink by date
- Price
- Purchase date

#### 1.2 View Wines
Users should be able to view all wines in their inventory. When viewing a wine, the user should be able to:
- See how many instances of the given wine they have
- See where each instance is located (ie which cellar)
- See when each instance was stored
- Show key information at a glance (name, type, vintage, quantity)

Users should also be able to see all the consumed wine of this reference type. This should be a togglable filter.

#### 1.3 Edit Wine
Users should be able to edit existing wine entries. It should be differentiable when they're editing the wine reference vs the wine instance. 

Update any field including quantity (when drinking/consuming). When consumed, the instance should be marked as consumed and should no longer occupy space in the cellar. It should still be tagged to the reference, and should still be searchable with the specific filter turned on.

#### 1.4 Delete Wine
Users should be able to remove wines from their inventory. This is different than consuming - this removes the entry altogether (ie a hard delete). 

Include confirmation to prevent accidental deletion

### 2. Search and Filter
#### 2.1 Search
- Users should be able to search wines by typing in a search box. That box will filter by relevance:
    - Name
    - Varietal
    - Vintage
    - Region
    - Everything else

#### 2.2 Filter
- Users should be able to filter wines by:
  - Type (Red, White, Rosé, etc.)
  - Vintage range
  - Rating
  - Country/Region
  - Whether consumed
  - Varietals
  - Producer
  - Date range added to the cellar
  - Price range

### 3. Data Persistence
Wine data should be stored persistently on the server.
Currently using JSON file storage (`wines.json`), but will eventually move to persistent storage like Dynamo.

### 4. Offline Access & Synchronization
#### 4.1 Offline Functionality
- Users should be able to access and modify their wine collection when offline
- All data (cellars, wine references, wine instances) must be cached locally on the client
- Changes made offline should be queued for synchronization when connection is restored
- The app should clearly indicate when it's operating in offline mode

#### 4.2 Synchronization
- When the client comes back online, it should automatically sync changes with the server
- Sync should be bidirectional (client → server and server → client)
- Sync should handle:
  - New items created offline
  - Updates made offline
  - Deletions made offline
  - Changes made on other devices while offline

#### 4.3 Conflict Resolution
- Server-side conflict resolution for automatically resolvable conflicts:
  - Last-write-wins for non-critical fields (with timestamp comparison)
  - Merge strategies for additive changes (e.g., adding instances to a reference)
  - Version-based conflict detection using timestamps or version numbers
- User-facing conflict resolution for unresolvable conflicts:
  - Present conflicts to the user in a clear, understandable format
  - Show both versions (local and server) side-by-side
  - Allow user to choose which version to keep, or manually merge
  - Prevent user confusion by clearly explaining what each version represents
  - Queue conflicts that can't be auto-resolved until user makes a decision

## Technical Requirements

### Backend (Server)
- Flask REST API
- CORS enabled for frontend communication
- JSON file-based storage (initial implementation)
  - Separate JSON files for: cellars, wine references, wine instances
  - Migration path to DynamoDB for production scalability
- **Synchronization and conflict resolution**
  - Timestamp/version tracking for all entities (createdAt, updatedAt, version)
  - Server-side conflict detection and resolution
  - Automatic resolution for non-conflicting changes
  - Conflict queue for user-resolvable conflicts
  - Sync endpoints that support batch operations
- Blob storage for wine label images
  - Store label images in cloud blob storage (AWS S3, Azure Blob Storage, or similar)
  - Wine references contain URL/link to blob storage location
  - Support for image upload and retrieval
- RESTful endpoints for CRUD operations
- External API integration for wine label scanning
  - Integration with wine lookup services (InVintory, TotalWine, or similar)
  - Image processing for label recognition
- Data model supporting:
  - Cellar management (multiple cellars with row-based organization)
  - Wine Reference/Instance pattern (singleton references, multiple instances)
  - Unshelved wine tracking
  - Consumed wine tracking (soft delete with filter capability)
  - Label image storage and retrieval
  - Version tracking and conflict resolution metadata

### Frontend (Client)
- Start with HTML/CSS/JavaScript
- Should communicate with Flask API via REST calls
- **Client-side caching and offline support**
  - Local storage (IndexedDB or similar) for full data cache
  - Cache all cellars, wine references, and wine instances locally
  - Queue offline changes for sync when connection is restored
  - Detect online/offline status and update UI accordingly
  - Background sync when connection is restored
- Responsive design for desktop and mobile
- Graphical cellar visualization
  - Visual representation of cellar rows
  - Interactive wine labels in cellar view
  - Click-to-view wine details
- Search and filter UI components
- Image capture/upload for wine label scanning
- **Conflict resolution UI**
  - Display conflicts in a user-friendly interface
  - Side-by-side comparison of conflicting versions
  - Allow user to select preferred version or manually merge
  - Clear messaging about what each version represents
- Modern, user-friendly interface
- Will add graphics and skinning later

### Data Architecture
- **Wine Reference** (Singleton pattern)
  - One reference per unique wine (name + vintage + producer)
  - Contains shared metadata (name, type, producer, varietal, region, country, rating, tasting notes)
  - Contains label image URL pointing to blob storage location
  - Version tracking for conflict resolution
- **Wine Instance** (Multiple per reference)
  - Links to wine reference via reference ID
  - Contains instance-specific data (location, purchase date, price, drink by date)
  - Tracks consumption status
  - Version tracking for conflict resolution
- **Cellar**
  - Contains multiple rows
  - Each row has capacity and side configuration (one-sided vs front/back)
  - Tracks metadata (temperature, capacity)
  - Maps wine instances to specific locations (cellar + row + position)
  - Version tracking for conflict resolution
- **Unshelved List**
  - Temporary storage for wines not yet assigned to a cellar
  - Includes newly scanned wines and wines from deleted cellars
- **Sync Metadata**
  - All entities include version numbers and timestamps (createdAt, updatedAt)
  - Client tracks lastSyncTimestamp for incremental sync
  - Conflict objects track both local and server versions for user resolution

## API Endpoints (Current & Planned)

### Cellar Endpoints
- `GET /cellars` - Get all cellars
- `POST /cellars` - Create a new cellar
- `GET /cellars/<id>` - Get a specific cellar with row layout
- `PUT /cellars/<id>` - Update cellar metadata
- `DELETE /cellars/<id>` - Delete a cellar (moves wines to unshelved)
- `GET /cellars/<id>/layout` - Get graphical layout of cellar rows and wine positions

### Wine Reference Endpoints
- `GET /wine-references` - Get all wine references
- `POST /wine-references` - Create a new wine reference
- `GET /wine-references/<id>` - Get a specific wine reference with all instances
- `PUT /wine-references/<id>` - Update wine reference metadata
- `DELETE /wine-references/<id>` - Hard delete a wine reference and all instances
- `GET /wine-references/search?q=<query>` - Search wine references by relevance
- `GET /wine-references/filter?type=<type>&vintage=<year>&country=<country>&varietal=<varietal>&producer=<producer>&rating=<rating>&consumed=<true|false>&priceMin=<min>&priceMax=<max>&dateFrom=<date>&dateTo=<date>` - Filter wine references

### Wine Instance Endpoints
- `GET /wine-instances` - Get all wine instances
- `POST /wine-instances` - Create a new wine instance (link to reference)
- `GET /wine-instances/<id>` - Get a specific wine instance
- `PUT /wine-instances/<id>` - Update wine instance (location, dates, price)
- `DELETE /wine-instances/<id>` - Hard delete a wine instance
- `POST /wine-instances/<id>/consume` - Mark instance as consumed (soft delete)
- `PUT /wine-instances/<id>/location` - Update instance location (cellar, row, position)

### Scanning Endpoints
- `POST /scan/label` - Upload wine label image for recognition
  - Returns: Wine data from external API (InVintory/TotalWine)
  - May return multiple matches for user selection
- `POST /scan/label/confirm` - Confirm scanned wine and create reference/instance

### Image Storage Endpoints
- `POST /images/upload` - Upload wine label image to blob storage
  - Returns: URL to stored image in blob storage
- `GET /images/<image-id>` - Retrieve image from blob storage (or direct blob storage URL)
- `DELETE /images/<image-id>` - Delete image from blob storage

### Unshelved Endpoints
- `GET /unshelved` - Get all unshelved wine instances
- `POST /unshelved/<instance-id>/assign` - Assign unshelved wine to a cellar location

### Synchronization Endpoints
- `POST /sync/check` - Check for updates since last sync
  - Request body: `{ "lastSyncTimestamp": "2024-01-15T10:30:00Z" }`
  - Returns: List of entities that have changed since last sync
- `POST /sync/push` - Push local changes to server
  - Request body: Array of create/update/delete operations
  - Returns: Sync result with conflicts (if any)
- `POST /sync/pull` - Pull latest changes from server
  - Request body: `{ "lastSyncTimestamp": "2024-01-15T10:30:00Z", "entityTypes": ["cellars", "wine-references", "wine-instances"] }`
  - Returns: All entities updated since last sync
- `POST /sync/resolve-conflict` - Resolve a user-confirmed conflict
  - Request body: `{ "entityType": "wine-reference", "entityId": "id", "resolution": "local|server|merged", "mergedData": {...} }`
  - Returns: Confirmation of resolution
- `GET /sync/conflicts` - Get all pending conflicts requiring user resolution
  - Returns: List of conflicts with both versions

## Data Model

### Cellar Object
```json
{
  "id": "unique-identifier",
  "name": "Main Cellar",
  "temperature": 55,
  "capacity": 500,
  "rows": [
    {
      "id": "row-1",
      "bottlesPerSide": 50,
      "sides": "front-back",
      "winePositions": {
        "front": ["instance-id-1", "instance-id-2", null, ...],
        "back": ["instance-id-3", null, ...]
      }
    },
    {
      "id": "row-2",
      "bottlesPerSide": 30,
      "sides": "single",
      "winePositions": {
        "single": ["instance-id-4", null, ...]
      }
    }
  ],
  "version": 5,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Wine Reference Object
```json
{
  "id": "unique-reference-id",
  "name": "Wine Name",
  "type": "Red|White|Rosé|Sparkling",
  "vintage": 2020,
  "producer": "Winery Name",
  "varietals": ["Cabernet Sauvignon", "Merlot"],
  "region": "Napa Valley",
  "country": "USA",
  "rating": 4,
  "tastingNotes": "Full-bodied with notes of blackberry...",
  "labelImageUrl": "https://blob-storage.example.com/wine-labels/unique-reference-id.jpg",
  "instanceCount": 3,
  "version": 3,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Wine Instance Object
```json
{
  "id": "unique-instance-id",
  "referenceId": "unique-reference-id",
  "location": {
    "type": "cellar|unshelved",
    "cellarId": "cellar-id-1",
    "rowId": "row-1",
    "side": "front",
    "position": 5
  },
  "price": 25.99,
  "purchaseDate": "2024-01-15",
  "drinkByDate": "2025-12-31",
  "consumed": false,
  "consumedDate": null,
  "storedDate": "2024-01-15T10:30:00Z",
  "version": 2,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Conflict Object
```json
{
  "id": "conflict-id",
  "entityType": "wine-reference|wine-instance|cellar",
  "entityId": "unique-entity-id",
  "localVersion": {
    "version": 3,
    "data": { /* local version of the entity */ },
    "updatedAt": "2024-01-15T11:00:00Z"
  },
  "serverVersion": {
    "version": 4,
    "data": { /* server version of the entity */ },
    "updatedAt": "2024-01-15T11:30:00Z"
  },
  "conflictFields": ["name", "rating"],
  "createdAt": "2024-01-15T11:35:00Z"
}
```

## Future Enhancements (Out of Scope for MVP)
- User authentication
- Multiple user support
- Wine recommendations
- Barcode scanning (beyond label scanning)
- Advanced photo management (multiple photos per wine)
- Export/Import functionality
- Statistics and analytics dashboard
- Mobile native app
- Wine aging predictions
- Food pairing suggestions
- Price tracking over time
