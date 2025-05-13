# Database Schema

The AI-Wardrobe application uses Supabase (PostgreSQL) for data storage, with a relational schema optimized for wardrobe management and outfit recommendations.

## Entity Relationship Diagram

```
┌─────────┐       ┌───────────────┐       ┌────────────┐
│  Users  │──1:N──┤ Clothing Items │──M:N──┤  Outfits   │
└─────────┘       └───────────────┘       └────────────┘
     │                                          │
     │                                          │
     │                  ┌──────────────────┐    │
     └────────1:1───────┤ User Preferences │    │
                        └──────────────────┘    │
                                                │
                        ┌──────────────────┐    │
                        │   Outfit Items   │◄───┘
                        └──────────────────┘
```

## Core Tables

### Users

Stores user authentication and profile information.

| Key Columns | Type | Description |
|-------------|------|-------------|
| id | UUID | Primary key |
| email | String | Unique email address |
| username | String | Unique username |
| first_name | String | User's first name |
| last_name | String | User's last name |
| gender | String | User's gender |

### Clothing Items

Stores information about individual clothing items in a user's wardrobe.

| Key Columns | Type | Description |
|-------------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to Users |
| item_type | String | Type (top, bottom, etc.) |
| material | String | Material composition |
| color | String | Primary color |
| formality | String | Formality level |
| fit | String | Fit description |
| suitable_for_weather | String | Weather suitability |
| suitable_for_occasion | String | Occasion suitability |
| image_link | String | URL to image |

### Outfits

Stores collections of clothing items that form complete outfits.

| Key Columns | Type | Description |
|-------------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to Users |
| occasion | String | Outfit occasion |
| favorite | Boolean | Favorite status |

### Outfit Items

Junction table connecting outfits to their constituent clothing items.

| Key Columns | Type | Description |
|-------------|------|-------------|
| id | UUID | Primary key |
| outfit_id | UUID | Foreign key to Outfits |
| clothing_item_id | UUID | Foreign key to Clothing Items |

### User Preferences

Stores user style preferences for AI recommendations.

| Key Columns | Type | Description |
|-------------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to Users |
| preferred_fit | String | Preferred fit style |
| preferred_colors | Array[String] | Preferred colors |
| preferred_formality | String | Preferred formality |
| preferred_patterns | Array[String] | Preferred patterns |

## Key Relationships

- **One-to-Many**: Users to Clothing Items
- **One-to-Many**: Users to Outfits
- **One-to-One**: Users to User Preferences
- **Many-to-Many**: Outfits to Clothing Items (via Outfit Items junction table)

## Design Considerations

- **Row-Level Security**: Implemented in Supabase for data isolation between users
- **Indexing**: Optimized indexes on frequently queried columns
- **Cascading Deletes**: Configured for referential integrity
- **JSON Storage**: Used for flexible attribute storage where appropriate 