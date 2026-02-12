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
- Number of positions (immutable after initialization)
- Whether the shelf is a double shelf or not (boolean, immutable after initialization)
- A 2D array of WineInstance objects (`wine_positions`). Can be empty if there's no wine there, or can contain specific instances. Serialized as IDs, but loaded as objects.

Creating a shelf has 2 inputs: number of positions, and whether the shelf is a double shelf or not.
- As a result, the array of WineInstance objects in the shelf has two dimensions: row dimension is either 1 if it is not a double shelf, or 2 if it is. Second dimension is number of positions.
- So for example, a shelf with num_positions:4 and isDouble:true will have a 2D array with 2 rows and 4 columns.
- For double shelves: row 0 = front, row 1 = back
- For single shelves: row 0 = single side

3. GlobalWineReference
Global Wine References are shared across all users and represent the basic information about a wine type.
- Required fields:
    - ID
    - Name
    - Type (Red, White, Rosé, Sparkling, etc.)
    - Vintage (year)
- Optional fields:
    - Producer/Winery
    - Varietal(s)
    - Region
    - Country
    - Label Image (URL to blob storage location)

There should be a global registry of all the global wine references that we have loaded into the system. We will try to de-dupe as much as possible based on (name, vintage, producer).

4. UserWineReference
User Wine References represent per-user data for a wine reference (personal ratings and tasting notes).
- Required fields:
    - ID
    - Global Reference ID (foreign key to GlobalWineReference)
- Optional fields:
    - Rating (1-5 stars)
    - Tasting Notes

Each user can have their own UserWineReference for a given GlobalWineReference, allowing personal ratings and notes while sharing the base wine information.

5. WineInstance
Wine Instances are single physical bottles of wine.
- Required fields:
    - ID. This is used to refer to an instance, and will be stored as a part of shelves' serialization.
    - Reference to UserWineReference. This should be stored as an ID for serialization purposes, but should be loaded as an object. This is immutable.
- Optional fields:
    - Price
    - Purchase date (ISO 8601 date)
    - Drink by date (ISO 8601 date, client code should obtain this from Vivino)
    - Consumed - a boolean value for whether or not this wine has been consumed
    - Consumed date - ISO 8601 timestamp when the WineInstance is consumed
    - Coravined - a boolean value for whether or not this wine has been opened with Coravin
    - Coravined date - ISO 8601 timestamp when the wine was coravined
    - Stored date - ISO 8601 timestamp when the wine was added to inventory

Note: Location is NOT stored on the WineInstance itself. Instead, location is tracked by storing the WineInstance object in the appropriate position within a Cellar's Shelf structure. An instance is considered "unshelved" if it is not found in any cellar's shelves.

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
    - For double shelves: row 0 = front, row 1 = back
    - For single shelves: row 0 = single side
- **Methods**:
  - `get_wine_at(side: str, position: int) -> Optional[WineInstance]`: Get wine instance object at position (returns object, not ID)
    - `side`: "front" or "back" for double shelves, "single" for single shelves
  - `set_wine_at(side: str, position: int, instance: Optional[WineInstance])`: Set wine instance object at position
  - Private methods prefixed with `_`
  - **Note**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when needed (e.g., `instance.id`)

#### 2.3 GlobalWineReference Model
- **Class**: `GlobalWineReference` (dataclass)
- **Fields**:
  - `id: str` (UUID)
  - `name: str`
  - `type: str` (Red, White, Rosé, Sparkling, etc.)
  - `vintage: int`
  - `producer: Optional[str]`
  - `varietals: Optional[List[str]]`
  - `region: Optional[str]`
  - `country: Optional[str]`
  - `label_image_url: Optional[str]` (URL to blob storage)
  - `version: int` (for conflict resolution)
  - `created_at: Optional[str]` (ISO 8601 timestamp)
  - `updated_at: Optional[str]` (ISO 8601 timestamp)
- **Methods**:
  - `get_unique_key() -> tuple`: Get unique key for deduplication (name, vintage, producer)
  - **Note**: GlobalWineReference represents shared wine information across all users

#### 2.4 UserWineReference Model
- **Class**: `UserWineReference` (dataclass)
- **Fields**:
  - `id: str` (UUID)
  - `global_reference_id: str` (foreign key to GlobalWineReference)
  - `rating: Optional[int]` (1-5)
  - `tasting_notes: Optional[str]`
  - `version: int` (for conflict resolution)
  - `created_at: Optional[str]` (ISO 8601 timestamp)
  - `updated_at: Optional[str]` (ISO 8601 timestamp)
- **Note**: UserWineReference represents per-user personal data (rating, tasting notes) for a wine reference

#### 2.5 WineInstance Model
- **Class**: `WineInstance` (dataclass)
- **Fields**:
  - `id: str` (UUID)
  - `reference: UserWineReference` (object reference, not ID - loaded from user wine references)
  - `price: Optional[float]`
  - `purchase_date: Optional[str]` (ISO 8601 date)
  - `drink_by_date: Optional[str]` (ISO 8601 date)
  - `consumed: bool`
  - `consumed_date: Optional[str]` (ISO 8601 timestamp)
  - `coravined: bool`
  - `coravined_date: Optional[str]` (ISO 8601 timestamp)
  - `stored_date: Optional[str]` (ISO 8601 timestamp)
  - `version: int` (for conflict resolution)
  - `created_at: Optional[str]` (ISO 8601 timestamp)
  - `updated_at: Optional[str]` (ISO 8601 timestamp)
- **Methods**:
  - `set_consumed()`: Mark wine as consumed and set consumed_date to current timestamp
  - `set_coravined()`: Mark wine as coravined and set coravined_date to current timestamp
  - **Note**: Location is NOT stored on WineInstance. Location is tracked by storing the WineInstance object in the appropriate position within a Cellar's Shelf structure. An instance is "unshelved" if it is not found in any cellar's shelves.
  - **Note**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when needed (e.g., `reference.id`)

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

#### 3.2 Global Wine Reference Management
- `GET /wine-references`
  - Returns: List of all global wine references as JSON array
  - Response: `200 OK` with JSON array of global wine reference objects
  - Each reference includes: `id, name, type, vintage, producer?, varietals?, region?, country?, labelImageUrl?, version, createdAt, updatedAt`
  
- `GET /wine-references/<reference_id>`
  - Returns: Single global wine reference by ID
  - Response: `200 OK` with global wine reference object, or `404 Not Found`
  
- `GET /wine-references/<reference_id>/instances`
  - Returns: Single global wine reference by ID with all associated instances
  - Response: `200 OK` with global wine reference object plus `instances` array, or `404 Not Found`
  - `instances`: Array of all wine instances (both active and consumed) for this reference
  
- `POST /wine-references`
  - Request Body: Global wine reference fields
    - Required: `name: str, type: str, vintage: int` (e.g., "Red", "White", "Rosé", "Sparkling", etc.)
    - Optional: `producer?: str, varietals?: string[], region?: str, country?: str, labelImageUrl?: str`
  - Returns: Created global wine reference with generated ID, version=1, timestamps
  - Response: `201 Created` with global wine reference object
  - Deduplication: Returns `409 Conflict` if reference with same `(name, vintage, producer)` already exists, includes existing reference in response
  
- `PUT /wine-references/<reference_id>`
  - Request Body: Updated global wine reference fields (all optional)
    - Any field can be updated: `name?, type?, vintage?, producer?, varietals?, region?, country?, labelImageUrl?`
  - Returns: Updated global wine reference with incremented version, updated timestamp
  - Response: `200 OK` with updated global wine reference object, or `404 Not Found`
  
- `DELETE /wine-references/<reference_id>`
  - Hard delete (removes from system)
  - Response: `200 OK` with `{message: "Wine reference deleted"}`, or `404 Not Found`
  - Note: Does not delete associated user wine references or wine instances

#### 3.3 User Wine Reference Management
- `GET /user-wine-references`
  - Returns: List of all user wine references as JSON array
  - Response: `200 OK` with JSON array of user wine reference objects
  - Each reference includes: `id, globalReferenceId, rating?, tastingNotes?, version, createdAt, updatedAt`
  
- `GET /user-wine-references/<user_reference_id>`
  - Returns: Single user wine reference by ID
  - Response: `200 OK` with user wine reference object, or `404 Not Found`
  
- `POST /user-wine-references`
  - Request Body: User wine reference fields
    - Required: `globalReferenceId: str`
    - Optional: `rating?: int (1-5), tastingNotes?: str`
  - Returns: Created user wine reference with generated ID, version=1, timestamps
  - Response: `201 Created` with user wine reference object
  
- `PUT /user-wine-references/<user_reference_id>`
  - Request Body: Updated user wine reference fields (all optional)
    - Any field can be updated: `rating?, tastingNotes?`
    - Note: `globalReferenceId` cannot be changed
  - Returns: Updated user wine reference with incremented version, updated timestamp
  - Response: `200 OK` with updated user wine reference object, or `404 Not Found`
  
- `DELETE /user-wine-references/<user_reference_id>`
  - Hard delete (removes from system)
  - Response: `200 OK` with `{message: "User wine reference deleted"}`, or `404 Not Found`
  - Note: Does not delete associated wine instances

#### 3.4 Wine Instance Management
- `GET /wine-instances`
  - Returns: List of all wine instances as JSON array
  - Response: `200 OK` with JSON array of wine instance objects
  - Each instance includes: `id, referenceId, price?, purchaseDate?, drinkByDate?, consumed, consumedDate?, coravined, coravinedDate?, storedDate?, version, createdAt, updatedAt`
  - Note: Location is not included in the instance object. Location is determined by searching cellars for the instance.
  
- `GET /wine-instances/<instance_id>`
  - Returns: Single wine instance by ID
  - Response: `200 OK` with wine instance object, or `404 Not Found`
  
- `POST /wine-instances`
  - Request Body: `{referenceId: str, location?: object, price?: float, purchaseDate?: str, drinkByDate?: str}`
  - Location format (optional):
    - For cellar: `{type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}`
    - For unshelved: `{type: "unshelved"}` or `null` or omitted
  - Returns: Created wine instance with generated ID, `consumed=false`, `coravined=false`, `storedDate` set to current timestamp, version=1, timestamps
  - Response: `201 Created` with wine instance object
  - Validation: Returns `404 Not Found` if `referenceId` doesn't exist
  - Note: If location is provided, assigns instance to cellar position using `cellar.assign_wine_to_position()`
  
- `PUT /wine-instances/<instance_id>`
  - Request Body: Updated wine instance fields (all optional)
    - Any field can be updated: `price?, purchaseDate?, drinkByDate?`
    - Note: `referenceId` cannot be changed. Location should be updated via `/location` endpoint.
  - Returns: Updated wine instance with incremented version, updated timestamp
  - Response: `200 OK` with updated wine instance object, or `404 Not Found`
  
- `DELETE /wine-instances/<instance_id>`
  - Hard delete (removes from system)
  - Removes from cellar position if applicable (calls `cellar.remove_wine_from_cellar()`)
  - Response: `200 OK` with `{message: "Wine instance deleted"}`, or `404 Not Found`
  
- `POST /wine-instances/<instance_id>/consume`
  - Marks wine instance as consumed
  - Sets `consumed=true` and `consumedDate` to current timestamp
  - Removes from cellar position if applicable (calls `cellar.remove_wine_from_cellar()`)
  - Updates version and timestamp
  - Response: `200 OK` with updated wine instance object, or `404 Not Found`
  
- `POST /wine-instances/<instance_id>/coravin`
  - Marks wine instance as coravined
  - Sets `coravined=true` and `coravinedDate` to current timestamp
  - Updates version and timestamp
  - Note: Wine remains in cellar location (unlike consumed wines)
  - Response: `200 OK` with updated wine instance object, or `404 Not Found`
  
- `PUT /wine-instances/<instance_id>/location`
  - Request Body: `{location: object | null}`
  - Location format:
    - For cellar: `{type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}`
    - For unshelved: `null` or `{type: "unshelved"}`
  - Moves wine instance to new location
  - Validates position using `cellar.is_position_valid()`
  - Checks availability using `cellar.is_position_available()` (allows same instance to stay in place)
  - Removes from old position if moving within same cellar or from different cellar
  - Assigns to new position using `cellar.assign_wine_to_position()` (passes WineInstance object)
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
- `server/data/wine-references.json`: Array of global wine reference objects
- `server/data/user-wine-references.json`: Array of user wine reference objects
- `server/data/wine-instances.json`: Array of wine instance objects

#### 4.2 Serialization Format
- All dates/timestamps: ISO 8601 format strings
- **General Rule**: All `get_*` methods return object instances, not IDs. IDs are extracted from objects when serializing to JSON (e.g., `cellar.id`, `reference.id`, `instance.id`)
- Location tracking:
  - Location is NOT stored on WineInstance objects
  - Location is tracked by storing WineInstance objects in Cellar Shelf structures (`wine_positions` 2D array)
  - To find an instance's location, search through all cellars and shelves
  - JSON (request format for location assignment): `{type: "cellar", cellarId: str, shelfIndex: int, side: "front"|"back"|"single", position: int}` or `null`/`{type: "unshelved"}`
  - Conversion: Request `side` string converted to row index (front=0, back=1 for double shelves, single=0 for single shelves)
- Shelf serialization:
  - In-memory: `Shelf` object with `wine_positions` as 2D array of `WineInstance` objects
  - JSON: `[positions, isDouble]` for shelf config, `{side: [instanceId, ...]}` for wine positions
  - IDs extracted from objects: `instance.id` for each `instanceId` in wine positions
- Reference serialization:
  - In-memory: `WineInstance.reference` is a `UserWineReference` object
  - JSON: `referenceId: str` extracted from `reference.id` (UserWineReference ID)
  - UserWineReference contains `globalReferenceId` which links to GlobalWineReference

#### 4.3 Loading Strategy
- Load global wine references first
- Load user wine references (with global reference IDs)
- Load cellars (without wine instances resolved)
- Load wine instances (with user wine references resolved)
- Resolve wine instances in cellars after all are loaded
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
├── models.py              # Data model classes (Cellar, Shelf, GlobalWineReference, UserWineReference, WineInstance)
├── cellars.py             # Cellar management endpoints and logic
├── wine_references.py     # Global wine reference management endpoints and logic
├── user_wine_references.py # User wine reference management endpoints and logic
├── wine_instances.py      # Wine instance management endpoints and logic
├── utils.py               # Utility functions (ID generation, timestamps, file paths)
├── data/                  # JSON data files
│   ├── cellars.json
│   ├── wine-references.json
│   ├── user-wine-references.json
│   └── wine-instances.json
└── tests/                 # Test suite
    ├── conftest.py
    ├── test_cellars.py
    ├── test_wine_references.py
    ├── test_user_wine_references.py
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