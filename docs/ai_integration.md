# AI Integration

## Overview

The AI-Wardrobe application leverages language models to provide intelligent outfit recommendations based on multiple factors:

- User's clothing inventory
- Style preferences
- Weather conditions
- Specific occasions/activities

## Architecture

![AI Integration Flow](https://i.imgur.com/placeholder.png)

1. User submits a natural language query about outfit suggestions
2. Backend enriches the query with user preferences and weather data
3. Enriched prompt is sent to the language model
4. LLM generates contextual outfit recommendations
5. Backend processes the response and returns formatted suggestions

## Implementation Highlights

### Prompt Engineering

The system uses carefully crafted prompts with dynamic context injection:

```
You are a personal stylist assistant for the AI-Wardrobe app. 
The current temperature is {temperature}.
The user's style preferences are:
- Preferred fit: {preferred_fit}
- Preferred colors: {preferred_colors}
- Preferred formality: {preferred_formality}
- Preferred patterns: {preferred_patterns}

The user has the following clothing items in their wardrobe:
{clothing_items}

User query: {user_message}

Based on the user's query, the weather conditions, and their wardrobe items, 
suggest an appropriate outfit. Explain your recommendation briefly.
```

### Response Processing

The AI response is processed to:
- Extract specific outfit recommendations
- Match recommendations to actual items in the user's wardrobe
- Format the response for frontend display
- Include item IDs for direct selection

### Technical Features

- **Model Abstraction** - Architecture supports multiple LLM providers
- **Context Management** - Dynamic injection of user preferences and wardrobe data
- **Response Parsing** - Structured extraction of recommendations
- **Error Handling** - Graceful fallbacks for API failures
- **Performance Optimization** - Response caching for common queries

## Example Interaction

**User Query:**
> "What should I wear for a casual coffee meeting tomorrow? It might rain."

**System Processing:**
1. Retrieves weather forecast (rainy, 65°F)
2. Fetches user's style preferences
3. Retrieves user's wardrobe items
4. Constructs prompt with context
5. Sends to LLM and processes response

**Response:**
```json
{
  "response": "For your casual coffee meeting tomorrow, I recommend a layered outfit that will keep you dry but stylish in the rain. Try your navy water-resistant jacket over the light blue button-down shirt, paired with your dark jeans. Complete the look with your brown leather boots which are perfect for wet weather.",
  "suggested_items": [
    {"id": "item123", "type": "jacket", "color": "navy"},
    {"id": "item456", "type": "shirt", "color": "light blue"},
    {"id": "item789", "type": "jeans", "color": "dark blue"},
    {"id": "item012", "type": "boots", "color": "brown"}
  ]
}
``` 