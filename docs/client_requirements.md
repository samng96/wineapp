# WineApp Client Requirements

## Overview
WineApp is a personal wine inventory management system that allows users to track, organize, and manage their wine collection.

## Data architecture
The data architecture will mirror that from server_requirements.md, with additions needed for client side management.

First, we need to build a set of types and library functions to manage the data transport coming across the wire from the REST APIs. These will be stored in the /communication folder. These will be separated into files:

- Connection management - manages establishing server communications, sending/receiving bits across the wire, and eventually auth.
- Communication management - manages transfer of high level concepts. This class has methods that should map directly to the REST API on the server, and takes first class objects defined in the Communication Types and converts them down into raw REST calls. It then uses Connection Management methods to send the raw data across the wire.


Next, we have internal data management. We need the following, all stored in the /models folder:

- Communication Types - manages the first class types that the raw REST payloads are parsed into, and referred to by the /communication files. These types will contain everything needed by the communication protocols, and will contain a second separate section that has local information (for example, local file location of downloaded label images etc).
- Models - any additional models we need to represent local client operations will live here.
- Cache management - we'll need to manage an on-device cache. It will need to load from local disk at start up, write to local disk each time a successful update to the server is made, and refresh from server at times. The cache manages communication types' liveness so that we always have fresh data from the server.
    - Refreshing will happen at specific periods:
        1. Connection time - once the user successfully logs in, we pull down a refresh
        2. Reconnection time - if the user has been in offline mode and regains connectivity, we re-login on the fly and refresh
        3. App Resume time - eventually when this becomes an iOS app, if the user tabs out and then comes back, we'll get a resume event from the iOS infrastructure that will signal that we need to attempt to reconnect.

Lastly, we have the actual client code. This can live in the root. For the web client, this is just the set of web pages that get loaded each time the user performs specific actions.

We'll want a /ui folder that has ui element binaries that we'll need to make the app prettier later on. It will also contain any logos etc that we want to keep.

We'll also want a /data folder that stores local cached copies of the downloaded labels etc for each wine from blob storage.

## Searching and Filtering
A lot of the wine management flows depend on filtering. Filters are additive, and can be checked on/off. Searching is just a specific filter, which is the "search" filter that returns items where something in the item matches the search term. 

**Currently Implemented Filters:**
  - **Type (Red, White, Rosé, etc.)** - checkbox-based dropdown with "Select all" option
  - **Varietals** - checkbox-based dropdown with "Select all" option
  - **Country** - checkbox-based dropdown with "Select all" option
  - **Consumed wines** - checkbox filter to show/hide consumed wines
  - **Unshelved wines** - checkbox filter to show/hide unshelved wines
  - **Shelved wines** - checkbox filter to show/hide shelved wines
  - **Coravined wines** - checkbox filter to show/hide wines opened with Coravin
  - **Search text** - free-form text search (case-insensitive and accent-insensitive)
  - **Sort by** - dropdown to sort by Name, Type, Vintage, Stored date, Drink by date, or Rating
  - **Sort order** - toggle button to switch between ascending and descending order

**Planned Filters (not yet implemented):**
  - Vintage range
  - Producer
  - Date range added to the cellar
  - Price range
  - In a specific cellar

## Functional requirements

We'll eventually need an auth page to start, but for the time being we can jump straight into the app, assuming a singleton user.

The main navigation will be done a bottom bar. That bottom bar will contain:
- Cellars - takes the user to cellar management
- Add wines - takes the user to the Add Wines section
- Wines - takes the user to the wines list view with filtering capabilities
- Search bar - takes the user to the search page with search term applied
- 3 dot hamburger menu - brings up the additional menu that has the following items:
    - Settings
    - User Profile

At app launch, the user will be brought to the Home page.

### 1. Home view
The home view needs several components. For now, just have a simple splash screen that says "Wine App". 

### 2. Cellar management
The cellar management screen starts by showing all the cellars the user has. From here, the user can add new cellars, edit them (they can only edit the cellar temperature and the name of the cellar), and remove them.

Each cellar that appears shows the name (displayed in ALL CAPS), the number of shelves, the total capacity (ie used/total), and what the cellar's temperature is set to. Hovering over the text for the number of bottles displays a breakdown by type of the bottles stored.

**Cellar Detail View:**
- Clicking on a cellar opens a detailed view showing all shelves
- Toggle switch in header to show/hide wine labels (shows vintage when labels hidden)
- Hovering over a wine bottle shows a wine card with detailed information:
  - Wine name, vintage, producer
  - Type, region, country with flag
  - **Stored date**
  - **Coravined date** (if applicable)
  - **Consumed date** (if applicable)
  - Rating stars (clickable to update)
- Clicking on a wine bottle opens the full wine detail modal
- Back button to return to cellar list view

UI placement:
- Top bar showing a plus sign on the right side that when clicked pops up a dialog to create a new cellar
- Main page is just a list view of all the cellars that the user has. Each cellar card has a three-dot menu button that shows options to edit or delete the cellar.
  - Edit option: pops up a dialog to edit the editable fields of a cellar
  - Delete option: prompts an "are you sure?" before deleting
- Cellar cards display a preview of the first 3 wine label images
- Cellar cards show a bottle layout preview matching the actual cellar layout (double-stacked for double shelves, single-stacked for single shelves, staggered by shelf row)

### 3. Wines View
The wines view displays all wine instances in the user's inventory with comprehensive filtering capabilities.

#### 3.1 Filter Panel
A collapsible filter panel is accessible via a filter icon button in the top right of the view header. When opened, it displays the following filters:

**Wine Type Filter:**
- Dropdown menu with checkboxes for each wine type (Red, White, etc.)
- "Select all" checkbox at the top that controls all type selections
- All types are checked by default
- When "Select all" is checked/unchecked, all type checkboxes follow
- When individual types are unchecked, "Select all" automatically unchecks if not all are selected

**Varietal Filter:**
- Dropdown menu with checkboxes for each unique varietal found in the wine collection
- "Select all" checkbox at the top that controls all varietal selections
- All varietals are checked by default
- Same behavior as Wine Type filter

**Country Filter:**
- Dropdown menu with checkboxes for each unique country found in the wine collection
- "Select all" checkbox at the top that controls all country selections
- All countries are checked by default
- Same behavior as Wine Type and Varietal filters

**Status Filters (OR logic):**
- **Consumed wines** - checkbox to show/hide consumed wines (off by default)
- **Unshelved wines** - checkbox to show/hide unshelved wines (on by default)
- **Shelved wines** - checkbox to show/hide shelved wines (on by default)
- **Coravined wines** - checkbox to show/hide wines opened with Coravin (off by default)
- These filters use OR logic - wine appears if it matches ANY checked status
- If all status checkboxes are unchecked, no wines are shown
- Consumed wines are never considered "unshelved" (they're consumed, not unshelved)

**Search Filter:**
- Text input for free-form search
- Searches across wine name, producer, region, country, type, and varietals
- Case-insensitive and accent-insensitive (e.g., "cafe" matches "Café", "CAFÉ", etc.)
- Updates results in real-time as user types (with debounce)

**Sort Controls:**
- **Sort by dropdown** - select field to sort by: Name (default), Type, Vintage, Stored date, Drink by date, or Rating
- **Sort order toggle** - button with up/down arrow to toggle between ascending (default) and descending order
- Sort is applied immediately when changed

**Reset Filters Button:**
- Button that resets all filters to default values:
  - All wine types checked
  - All varietals checked
  - All countries checked
  - Consumed wines unchecked
  - Unshelved wines checked
  - Shelved wines checked
  - Coravined wines unchecked
  - Search text cleared
  - Sort by Name, ascending order

#### 3.2 Filter Behavior
- All filters are live - changes are applied immediately without an "Apply" button
- Wine Type, Country, and Varietal dropdowns are displayed side-by-side in a row
- Only one dropdown can be open at a time (opening one closes the other)
- Clicking outside a dropdown closes it
- Search input has a 300ms debounce for performance
- Filter panel can be collapsed/expanded via filter icon in header

#### 3.3 Wine List Display
- Displays all wine instances matching the current filter criteria
- Each wine item shows:
  - Wine label image or placeholder icon
  - Vintage and name
  - Producer
  - Country flag + wine type + region/country
  - **Stored date** (always shown)
  - **Additional bottles count** (if user owns multiple of this wine)
  - **Coravined date** (if wine has been opened with Coravin)
  - **Consumed date** (if wine has been consumed)
  - **Location** (cellar, shelf, side, position - only shown if not consumed)
  - **Rating stars** (clickable to update rating, 1-5 stars)
- Click anywhere on a wine item to open detailed view modal
- Click on rating stars to update rating without opening modal
- Updates dynamically as filters change

#### 3.4 Wine Instance management
Users should be able to add new wines to their inventory. They should be able to do this by scanning the label of the wine, having the app look up the wine online (via InVintory or TotalWine or some other service) to auto-populate the wine's details.
- When we add a wine, user should be able to determine if they've purchased the wine before; if so, we should refer to the same instance and have it keep tally of each purchase/consumption date.
- This likely means we need a singleton that tracks each wine reference, and then a separate entity for instances.

#### 3.5 View Wines - Instances and References
Users should be able to view all wines in their inventory. When viewing a wine, the user should be able to:
- See how many instances of the given wine they have
- See where each instance is located (ie which cellar)
- See when each instance was stored
- Show key information at a glance (name, type, vintage, quantity)

Users should also be able to see all the consumed wine of this reference type. This should be a togglable filter.

#### 3.6 Wine Detail View
Clicking on a wine in the wine list or hovering over a wine in the cellar view opens a detailed view modal showing:

**Display Information:**
- Wine label image
- Full name with vintage
- Producer, type, region, country
- Rating stars (clickable to update)
- **Stored date** (when the bottle was added to inventory)
- **Consumed date** (if consumed)
- **Coravined date** (if opened with Coravin)
- Tasting notes textarea with save button
- Additional information section (drink time, drink window - placeholder for future Vivino integration)

**Actions for Non-Consumed Wines:**
- **"Open with a Coravin" button** - marks wine as coravined with current date/time
  - Shows confirmation dialog before marking
  - After marking, button is replaced with coravined date display
  - Wine remains in cellar location
- **"Drink wine" button** - marks wine as consumed with current date/time
  - Shows confirmation dialog before marking
  - Automatically removes wine from cellar location
  - Updates consumed date and hides action buttons
  - Cellar view refreshes automatically to show removed bottle
  - Wine list refreshes to show consumed status

**Behavior:**
- Modal can be closed via X button, clicking overlay, or clicking bottom nav
- Changes to rating and tasting notes are saved via API
- After consuming a wine, it no longer shows location information
- Consumed wines don't appear in "unshelved" filter (they're consumed, not unshelved)

#### 3.7 Coravin Feature
Coravin is a wine preservation system that allows opening a bottle without removing the cork. The app tracks wines that have been opened with Coravin:
- **Marking as Coravined:** Click "Open with a Coravin" button in wine detail view
- **Coravined Date:** Records the date/time when wine was first coravined
- **Display:** Shows "Coravined: [date]" in wine list, wine card hover, and detail view
- **Filtering:** Can filter to show only coravined wines
- **Behavior:** Coravined wines remain in their cellar location (unlike consumed wines)

#### 3.8 Wine Consumption
When a wine is marked as consumed:
1. The wine instance is marked with consumed=true and consumedDate=current timestamp
2. Wine is automatically removed from its cellar location (shelf position becomes empty)
3. Cellar detail view refreshes to show the removed bottle
4. Wine list updates to show consumed status
5. Location information is hidden in wine list display
6. Wine no longer appears in "unshelved" filter (it's consumed, not unshelved)
7. Wine appears in "consumed" filter if that's checked
8. Action buttons (Coravin, Drink) are hidden in detail view

#### 3.9 Delete Wine
Users should be able to remove wines from their inventory. This is different than consuming - this removes the entry altogether (ie a hard delete). 

Include confirmation to prevent accidental deletion

*Note: Delete functionality is planned but not yet implemented in the UI.*


### 9. Offline mode