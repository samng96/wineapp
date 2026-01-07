# WineApp Client Requirements

## Overview
WineApp is a personal wine inventory management system that allows users to track, organize, and manage their wine collection.

## Data architecture
The data architecture will mirror that from server_requirements.md, with additions needed for client side management.

## Functional requirements

### 0. Unshelved wines

### 1. Cellar management

### 2. Wine Reference management

### 3. Wine Instance management
Users should be able to add new wines to their inventory. They should be able to do this by scanning the label of the wine, having the app look up the wine online (via InVintory or TotalWine or some other service) to auto-populate the wine's details.
- When we add a wine, user should be able to determine if they've purchased the wine before; if so, we should refer to the same instance and have it keep tally of each purchase/consumption date.
- This likely means we need a singleton that tracks each wine reference, and then a separate entity for instances.


### 9. Offline mode