# WineApp Server Requirements

## Overview
WineApp is a personal wine inventory management system that allows users to track, organize, and manage their wine collection.

## Conventions
- Always follow the standard Python convention of naming where private methods are prefixed with underscore.
- Always create data classes for each of the data architectural elements
- Always track version history for updates to each element type. This is so that in the future we can handle conflict resolution.
- Always have a unique ID for each element type.

## Data architecture
1. Cellars
Cellars have the following fields:
- ID
- Name
- Capacity - this is calculated
- Temperature - this is specified by the user
- List of <Shelf> - this is specified by the user upon creation of the cellar.

2. Shelf
A shelf has the following fields:
- ID
- Number of positions
- Whether the shelf is a double shelf or not (boolean)
- A dictionary of WineInstance objects. Can be empty if there's no wine there, or can be a specific instance. Serialized as the ID, but loaded as the object itself.

Creating a shelf has 2 inputs: number of positions, and whether the shelf is a double shelf or not.
- As a result, the dictionary of WineInstance objects in the shelf has two dimensions: row dimension is either 1 if it is not a double shelf, or 2 if it is. Second dimension is number of positions.
- So for example, a shelf with num_positions:4 and isDouble:true will have a dictionary of WineInstance objects that is a 2D array with 2 rows and 4 columns.

3. WineReference
Wine References are singletons that are for each bottle type of wine. 
- Required fields:
    - ID
    - Name
    - Type (Red, White, Rosé, Sparkling, etc.)
- Optional fields:
    - Producer/Winery
    - Varietal(s)
    - Region
    - Country
    - Rating (1-5 stars)
    - Tasting Notes
    - Label Image (URL to blob storage location)

There should be a global registry of all the wine references that we have loaded into the system. We will try to de-dupe as much as possible.

4. WineInstance
Wine Instances are single instances of each reference wine.
- Required fields:
    - ID. This is used to refer to an instance, and will be stored as a part of shelves' serialization.
    - ID to the reference. This should be stored as an ID for serialization purposes, but should be loaded as an object based on the global WineReference registry. This is immutable.
    - Vintage (year)
    - Location - This should be a tuple of {cellarID, shelfIndex, positionIndex, isFront} where cellarID is the cellar, shelfIndex is the index of the shelf in the cellar, positionIndex is the position in the shelf, and isFront is whether or not it's front or back. These should also be loaded as objects for the Cellar and Shelf, and positionIndex/isFront can be loaded as their direct values.
    - IsConsumed - a boolean value for whether or not this wine has been consumed
- Optional fields
    - Drink by date (client code should obtain this from Vivino)
    - Price
    - Purchase date
    - Purchase location
    - Consumption date - when the WineInstance is consumed, this will be set to the consumption date.

## Functional Requirements
### 0. Unshelved wines.
This is a list of WineInstances.

Any new wines being added will automatically be first added to the unshelved list. The user can then move anything from unshelved to a specific cellar. Anytime a cellar is deleted, WineInstances in that cellar automatically get moved to the unshelved wines list.

### 1. Cellar Management API
- Add Cellar - The user should be able to add multiple cellars to their app. 
- Delete Cellar - The user should be able to delete a cellar if they no longer have it. Any wines in the cellar deleted will be added to an unshelved list, which is also where all newly scanned wines will go.
- Get Cellars - The user should be able to list all their cellars
- Get Cellar(id) - The user should be able to get a specific cellar by ID

### 2. Wine Reference Management API
- Wine References should be basic - the user should have standard CRUD operations on them.

### 3. Wine Instance Management API
- Wine Instance management should be basic as well - the user should be able to have standard CRUD operations on them. Additionally:
- Consume Wine - The user should be able to consume a wine - this will store the consumption date, and will mark the wine as consumed and will update the consumption date in the WineInstance.
- Move Wine - The user should be able to move WineInstances around in their collection - either moving to unshelved, or moving to a specific location (ie {cellar/shelf/position/isFront combination}).

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

### 1. Technology Stack
- **Backend Framework**: Flask (Python)
- **Data Storage**: JSON files (MVP), with migration path to DynamoDB
- **API Format**: RESTful JSON API
- **Version Control**: Git/GitHub
- **Testing**: pytest

### 2. Data Models

#### 2.1 Cellar Model
- **Class**: `Cellar` (dataclass)
- **Fields**:
  - `id: str` (UUID)
  - `name: str`
  - `shelves: List[Shelf]`
  - `temperature: Optional[int]`
  - `capacity: int` (auto-calculated from shelves)
  - `version: int` (for conflict resolution)
  - `created_at: Optional[str]` (ISO 8601 timestamp)
  - `updated_at: Optional[str]` (ISO 8601 timestamp)
- **Methods**:
  - `to_dict() -> Dict[str, Any]`: Serialize to JSON format (extracts IDs from objects when needed)
  - `from_dict(data: Dict, wine_instances: Dict) -> Cellar`: Deserialize from JSON (resolves IDs to objects)
  - `is_position_valid(shelf_index: int, side: str, position: int) -> bool`: Validate position
  - `is_position_available(shelf_index: int, side: str, position: int) -> bool`: Check if position is free
  - `assign_wine_to_position(shelf_index: int, side: str, position: int, instance: WineInstance)`: Assign wine instance object
  - `remove_wine_from_position(shelf_index: int, side: str, position: int)`: Remove wine
  - Private methods prefixed with `_`
  - **Note**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when needed (e.g., `instance.id`)

#### 2.2 Shelf Model
- **Class**: `Shelf` (dataclass)
- **Fields**:
  - `positions: int` (immutable after initialization)
  - `is_double: bool` (immutable after initialization)
  - `wine_positions: List[List[Optional[WineInstance]]]` (mutable 2D array)
    - Row dimension: 1 if `is_double=False`, 2 if `is_double=True`
    - Column dimension: `positions`
- **Methods**:
  - `to_tuple() -> List`: Serialize to `[positions, is_double]` format
  - `from_tuple(shelf_data: List, wine_positions_ids: Dict, wine_instances: Dict) -> Shelf`: Deserialize
  - `get_wine_at(side: str, position: int) -> Optional[WineInstance]`: Get wine instance object at position (returns object, not ID)
  - `set_wine_at(side: str, position: int, instance: Optional[WineInstance])`: Set wine instance object at position
  - Private methods prefixed with `_`
  - **Note**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when needed (e.g., `instance.id`)

#### 2.3 WineReference Model
- **Class**: `WineReference` (dataclass)
- **Global Registry**: `_wine_references_registry: Dict[str, WineReference]` (in-memory registry)
- **Fields**:
  - `id: str` (UUID)
  - `name: str`
  - `type: WineType` (enum: Red, White, Rose, Sparkling White, Sparkling Red, Other)
  - `vintage: Optional[int]`
  - `producer: Optional[str]`
  - `varietals: Optional[List[str]]`
  - `region: Optional[str]`
  - `country: Optional[str]`
  - `rating: Optional[int]` (1-5)
  - `tasting_notes: Optional[str]`
  - `label_image_url: Optional[str]` (URL to blob storage)
  - `vivino_url: Optional[str]` (URL to Vivino link where we imported information)
  - `version: int` (for conflict resolution)
  - `created_at: Optional[str]` (ISO 8601 timestamp)
  - `updated_at: Optional[str]` (ISO 8601 timestamp)
- **Methods**:
  - `to_dict() -> Dict[str, Any]`: Serialize to JSON format (includes `id` field from object)
  - `from_dict(data: Dict) -> WineReference`: Deserialize and auto-register in global registry
  - `get_unique_key() -> tuple`: Get unique key for deduplication (name, vintage, producer)
- **Registry Functions**:
  - `get_wine_reference(reference_id: str) -> Optional[WineReference]`: Get WineReference object from registry (returns object, not ID)
  - `register_wine_reference(reference: WineReference)`: Register WineReference object in global registry
  - `clear_wine_references_registry()`: Clear registry (for testing)
  - **Note**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when needed (e.g., `reference.id`)

#### 2.4 WineInstance Model
- **Class**: `WineInstance` (dataclass)
- **Fields**:
  - `id: str` (UUID)
  - `reference: WineReference` (object reference, not ID - loaded from global registry)
  - `location: Optional[Tuple[Cellar, Shelf, int, bool]]` (Cellar object, Shelf object, position, isFront) or None for unshelved
  - `price: Optional[float]`
  - `purchase_date: Optional[str]` (ISO 8601 date)
  - `drink_by_date: Optional[str]` (ISO 8601 date)
  - `consumed: bool`
  - `consumed_date: Optional[str]` (ISO 8601 timestamp)
  - `stored_date: Optional[str]` (ISO 8601 timestamp)
  - `version: int` (for conflict resolution)
  - `created_at: Optional[str]` (ISO 8601 timestamp)
  - `updated_at: Optional[str]` (ISO 8601 timestamp)
- **Methods**:
  - `to_dict() -> Dict[str, Any]`: Serialize location as `{cellarId, shelfIndex, position, isFront}` or None (extracts IDs from Cellar object via `cellar.id`, extracts shelfIndex from the list of shelves stored in the cellar object)
  - `from_dict(data: Dict, cellars: Optional[List[Cellar]]) -> WineInstance`: Deserialize location by looking up Cellar and Shelf objects
  - `_is_in_cellar() -> bool`: Check if in cellar (private)
  - `_is_unshelved() -> bool`: Check if unshelved (private)
  - `get_cellar_location() -> Optional[Dict]`: Get location details if in cellar (returns dict with IDs extracted from objects)
  - **Note**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when needed (e.g., `cellar.id`, `reference.id`)

### 3. API Endpoints

#### 3.1 Cellar Management
- `GET /cellars`
  - Returns: List of all cellars as JSON array
  - Response: `200 OK` with JSON array of cellar objects
  - Each cellar object includes: `id, name, temperature, capacity, shelves, winePositions, version, createdAt, updatedAt`
  - `shelves`: Array of `[positions, isDouble]` tuples
  - `winePositions`: Dict mapping shelf index to `{side: [instanceId, ...]}` format
  
- `GET /cellars/<cellar_id>`
  - Returns: Single cellar by ID
  - Response: `200 OK` with cellar object, or `404 Not Found` with `{error: "message"}`
  
- `POST /cellars`
  - Request Body: `{name: str, temperature?: int, shelves: [[positions: int, isDouble: bool], ...]}`
  - `shelves`: Array of shelf tuples `[positions, isDouble]`
  - Returns: Created cellar with generated ID, auto-calculated capacity, version=1, timestamps
  - Response: `201 Created` with cellar object
  - Validation: Returns `400 Bad Request` if shelf format is invalid
  
- `PUT /cellars/<cellar_id>`
  - Request Body: `{name?: str, temperature?: int, shelves?: [[positions, isDouble], ...]}`
  - All fields optional - only provided fields are updated
  - Returns: Updated cellar with incremented version, updated timestamp
  - Response: `200 OK` with updated cellar object, or `404 Not Found`
  - Note: Updating shelves preserves existing wine positions where possible
  
- `DELETE /cellars/<cellar_id>`
  - Moves all wine instances in cellar to unshelved (sets location to `None`)
  - Updates version and timestamps on affected wine instances
  - Response: `200 OK` with `{message: "Cellar deleted"}`, or `404 Not Found`
  
- `GET /cellars/<cellar_id>/layout`
  - Returns: Graphical layout of cellar with wine positions
  - Response: `200 OK` with layout object (cellar dict with wine positions), or `404 Not Found`

#### 3.2 Wine Reference Management
- `GET /wine-references`
  - Returns: List of all wine references as JSON array
  - Response: `200 OK` with JSON array of wine reference objects
  - Each reference includes: `id, name, type, vintage?, producer?, varietals?, region?, country?, rating?, tastingNotes?, labelImageUrl?, instanceCount, version, createdAt, updatedAt`
  - Note: References are loaded from global registry
  
- `GET /wine-references/<reference_id>`
  - Returns: Single wine reference by ID with all associated instances
  - Response: `200 OK` with wine reference object plus `instances` array, or `404 Not Found`
  - `instances`: Array of all wine instances (both active and consumed) for this reference
  
- `POST /wine-references`
  - Request Body: Wine reference fields
    - Required: `name: str, type: str` (e.g., "Red", "White", "Rosé", "Sparkling", etc.)
    - Optional: `vintage?: int, producer?: str, varietals?: string[], region?: str, country?: str, rating?: int (1-5), tastingNotes?: str, labelImageUrl?: str`
  - Returns: Created wine reference with generated ID, `instanceCount=0`, version=1, timestamps
  - Response: `201 Created` with wine reference object
  - Auto-registers in global registry
  - Deduplication: Returns `409 Conflict` if reference with same `(name, vintage, producer)` already exists, includes existing reference in response
  
- `PUT /wine-references/<reference_id>`
  - Request Body: Updated wine reference fields (all optional)
    - Any field can be updated: `name?, type?, vintage?, producer?, varietals?, region?, country?, rating?, tastingNotes?, labelImageUrl?`
  - Returns: Updated wine reference with incremented version, updated timestamp
  - Response: `200 OK` with updated wine reference object, or `404 Not Found`
  - Note: Updates are applied to the model object and global registry
  
- `DELETE /wine-references/<reference_id>`
  - Hard delete (removes from system and registry)
  - Response: `200 OK` with `{message: "Wine reference deleted"}`, or `404 Not Found`
  - Note: Does not delete associated wine instances

#### 3.3 Wine Instance Management
- `GET /wine-instances`
  - Returns: List of all wine instances as JSON array
  - Response: `200 OK` with JSON array of wine instance objects
  - Each instance includes: `id, referenceId, location?, price?, purchaseDate?, drinkByDate?, consumed, consumedDate?, storedDate?, version, createdAt, updatedAt`
  - `location`: `{cellarId, shelfIndex, position, isFront}` or `null` for unshelved
  
- `GET /wine-instances/<instance_id>`
  - Returns: Single wine instance by ID
  - Response: `200 OK` with wine instance object, or `404 Not Found`
  
- `POST /wine-instances`
  - Request Body: `{referenceId: str, location?: object, price?: float, purchaseDate?: str, drinkByDate?: str}`
  - Location format (optional):
    - For cellar: `{type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}`
    - For unshelved: `{type: "unshelved"}` or `null` or omitted
  - Returns: Created wine instance with generated ID, `consumed=false`, `storedDate` set to current timestamp, version=1, timestamps
  - Response: `201 Created` with wine instance object
  - Auto-updates `instanceCount` on associated WineReference
  - Validation: Returns `404 Not Found` if `referenceId` doesn't exist
  - Note: Location is converted to tuple format `(Cellar, Shelf, position, isFront)` internally
  
- `PUT /wine-instances/<instance_id>`
  - Request Body: Updated wine instance fields (all optional)
    - Any field can be updated: `price?, purchaseDate?, drinkByDate?`
    - Note: `referenceId` and `location` should be updated via specific endpoints
  - Returns: Updated wine instance with incremented version, updated timestamp
  - Response: `200 OK` with updated wine instance object, or `404 Not Found`
  
- `DELETE /wine-instances/<instance_id>`
  - Hard delete (removes from system)
  - Removes from cellar position if applicable (calls `cellar.remove_wine_from_position()`)
  - Updates `instanceCount` on associated WineReference
  - Response: `200 OK` with `{message: "Wine instance deleted"}`, or `404 Not Found`
  
- `POST /wine-instances/<instance_id>/consume`
  - Marks wine instance as consumed
  - Sets `consumed=true` and `consumedDate` to current timestamp
  - Removes from cellar position if applicable (calls `cellar.remove_wine_from_position()`)
  - Sets `location` to `None` (unshelved)
  - Updates version and timestamp
  - Updates `instanceCount` on associated WineReference
  - Response: `200 OK` with updated wine instance object, or `404 Not Found`
  
- `PUT /wine-instances/<instance_id>/location`
  - Request Body: `{location: object | null}`
  - Location format:
    - For cellar: `{type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}`
    - For unshelved: `null` or `{type: "unshelved"}`
  - Moves wine instance to new location
  - Validates position using `cellar.is_position_valid()`
  - Checks availability using `cellar.is_position_available()` (allows same instance to stay in place)
  - Removes from old position if moving within same cellar
  - Assigns to new position using `cellar.assign_wine_to_position()` (passes WineInstance object)
  - Converts location to tuple format internally: `(Cellar, Shelf, position, isFront)`
  - Updates version and timestamp
  - Response: `200 OK` with updated wine instance object
  - Error responses:
    - `400 Bad Request` if location format is invalid, position is invalid, or position is occupied
    - `404 Not Found` if wine instance or cellar doesn't exist

#### 3.4 Unshelved Wines
- `GET /unshelved`
  - Returns: List of all unshelved wine instances (where `location` is `None` and `consumed` is `false`)
  - Response: `200 OK` with JSON array of wine instance objects
  - Note: Uses model objects internally, filters by `instance.location is None`
  
- `POST /unshelved/<instance_id>/assign`
  - Request Body: `{location: {type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}}`
  - Assigns unshelved wine to a cellar position
  - Validates position using `cellar.is_position_valid()`
  - Checks availability using `cellar.is_position_available()`
  - Assigns using `cellar.assign_wine_to_position()` (passes WineInstance object)
  - Converts location to tuple format: `(Cellar, Shelf, position, isFront)`
  - Updates version and timestamp
  - Response: `200 OK` with updated wine instance object
  - Error responses:
    - `400 Bad Request` if location format is invalid, position is invalid, or position is occupied
    - `404 Not Found` if wine instance or cellar doesn't exist

### 4. Data Persistence

#### 4.1 File Structure
- `server/data/cellars.json`: Array of cellar objects
- `server/data/wine-references.json`: Array of wine reference objects
- `server/data/wine-instances.json`: Array of wine instance objects

#### 4.2 Serialization Format
- All dates/timestamps: ISO 8601 format strings
- **General Rule**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when serializing to JSON (e.g., `cellar.id`, `reference.id`, `instance.id`)
- Location serialization:
  - In-memory: `(Cellar object, Shelf object, position: int, isFront: bool)` or `None`
  - JSON (serialized): `{cellarId: str, shelfIndex: int, position: int, isFront: bool}` or `null`
  - JSON (request format): `{type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}` or `null`/`{type: "unshelved"}`
  - IDs extracted from objects: `cellar.id` for `cellarId`, `shelf` found by index in `cellar.shelves`
  - Conversion: Request `side` string converted to `isFront` boolean (front=true, back=false, single=true)
- Shelf serialization:
  - In-memory: `Shelf` object with `wine_positions` as 2D array of `WineInstance` objects
  - JSON: `[positions, isDouble]` for shelf config, `{side: [instanceId, ...]}` for wine positions
  - IDs extracted from objects: `instance.id` for each `instanceId` in wine positions
- Reference serialization:
  - In-memory: `WineInstance.reference` is a `WineReference` object
  - JSON: `referenceId: str` extracted from `reference.id`

#### 4.3 Loading Strategy
- Load cellars first (without wine instances resolved)
- Load wine instances with cellars for location resolution
- Resolve wine instances in cellars after both are loaded
- This breaks circular dependency between cellars and wine instances

### 5. Version Tracking & Conflict Resolution (Future)

#### 5.1 Version Fields
- All entities have `version: int` field (incremented on each update)
- All entities have `created_at` and `updated_at` timestamps
- Used for conflict detection during synchronization

#### 5.2 Conflict Resolution Strategy (Planned)
- Server-side automatic resolution:
  - Last-write-wins for non-critical fields (timestamp comparison)
  - Merge strategies for additive changes
  - Version-based conflict detection
- User-facing resolution:
  - Present conflicts in clear format
  - Show local vs server versions side-by-side
  - Allow user to choose or manually merge
  - Queue unresolved conflicts

### 6. Code Organization

#### 6.1 File Structure
```
server/
├── app.py                 # Main Flask application
├── models.py              # Data model classes (Cellar, Shelf, WineReference, WineInstance)
├── cellars.py             # Cellar management endpoints and logic
├── wine_references.py     # Wine reference management endpoints and logic
├── wine_instances.py      # Wine instance management endpoints and logic
├── utils.py               # Utility functions (ID generation, timestamps, file paths)
├── data/                  # JSON data files
│   ├── cellars.json
│   ├── wine-references.json
│   └── wine-instances.json
└── tests/                 # Test suite
    ├── conftest.py
    ├── test_cellars.py
    ├── test_wine_references.py
    └── test_wine_instances.py
```

#### 6.2 Naming Conventions
- Private methods: Prefix with underscore (`_method_name`)
- Data models: PascalCase (`Cellar`, `WineReference`)
- Functions: snake_case (`load_cellars`, `find_cellar_by_id`)
- Constants: UPPER_SNAKE_CASE (`CELLARS_FILE`)

### 7. Error Handling
- All endpoints return appropriate HTTP status codes
- Error responses include `{error: "message"}` format
- Validation errors return `400 Bad Request`
- Not found errors return `404 Not Found`
- Server errors return `500 Internal Server Error`

### 8. Testing Requirements
- Unit tests for all data models
- Integration tests for all API endpoints
- Test fixtures for sample data
- Test isolation (cleanup between tests)
- Test coverage target: >80%

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