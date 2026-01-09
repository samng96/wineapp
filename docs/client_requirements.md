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

We have the following filters:
  - Type (Red, White, Rosé, etc.)
  - Vintage range
  - Rating
  - Country/Region
  - Whether consumed
  - Varietals
  - Producer
  - Date range added to the cellar
  - Price range
  - Unshelved or not
  - In a specific cellar

## Functional requirements

We'll eventually need an auth page to start, but for the time being we can jump straight into the app, assuming a singleton user.

The main navigation will be done a bottom bar. That bottom bar will contain:
- Cellar - takes the user to cellar management
- Photo - takes the user to the Add Wines section
- Wines - takes the user to the search page, no filter
- Unshelved - takes the user to the search page, with filter = "Unshelved Wines" applied.
- Search bar - takes the user to the search page with search term applied
- 3 dot hamburger menu - brings up the additional menu that has the following items:
    - Settings
    - User Profile

At app launch, the user will be brought to the Home page.

### 1. Home view
The home view needs several components. For now, just have a simple splash screen that says "Wine App". 

### 2. Cellar management
The cellar management screen starts by showing all the cellars the user has. From here, the user can add new cellars, edit them (they can only edit the cellar temperature and the name of the cellar), and remove them.

Each cellar that apperas shows the name that is editable, the number of shelves, the total capacity (ie used/total), and what the cellar's temperature is set to. Hovering over the text for the number of bottles displays a breakdown by type of the bottles stored.

UI placement:
- Top bar showing a plus sign on the right side that when clicked pops up a dialog to create a new cellar
- Main page is just a list view of all the cellars that the user has. Next to the cellar, there is an edit icon and a delete icon. Clicking the edit icon pops up a dialog to edit the editable fileds of a cellar, and clicking the delete icon prompts an "are you sure?" before deleting.

### 3. Search page

### 3. Wine Instance management
Users should be able to add new wines to their inventory. They should be able to do this by scanning the label of the wine, having the app look up the wine online (via InVintory or TotalWine or some other service) to auto-populate the wine's details.
- When we add a wine, user should be able to determine if they've purchased the wine before; if so, we should refer to the same instance and have it keep tally of each purchase/consumption date.
- This likely means we need a singleton that tracks each wine reference, and then a separate entity for instances.

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


### 9. Offline mode