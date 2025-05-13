# API Endpoints

This document provides a reference of key API endpoints in the AI-Wardrobe backend.

## Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sign-up/` | POST | Register a new user account |
| `/sign-in/` | POST | Authenticate and get session token |
| `/session/` | GET | Validate current session |
| `/sign-out/` | POST | End current session |

**Example Authentication Flow:**
```javascript
// Registration
const registerResponse = await fetch('/sign-up/', {
  method: 'POST',
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Doe',
    username: 'johndoe',
    email: 'john@example.com',
    password: 'SecurePass123',
    gender: 'male'
  })
});

// Login
const loginResponse = await fetch('/sign-in/', {
  method: 'POST',
  body: JSON.stringify({
    identifier: 'johndoe',
    password: 'SecurePass123'
  })
});

const { access_token } = await loginResponse.json();
```

## Wardrobe Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/add_clothing_item/` | POST | Add item to wardrobe |
| `/clothing_items/` | GET | Get all user's clothing items |
| `/clothing_item/{item_id}` | GET | Get specific item details |
| `/update_clothing_item/{item_id}` | PUT | Update item details |
| `/delete_clothing_item/{item_id}` | DELETE | Remove item from wardrobe |

**Example Response: Get Clothing Items**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "a385a273-d693-4851-a1a7-3dfd1a9a0d46",
    "item_type": "top",
    "sub_type": "t-shirt",
    "material": "cotton",
    "color": "navy",
    "formality": "casual",
    "pattern": "solid",
    "fit": "regular",
    "suitable_for_weather": "warm",
    "suitable_for_occasion": "casual",
    "image_link": "https://example.com/images/navy-tshirt.jpg"
  },
  {
    "id": "c7d3e8f6-d2b1-4a63-9c5e-7f8a9b0c1d2e",
    "user_id": "a385a273-d693-4851-a1a7-3dfd1a9a0d46",
    "item_type": "bottom",
    "sub_type": "jeans",
    "material": "denim",
    "color": "blue",
    "formality": "casual",
    "pattern": "solid",
    "fit": "slim",
    "suitable_for_weather": "moderate",
    "suitable_for_occasion": "casual",
    "image_link": "https://example.com/images/blue-jeans.jpg"
  }
]
```

## Outfit Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create_outfit/` | POST | Create new outfit |
| `/outfits/` | GET | Get all user's outfits |
| `/outfit/{outfit_id}` | GET | Get specific outfit |
| `/update_outfit/{outfit_id}` | PUT | Update outfit details |
| `/delete_outfit/{outfit_id}` | DELETE | Remove outfit |

## User Profile

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/profile/` | GET | Get user profile data |
| `/update_profile/` | PUT | Update profile information |

## AI Recommendations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/` | POST | Get AI outfit suggestions |

**Example Request:**
```json
{
  "user_message": "What should I wear to a job interview tomorrow?",
  "temp": "72°F"
}
```

**Example Response:**
```json
{
  "response": "For a job interview in 72°F weather, I recommend a professional outfit that's comfortable but not too warm. From your wardrobe, try your navy blazer with the light blue button-down shirt and gray dress pants. Complete the look with your brown leather shoes and matching belt for a polished appearance.",
  "suggested_items": [
    {
      "id": "7f9c2e5a-1d3b-4f8e-9a7c-6d5e4f3c2b1a",
      "item_type": "top",
      "sub_type": "blazer",
      "color": "navy"
    },
    {
      "id": "2a1b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
      "item_type": "top",
      "sub_type": "button-down",
      "color": "light blue"
    },
    {
      "id": "9p8o7n6m-5l4k3j2i-1h0g9f8e-7d6c5b4a",
      "item_type": "bottom",
      "sub_type": "dress pants",
      "color": "gray"
    },
    {
      "id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
      "item_type": "footwear",
      "sub_type": "dress shoes",
      "color": "brown"
    }
  ]
}
``` 