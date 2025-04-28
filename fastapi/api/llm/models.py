from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ClothingItem:
    """Represents a clothing item with its properties."""
    
    user_id: str
    item_type: str
    material: str
    color: str
    formality: str
    pattern: str
    fit: str
    suitable_for_weather: str
    suitable_for_occasion: str = "all occasions"
    sub_type: str = ""
    image_link: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClothingItem':
        """Create a ClothingItem instance from a dictionary."""
        return cls(
            id=data.get('id', ''),
            item_type=data.get('item_type', ''),
            material=data.get('material', 'unknown'),
            color=data.get('color', 'unknown'),
            formality=data.get('formality', ''),
            pattern=data.get('pattern', ''),
            fit=data.get('fit', ''),
            suitable_for_weather=data.get('suitable_for_weather', ''),
            suitable_for_occasion=data.get('suitable_for_occasion', 'all occasions'),
            sub_type=data.get('sub_type', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the ClothingItem instance to a dictionary."""
        return {
            'id': self.id,
            'item_type': self.item_type,
            'material': self.material,
            'color': self.color,
            'formality': self.formality,
            'pattern': self.pattern,
            'fit': self.fit,
            'suitable_for_weather': self.suitable_for_weather,
            'suitable_for_occasion': self.suitable_for_occasion,
            'sub_type': self.sub_type
        }