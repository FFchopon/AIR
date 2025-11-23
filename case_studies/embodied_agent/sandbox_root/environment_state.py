"""
Environment state management for embodied agent sandbox.

This module defines the core data structures for maintaining object states
and spatial relationships in the simulated environment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import json
import copy


class ObjectType(Enum):
    """Common object types in the environment."""
    # Containers/Receptacles
    CABINET = "Cabinet"
    DRAWER = "Drawer"
    FRIDGE = "Fridge"
    MICROWAVE = "Microwave"
    SINK = "Sink"
    TOILET = "Toilet"
    BATHTUB = "Bathtub"
    MUG = "Mug"
    CUP = "Cup"
    BOWL = "Bowl"
    POT = "Pot"
    PAN = "Pan"
    
    # Appliances
    STOVE_BURNER = "StoveBurner"
    STOVE_KNOB = "StoveKnob"
    TOASTER = "Toaster"
    COFFEE_MACHINE = "CoffeeMachine"
    LAPTOP = "Laptop"
    TELEVISION = "Television"
    DESK_LAMP = "DeskLamp"
    
    # Items
    CANDLE = "Candle"
    BOOK = "Book"
    CREDIT_CARD = "CreditCard"
    FORK = "Fork"
    SPOON = "Spoon"
    KNIFE = "Knife"
    CELL_PHONE = "CellPhone"
    ALARM_CLOCK = "AlarmClock"
    CLOTH = "Cloth"
    SALT_SHAKER = "SaltShaker"
    SHOWER_CURTAIN = "ShowerCurtain"
    WATERING_CAN = "WateringCan"
    WINE_BOTTLE = "WineBottle"
    SPRAY_BOTTLE = "SprayBottle"
    
    # Liquids (virtual items)
    COFFEE = "Coffee"
    WATER = "Water"
    WINE = "Wine"


class LocationType(Enum):
    """Types of spatial locations."""
    ON_FLOOR = "on the floor"
    ON_TABLE = "on the table"
    ON_COUNTER = "on the counter"
    IN_CONTAINER = "in container"  # Specific container in parentReceptacles
    ON_APPLIANCE = "on appliance"  # e.g., on StoveBurner
    HELD_BY_AGENT = "held by agent"
    UNKNOWN = "unknown"


@dataclass
class ObjectState:
    """
    Represents the state of a single object in the environment.
    
    Attributes:
        object_type: Type of the object (e.g., "Candle", "Microwave")
        is_dirty: Whether the object is dirty
        is_broken: Whether the object is broken
        is_toggled: Whether the object is on/off (for toggleable items)
        is_open: Whether the object is open (for containers)
        is_filled_with_liquid: Whether the object contains liquid (inside)
        liquid_content: Type of liquid if filled (e.g., "coffee", "water")
        has_liquid_on_surface: Whether liquid has been poured onto this object's surface
        surface_liquid_type: Type of liquid on surface (e.g., "coffee", "water")
        parent_receptacles: List of containers this object is in/on
        location_type: General location category
        is_held_by_agent: Whether the agent is currently holding this object
        is_sliced: Whether the object has been sliced
        material: Material type (e.g., "metal", "plastic", "flammable")
    """
    object_type: str
    is_dirty: bool = False
    is_broken: bool = False
    is_toggled: bool = False  # on/off state
    is_open: bool = False
    is_filled_with_liquid: bool = False  # Liquid INSIDE container
    liquid_content: Optional[str] = None  # Type of liquid inside
    has_liquid_on_surface: bool = False  # Liquid poured ONTO surface
    surface_liquid_type: Optional[str] = None  # Type of liquid on surface
    parent_receptacles: List[str] = field(default_factory=list)
    location_type: str = LocationType.ON_FLOOR.value
    is_held_by_agent: bool = False
    is_sliced: bool = False
    material: Optional[str] = None  # "metal", "plastic", "flammable", "electronic"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for comparison with final_state."""
        result = {}
        if self.is_dirty:
            result["isDirty"] = True
        if self.is_broken:
            result["isBroken"] = True
        if self.is_toggled:
            result["isToggled"] = True
        if self.is_open:
            result["isOpen"] = True
        if self.is_filled_with_liquid:
            result["isFilledWithLiquid"] = True
        if self.has_liquid_on_surface:
            result["hasLiquidOnSurface"] = True
        if self.parent_receptacles:
            result["parentReceptacles"] = self.parent_receptacles.copy()
        if self.is_sliced:
            result["isSliced"] = True
        return result
    
    def get_location_description(self) -> str:
        """Get human-readable location description."""
        if self.is_held_by_agent:
            return "held by agent"
        elif self.parent_receptacles:
            return f"in/on {', '.join(self.parent_receptacles)}"
        else:
            return self.location_type
    
    def get_liquid_description(self) -> str:
        """Get description of liquid state."""
        parts = []
        if self.is_filled_with_liquid:
            liquid = self.liquid_content or "unknown liquid"
            parts.append(f"filled with {liquid}")
        if self.has_liquid_on_surface:
            liquid = self.surface_liquid_type or "unknown liquid"
            parts.append(f"{liquid} on surface")
        return ", ".join(parts) if parts else "no liquid"
    
    def clone(self) -> 'ObjectState':
        """Create a deep copy of this object state."""
        return ObjectState(
            object_type=self.object_type,
            is_dirty=self.is_dirty,
            is_broken=self.is_broken,
            is_toggled=self.is_toggled,
            is_open=self.is_open,
            is_filled_with_liquid=self.is_filled_with_liquid,
            liquid_content=self.liquid_content,
            has_liquid_on_surface=self.has_liquid_on_surface,
            surface_liquid_type=self.surface_liquid_type,
            parent_receptacles=self.parent_receptacles.copy(),
            location_type=self.location_type,
            is_held_by_agent=self.is_held_by_agent,
            is_sliced=self.is_sliced,
            material=self.material
        )


@dataclass
class EnvironmentState:
    """
    Represents the complete state of the simulated environment.
    
    This maintains all objects and their properties, spatial relationships,
    and provides methods for state manipulation and verification.
    """
    objects: Dict[str, ObjectState] = field(default_factory=dict)
    scene_name: str = "Unknown"
    agent_holding: Optional[str] = None  # Name of object currently held
    
    def add_object(self, name: str, obj_state: ObjectState):
        """Add an object to the environment."""
        self.objects[name] = obj_state
    
    def get_object(self, name: str) -> Optional[ObjectState]:
        """Get object state by name."""
        return self.objects.get(name)
    
    def has_object(self, name: str) -> bool:
        """Check if object exists in environment."""
        return name in self.objects
    
    def update_object(self, name: str, **kwargs):
        """
        Update object properties.
        
        Args:
            name: Object name
            **kwargs: Properties to update
        """
        if name in self.objects:
            for k, v in kwargs.items():
                if hasattr(self.objects[name], k):
                    setattr(self.objects[name], k, v)
    
    def remove_object(self, name: str):
        """Remove an object from the environment (e.g., after throw/break)."""
        if name in self.objects:
            del self.objects[name]
            if self.agent_holding == name:
                self.agent_holding = None
    
    def pick_object(self, name: str) -> bool:
        """
        Agent picks up an object.
        
        Returns:
            True if successful, False otherwise
        """
        if self.agent_holding:
            return False  # Already holding something
        
        obj = self.get_object(name)
        if not obj:
            return False
        
        # Update state
        obj.is_held_by_agent = True
        obj.parent_receptacles.clear()
        obj.location_type = LocationType.HELD_BY_AGENT.value
        self.agent_holding = name
        return True
    
    def drop_object(self, name: str, location: str = "floor"):
        """
        Agent drops the held object.
        
        Args:
            name: Object name
            location: Where to drop (default: floor)
        """
        obj = self.get_object(name)
        if obj and obj.is_held_by_agent:
            obj.is_held_by_agent = False
            obj.location_type = LocationType.ON_FLOOR.value
            self.agent_holding = None
    
    def put_object(self, object_name: str, receptacle_name: str) -> bool:
        """
        Place an object into/onto a receptacle.
        
        Args:
            object_name: Name of object to place
            receptacle_name: Name of target receptacle
            
        Returns:
            True if successful, False otherwise
        """
        obj = self.get_object(object_name)
        receptacle = self.get_object(receptacle_name)
        
        if not obj or not receptacle:
            return False
        
        # Update object state
        obj.parent_receptacles = [receptacle_name]
        obj.is_held_by_agent = False
        obj.location_type = LocationType.IN_CONTAINER.value
        
        if self.agent_holding == object_name:
            self.agent_holding = None
        
        return True
    
    def pour_liquid(self, source_object_name: str, target_object_name: str) -> bool:
        """
        Pour liquid from source object onto/into target object.
        
        This handles two scenarios:
        1. Pour INTO a container (target becomes filled)
        2. Pour ONTO a surface (target gets liquid on surface)
        
        Args:
            source_object_name: Object containing liquid to pour
            target_object_name: Target object to pour onto/into
            
        Returns:
            True if successful, False otherwise
        """
        source = self.get_object(source_object_name)
        target = self.get_object(target_object_name)
        
        if not source or not target:
            return False
        
        # Source must have liquid
        if not source.is_filled_with_liquid or not source.liquid_content:
            return False
        
        liquid_type = source.liquid_content
        
        # Determine if pouring into container or onto surface
        # Containers: Mug, Cup, Bowl, Pot, Pan, Sink, Toilet, Bathtub
        container_types = ["Mug", "Cup", "Bowl", "Pot", "Pan", "Sink", "Toilet", "Bathtub", 
                          "Microwave", "Fridge", "Cabinet", "Drawer"]
        
        if target.object_type in container_types and target.is_open:
            # Pour INTO container
            target.is_filled_with_liquid = True
            target.liquid_content = liquid_type
        else:
            # Pour ONTO surface (e.g., Laptop, Television, StoveBurner)
            target.has_liquid_on_surface = True
            target.surface_liquid_type = liquid_type
        
        # Empty the source container
        source.is_filled_with_liquid = False
        source.liquid_content = None
        
        return True
    
    def fill_liquid(self, container_name: str, liquid_type: str) -> bool:
        """
        Fill a container with liquid from a virtual source.
        
        Args:
            container_name: Name of container to fill
            liquid_type: Type of liquid (e.g., "coffee", "water", "wine")
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_object(container_name)
        if not container:
            return False
        
        # Check if liquid source exists (virtual objects)
        liquid_source = self.get_object(liquid_type.capitalize())
        if not liquid_source:
            return False
        
        # Fill the container
        container.is_filled_with_liquid = True
        container.liquid_content = liquid_type
        
        return True
    
    def verify_final_state(self, expected_final_state: Optional[List[Dict[str, Any]]]) -> bool:
        """
        Verify if current state matches expected final state.
        
        Args:
            expected_final_state: List of expected object states from dataset
            
        Returns:
            True if states match, False otherwise
        """
        if expected_final_state is None:
            # null means no specific final state required
            return True
        
        for expected_obj in expected_final_state:
            obj_type = expected_obj.get("objectType")
            if not obj_type:
                continue
            
            # Find object by type
            actual_obj = self.get_object(obj_type)
            if not actual_obj:
                return False
            
            # Check each expected property
            for key, expected_value in expected_obj.items():
                if key == "objectType":
                    continue
                
                # Map dataset keys to ObjectState attributes
                attr_map = {
                    "isDirty": "is_dirty",
                    "isBroken": "is_broken",
                    "isToggled": "is_toggled",
                    "isOpen": "is_open",
                    "isFilledWithLiquid": "is_filled_with_liquid",
                    "parentReceptacles": "parent_receptacles",
                    "isSliced": "is_sliced"
                }
                
                attr_name = attr_map.get(key, key)
                actual_value = getattr(actual_obj, attr_name, None)
                
                if actual_value != expected_value:
                    return False
        
        return True
    
    def get_state_summary(self) -> str:
        """Get a human-readable summary of the environment state."""
        lines = [f"Scene: {self.scene_name}"]
        lines.append(f"Agent holding: {self.agent_holding or 'nothing'}")
        lines.append("\nObjects:")
        
        for name, obj in sorted(self.objects.items()):
            props = []
            if obj.is_toggled:
                props.append("ON")
            if obj.is_open:
                props.append("OPEN")
            if obj.is_dirty:
                props.append("DIRTY")
            if obj.is_broken:
                props.append("BROKEN")
            if obj.is_filled_with_liquid:
                liquid = f" with {obj.liquid_content}" if obj.liquid_content else ""
                props.append(f"FILLED{liquid}")
            if obj.has_liquid_on_surface:
                liquid = obj.surface_liquid_type or "unknown"
                props.append(f"{liquid.upper()} ON SURFACE")
            
            prop_str = f" [{', '.join(props)}]" if props else ""
            location = obj.get_location_description()
            lines.append(f"  - {name} ({obj.object_type}){prop_str}: {location}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire environment to dictionary."""
        return {
            "scene_name": self.scene_name,
            "agent_holding": self.agent_holding,
            "objects": {
                name: obj.to_dict()
                for name, obj in self.objects.items()
            }
        }
    
    def clone(self) -> 'EnvironmentState':
        """Create a deep copy of the environment state."""
        new_env = EnvironmentState(
            scene_name=self.scene_name,
            agent_holding=self.agent_holding
        )
        for name, obj in self.objects.items():
            new_env.objects[name] = obj.clone()
        return new_env
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentState':
        """Create environment state from dictionary."""
        env = cls(scene_name=data.get("scene_name", "Unknown"))
        env.agent_holding = data.get("agent_holding")
        
        for name, obj_data in data.get("objects", {}).items():
            obj = ObjectState(object_type=obj_data["object_type"])
            for key, value in obj_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            env.objects[name] = obj
        
        return env
