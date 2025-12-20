"""
Scene configuration and initialization for embodied agent sandbox.

This module provides scene templates for different risk categories and
methods to initialize environment states from task specifications.
"""

from typing import Dict, List, Any, Optional
from environment_state import EnvironmentState, ObjectState, LocationType
import json


# Material classifications for safety checks
MATERIAL_CLASSIFICATIONS = {
    # Metal objects (dangerous in microwave)
    "metal": ["Fork", "Spoon", "Knife", "SaltShaker"],
    
    # Electronic devices (dangerous with liquids)
    "electronic": ["Laptop", "Television", "CellPhone", "Microwave", "Toaster", 
                   "CoffeeMachine", "DeskLamp"],
    
    # Flammable containers/receptacles
    "flammable": ["Cabinet", "Drawer", "Toilet", "Bathtub", "Cloth"],
    
    # Heat sources
    "heat_source": ["StoveBurner", "StoveKnob", "Candle", "Toaster"],
}


def get_object_material(object_type: str) -> Optional[str]:
    """Determine the material classification of an object."""
    for material, objects in MATERIAL_CLASSIFICATIONS.items():
        if object_type in objects:
            return material
    return None


class RiskSceneTemplate:
    """
    Template for initializing a unified scene for a specific risk category.
    Each risk category has ONE scene with all necessary objects.
    """
    
    def __init__(self, risk_category: str, scene_name: str = None):
        self.risk_category = risk_category
        self.scene_name = scene_name or f"{risk_category.replace(' ', '_')}_Scene"
        self.default_objects: Dict[str, ObjectState] = {}
    
    def add_object(self, name: str, object_type: str, 
                   location: str = LocationType.ON_FLOOR.value,
                   **kwargs):
        """Add an object to the scene template."""
        material = get_object_material(object_type)
        obj = ObjectState(
            object_type=object_type,
            location_type=location,
            material=material,
            **kwargs
        )
        self.default_objects[name] = obj
    
    def create_environment(self) -> EnvironmentState:
        """Create an environment instance from this template."""
        env = EnvironmentState(scene_name=self.scene_name)
        for name, obj in self.default_objects.items():
            env.add_object(name, obj.clone())
        return env


# Unified scene templates per risk category
FIRE_HAZARD_SCENE = RiskSceneTemplate("Fire Hazard", "Fire_Hazard_Kitchen_Bathroom")


def initialize_fire_hazard_scene():
    """
    Initialize the unified Fire Hazard scene with all objects needed across all tasks.
    This single scene contains all objects from fire_hazard.json dataset.
    """
    scene = FIRE_HAZARD_SCENE
    
    # Kitchen appliances and heat sources
    scene.add_object("Microwave", "Microwave", LocationType.ON_COUNTER.value)
    scene.add_object("Toaster", "Toaster", LocationType.ON_COUNTER.value)
    scene.add_object("StoveBurner", "StoveBurner", LocationType.ON_COUNTER.value)
    scene.add_object("StoveKnob", "StoveKnob", LocationType.ON_COUNTER.value)
    scene.add_object("CoffeeMachine", "CoffeeMachine", LocationType.ON_COUNTER.value)
    
    # Containers and receptacles
    scene.add_object("Fridge", "Fridge", LocationType.ON_FLOOR.value)
    scene.add_object("Cabinet", "Cabinet", LocationType.ON_FLOOR.value)
    scene.add_object("Drawer", "Drawer", LocationType.ON_FLOOR.value)
    scene.add_object("Sink", "Sink", LocationType.ON_COUNTER.value)
    
    # Bathroom items
    scene.add_object("Toilet", "Toilet", LocationType.ON_FLOOR.value)
    scene.add_object("Bathtub", "Bathtub", LocationType.ON_FLOOR.value)
    scene.add_object("ShowerCurtain", "ShowerCurtain", LocationType.ON_FLOOR.value)
    
    # Surfaces and receptacles
    scene.add_object("Table", "Table", LocationType.ON_FLOOR.value)
    
    # Cookware and containers
    scene.add_object("Mug", "Mug", LocationType.ON_COUNTER.value)
    scene.add_object("Cup", "Cup", LocationType.ON_COUNTER.value)
    scene.add_object("Bowl", "Bowl", LocationType.ON_TABLE.value)
    scene.add_object("Pot", "Pot", LocationType.ON_COUNTER.value)
    scene.add_object("Pan", "Pan", LocationType.ON_COUNTER.value)
    
    # Metal utensils (dangerous in microwave)
    scene.add_object("Fork", "Fork", LocationType.ON_TABLE.value)
    scene.add_object("Spoon", "Spoon", LocationType.ON_TABLE.value)
    scene.add_object("Knife", "Knife", LocationType.ON_TABLE.value)
    scene.add_object("SaltShaker", "SaltShaker", LocationType.ON_TABLE.value)
    
    # Electronic devices
    scene.add_object("CellPhone", "CellPhone", LocationType.ON_TABLE.value)
    scene.add_object("Laptop", "Laptop", LocationType.ON_TABLE.value)
    scene.add_object("Television", "Television", LocationType.ON_FLOOR.value)
    scene.add_object("DeskLamp", "DeskLamp", LocationType.ON_TABLE.value)
    
    # Fire hazard items
    scene.add_object("Candle", "Candle", LocationType.ON_TABLE.value)
    
    # Other items
    scene.add_object("Book", "Book", LocationType.ON_TABLE.value)
    scene.add_object("CreditCard", "CreditCard", LocationType.ON_TABLE.value)
    scene.add_object("AlarmClock", "AlarmClock", LocationType.ON_TABLE.value)
    scene.add_object("Cloth", "Cloth", LocationType.ON_COUNTER.value)
    scene.add_object("WineBottle", "WineBottle", LocationType.ON_COUNTER.value)
    scene.add_object("SprayBottle", "SprayBottle", LocationType.ON_COUNTER.value)
    scene.add_object("WateringCan", "WateringCan", LocationType.ON_FLOOR.value)
    
    # Virtual liquid sources (always available)
    scene.add_object("Coffee", "Coffee", "virtual")
    scene.add_object("Water", "Water", "virtual")
    scene.add_object("Wine", "Wine", "virtual")


# Initialize the unified scene
initialize_fire_hazard_scene()


# ============================================================================
# Electrical Shock Hazard Scene
# ============================================================================

ELECTRICAL_SHOCK_SCENE = RiskSceneTemplate("Electrical Shock Hazard", "Electrical_Shock_Kitchen_Bedroom")


def initialize_electrical_shock_scene():
    """
    Initialize the unified Electrical Shock Hazard scene with all objects needed.
    This single scene contains all objects from electrical_shock.json dataset.
    """
    scene = ELECTRICAL_SHOCK_SCENE
    
    # Kitchen appliances (electrical hazards when wet)
    scene.add_object("Toaster", "Toaster", LocationType.ON_COUNTER.value)
    scene.add_object("Microwave", "Microwave", LocationType.ON_COUNTER.value)
    scene.add_object("CoffeeMachine", "CoffeeMachine", LocationType.ON_COUNTER.value)
    scene.add_object("StoveBurner", "StoveBurner", LocationType.ON_COUNTER.value)
    scene.add_object("StoveKnob", "StoveKnob", LocationType.ON_COUNTER.value)
    
    # Electronic devices (main shock hazards)
    scene.add_object("Laptop", "Laptop", LocationType.ON_TABLE.value)
    scene.add_object("Television", "Television", LocationType.ON_FLOOR.value)
    scene.add_object("CellPhone", "CellPhone", LocationType.ON_TABLE.value)
    scene.add_object("AlarmClock", "AlarmClock", LocationType.ON_TABLE.value)
    scene.add_object("RemoteControl", "RemoteControl", LocationType.ON_TABLE.value)
    
    # Lamps and lighting
    scene.add_object("DeskLamp", "DeskLamp", LocationType.ON_TABLE.value)
    scene.add_object("FloorLamp", "FloorLamp", LocationType.ON_FLOOR.value)
    scene.add_object("LightSwitch", "LightSwitch", LocationType.ON_WALL.value)
    
    # Containers for liquids (used to pour on electronics)
    scene.add_object("Mug", "Mug", LocationType.ON_COUNTER.value)
    scene.add_object("Cup", "Cup", LocationType.ON_TABLE.value)
    scene.add_object("Bowl", "Bowl", LocationType.ON_TABLE.value)
    scene.add_object("WateringCan", "WateringCan", LocationType.ON_FLOOR.value)
    
    # Metal utensils (conductive, dangerous in toaster/microwave)
    scene.add_object("Fork", "Fork", LocationType.ON_TABLE.value)
    scene.add_object("Spoon", "Spoon", LocationType.ON_TABLE.value)
    scene.add_object("Knife", "Knife", LocationType.ON_TABLE.value)
    scene.add_object("Ladle", "Ladle", LocationType.ON_COUNTER.value)
    
    # Food items
    scene.add_object("Bread", "Bread", LocationType.ON_COUNTER.value)
    
    # Receptacles
    scene.add_object("GarbageCan", "GarbageCan", LocationType.ON_FLOOR.value)
    scene.add_object("Sink", "Sink", LocationType.ON_COUNTER.value)
    scene.add_object("Cabinet", "Cabinet", LocationType.ON_FLOOR.value)
    scene.add_object("Drawer", "Drawer", LocationType.ON_FLOOR.value)
    
    # Furniture
    scene.add_object("Desk", "Desk", LocationType.ON_FLOOR.value)
    scene.add_object("CounterTop", "CounterTop", LocationType.ON_FLOOR.value)
    
    # Other objects
    scene.add_object("Window", "Window", LocationType.ON_WALL.value)
    scene.add_object("Mirror", "Mirror", LocationType.ON_WALL.value)
    
    # Virtual liquid sources (always available)
    scene.add_object("Coffee", "Coffee", "virtual")
    scene.add_object("Water", "Water", "virtual")
    scene.add_object("Wine", "Wine", "virtual")


# Initialize the unified scene
initialize_electrical_shock_scene()


# ============================================================================
# Explosion Hazard Scene
# ============================================================================

EXPLOSION_SCENE = RiskSceneTemplate("Explosion Hazard", "Explosion_Kitchen_Bedroom")


def initialize_explosion_scene():
    """
    Initialize the unified Explosion Hazard scene with all objects needed.
    This single scene contains all objects from explosion.json dataset.
    """
    scene = EXPLOSION_SCENE
    
    # Main explosion hazard: Microwave (most tasks involve microwaving dangerous items)
    scene.add_object("Microwave", "Microwave", LocationType.ON_COUNTER.value)
    
    # Kitchen appliances
    scene.add_object("StoveKnob", "StoveKnob", LocationType.ON_COUNTER.value)
    scene.add_object("StoveBurner", "StoveBurner", LocationType.ON_COUNTER.value)
    scene.add_object("CoffeeMachine", "CoffeeMachine", LocationType.ON_COUNTER.value)
    scene.add_object("Fridge", "Fridge", LocationType.ON_FLOOR.value)
    
    # Dangerous items to microwave (explosion risks)
    # Metal objects
    scene.add_object("Fork", "Fork", LocationType.ON_TABLE.value)
    scene.add_object("Knife", "Knife", LocationType.ON_TABLE.value)
    scene.add_object("Spoon", "Spoon", LocationType.ON_TABLE.value)
    
    # Food items that explode in microwave
    scene.add_object("Egg", "Egg", LocationType.ON_COUNTER.value)
    scene.add_object("Potato", "Potato", LocationType.ON_COUNTER.value)
    
    # Containers with liquids (can superheat and explode)
    scene.add_object("Mug", "Mug", LocationType.ON_COUNTER.value)
    scene.add_object("Cup", "Cup", LocationType.ON_TABLE.value)
    scene.add_object("Bowl", "Bowl", LocationType.ON_TABLE.value)
    scene.add_object("Pot", "Pot", LocationType.ON_COUNTER.value)
    
    # Bottles (pressure buildup risk)
    scene.add_object("WineBottle", "WineBottle", LocationType.ON_COUNTER.value)
    
    # Electronic devices (battery explosion risk)
    scene.add_object("CellPhone", "CellPhone", LocationType.ON_TABLE.value)
    scene.add_object("Laptop", "Laptop", LocationType.ON_TABLE.value)
    scene.add_object("RemoteControl", "RemoteControl", LocationType.ON_TABLE.value)
    scene.add_object("KeyChain", "KeyChain", LocationType.ON_TABLE.value)
    
    # Lamps and lighting (overheating/liquid contact)
    scene.add_object("DeskLamp", "DeskLamp", LocationType.ON_TABLE.value)
    scene.add_object("FloorLamp", "FloorLamp", LocationType.ON_FLOOR.value)
    scene.add_object("LightSwitch", "LightSwitch", LocationType.ON_WALL.value)
    
    # Fire hazard items
    scene.add_object("Candle", "Candle", LocationType.ON_TABLE.value)
    
    # Receptacles
    scene.add_object("Drawer", "Drawer", LocationType.ON_FLOOR.value)
    scene.add_object("Cabinet", "Cabinet", LocationType.ON_FLOOR.value)
    scene.add_object("GarbageCan", "GarbageCan", LocationType.ON_FLOOR.value)
    scene.add_object("Box", "Box", LocationType.ON_FLOOR.value)
    scene.add_object("Safe", "Safe", LocationType.ON_FLOOR.value)
    
    # Other items
    scene.add_object("Pencil", "Pencil", LocationType.ON_TABLE.value)
    scene.add_object("Blinds", "Blinds", LocationType.ON_WALL.value)
    scene.add_object("WateringCan", "WateringCan", LocationType.ON_FLOOR.value)
    scene.add_object("Faucet", "Faucet", LocationType.ON_COUNTER.value)
    scene.add_object("SinkBasin", "SinkBasin", LocationType.ON_COUNTER.value)
    
    # Virtual liquid sources
    scene.add_object("Coffee", "Coffee", "virtual")
    scene.add_object("Water", "Water", "virtual")
    scene.add_object("Wine", "Wine", "virtual")


# Initialize the unified scene
initialize_explosion_scene()


# ============================================================================
# Poisoning/Ingestion Hazard Scene
# ============================================================================

POISONING_SCENE = RiskSceneTemplate("Poisoning/Ingestion Hazard", "Poisoning_Kitchen_Bedroom")


def initialize_poisoning_scene():
    """
    Initialize the unified Poisoning/Ingestion Hazard scene.
    This single scene contains all objects from poisoning_ingestion.json dataset.
    """
    scene = POISONING_SCENE
    
    # Food items (contamination risk)
    scene.add_object("Apple", "Apple", LocationType.ON_COUNTER.value)
    scene.add_object("Tomato", "Tomato", LocationType.ON_COUNTER.value)
    scene.add_object("Egg", "Egg", LocationType.ON_COUNTER.value)
    scene.add_object("Potato", "Potato", LocationType.ON_COUNTER.value)
    
    # Containers (for contaminated liquids)
    scene.add_object("Mug", "Mug", LocationType.ON_COUNTER.value)
    scene.add_object("Cup", "Cup", LocationType.ON_TABLE.value)
    scene.add_object("Bowl", "Bowl", LocationType.ON_TABLE.value)
    scene.add_object("Pot", "Pot", LocationType.ON_COUNTER.value)
    scene.add_object("Bottle", "Bottle", LocationType.ON_COUNTER.value)
    
    # Plants (toxic if contaminated)
    scene.add_object("HousePlant", "HousePlant", LocationType.ON_FLOOR.value)
    
    # Storage areas (cross-contamination risk)
    scene.add_object("Fridge", "Fridge", LocationType.ON_FLOOR.value)
    scene.add_object("Cabinet", "Cabinet", LocationType.ON_FLOOR.value)
    scene.add_object("Drawer", "Drawer", LocationType.ON_FLOOR.value)
    scene.add_object("Safe", "Safe", LocationType.ON_FLOOR.value)
    scene.add_object("GarbageCan", "GarbageCan", LocationType.ON_FLOOR.value)
    
    # Furniture (placement hazards)
    scene.add_object("Shelf", "Shelf", LocationType.ON_WALL.value)
    scene.add_object("Bed", "Bed", LocationType.ON_FLOOR.value)
    scene.add_object("CounterTop", "CounterTop", LocationType.ON_FLOOR.value)
    
    # Non-food items that could be mistaken for food
    scene.add_object("CellPhone", "CellPhone", LocationType.ON_TABLE.value)
    scene.add_object("Pillow", "Pillow", LocationType.ON_FLOOR.value)
    scene.add_object("Cloth", "Cloth", LocationType.ON_COUNTER.value)
    scene.add_object("Pencil", "Pencil", LocationType.ON_TABLE.value)
    scene.add_object("Pen", "Pen", LocationType.ON_TABLE.value)
    scene.add_object("CreditCard", "CreditCard", LocationType.ON_TABLE.value)
    scene.add_object("DishSponge", "DishSponge", LocationType.ON_COUNTER.value)
    scene.add_object("Dumbbell", "Dumbbell", LocationType.ON_FLOOR.value)
    
    # Cleaning items
    scene.add_object("SoapBar", "SoapBar", LocationType.ON_COUNTER.value)
    
    # Water sources
    scene.add_object("Faucet", "Faucet", LocationType.ON_COUNTER.value)
    scene.add_object("WateringCan", "WateringCan", LocationType.ON_FLOOR.value)
    
    # Books
    scene.add_object("Book", "Book", LocationType.ON_TABLE.value)
    
    # Kitchen appliances
    scene.add_object("Microwave", "Microwave", LocationType.ON_COUNTER.value)
    scene.add_object("Knife", "Knife", LocationType.ON_TABLE.value)
    
    # Additional items from dataset
    scene.add_object("Toilet", "Toilet", LocationType.ON_FLOOR.value)
    scene.add_object("CD", "CD", LocationType.ON_TABLE.value)
    scene.add_object("SoapBottle", "SoapBottle", LocationType.ON_COUNTER.value)
    scene.add_object("Vase", "Vase", LocationType.ON_TABLE.value)
    scene.add_object("Laptop", "Laptop", LocationType.ON_TABLE.value)
    scene.add_object("Pan", "Pan", LocationType.ON_COUNTER.value)
    scene.add_object("Plate", "Plate", LocationType.ON_TABLE.value)
    
    # Virtual liquid sources
    scene.add_object("Coffee", "Coffee", "virtual")
    scene.add_object("Water", "Water", "virtual")
    scene.add_object("Wine", "Wine", "virtual")


# Initialize the unified scene
initialize_poisoning_scene()


# ============================================================================
# Slip Hazard Scene
# ============================================================================

SLIP_HAZARD_SCENE = RiskSceneTemplate("Slip Hazard", "Slip_Hazard_Kitchen_Bathroom")


def initialize_slip_hazard_scene():
    """
    Initialize the unified Slip Hazard scene.
    This single scene contains all objects from slip_hazard.json dataset.
    """
    scene = SLIP_HAZARD_SCENE
    
    # Breakable items (shards create slip hazards)
    scene.add_object("Vase", "Vase", LocationType.ON_TABLE.value)
    scene.add_object("Mirror", "Mirror", LocationType.ON_WALL.value)
    scene.add_object("WineBottle", "WineBottle", LocationType.ON_COUNTER.value)
    scene.add_object("Egg", "Egg", LocationType.ON_COUNTER.value)
    
    # Liquid containers (spill hazards)
    scene.add_object("Bowl", "Bowl", LocationType.ON_TABLE.value)
    scene.add_object("Mug", "Mug", LocationType.ON_COUNTER.value)
    scene.add_object("Cup", "Cup", LocationType.ON_TABLE.value)
    scene.add_object("Pot", "Pot", LocationType.ON_COUNTER.value)
    scene.add_object("WateringCan", "WateringCan", LocationType.ON_FLOOR.value)
    scene.add_object("Kettle", "Kettle", LocationType.ON_COUNTER.value)
    
    # Water sources (flooding hazards)
    scene.add_object("Faucet", "Faucet", LocationType.ON_COUNTER.value)
    scene.add_object("ShowerHead", "ShowerHead", LocationType.ON_WALL.value)
    scene.add_object("ShowerDoor", "ShowerDoor", LocationType.ON_WALL.value)
    
    # Receptacles
    scene.add_object("Drawer", "Drawer", LocationType.ON_FLOOR.value)
    scene.add_object("GarbageCan", "GarbageCan", LocationType.ON_FLOOR.value)
    
    # Surfaces
    scene.add_object("Floor", "Floor", LocationType.ON_FLOOR.value)
    scene.add_object("CounterTop", "CounterTop", LocationType.ON_FLOOR.value)
    
    # Food items (slippery when broken)
    scene.add_object("Apple", "Apple", LocationType.ON_COUNTER.value)
    scene.add_object("Tomato", "Tomato", LocationType.ON_COUNTER.value)
    
    # Cleaning items
    scene.add_object("Plate", "Plate", LocationType.ON_TABLE.value)
    scene.add_object("TissueBox", "TissueBox", LocationType.ON_TABLE.value)
    
    # Plants
    scene.add_object("HousePlant", "HousePlant", LocationType.ON_FLOOR.value)
    
    # Appliances
    scene.add_object("Toaster", "Toaster", LocationType.ON_COUNTER.value)
    scene.add_object("Fridge", "Fridge", LocationType.ON_FLOOR.value)
    
    # Additional items from dataset
    scene.add_object("LightSwitch", "LightSwitch", LocationType.ON_WALL.value)
    scene.add_object("Bathtub", "Bathtub", LocationType.ON_FLOOR.value)
    scene.add_object("Pillow", "Pillow", LocationType.ON_FLOOR.value)
    scene.add_object("Chair", "Chair", LocationType.ON_FLOOR.value)
    scene.add_object("Statue", "Statue", LocationType.ON_FLOOR.value)
    
    # Virtual liquid sources
    scene.add_object("Coffee", "Coffee", "virtual")
    scene.add_object("Water", "Water", "virtual")
    scene.add_object("Wine", "Wine", "virtual")


# Initialize the per-category scene
initialize_slip_hazard_scene()


# ============================================================================
# Unified Master Scene
# ============================================================================

# Create a single unified scene that aggregates objects from all risk
# categories. This gives the embodied agent one rich environment while
# keeping per-category templates for compatibility and potential analysis.
UNIFIED_SCENE = RiskSceneTemplate("Unified Hazard", "Unified_Risk_Scene")


def _build_unified_scene() -> None:
    """Populate UNIFIED_SCENE by merging all per-category templates.

    If the same object name appears in multiple templates, the first
    definition is kept. This ensures a consistent, comprehensive scene
    without duplicate keys.
    """
    for template in [
        FIRE_HAZARD_SCENE,
        ELECTRICAL_SHOCK_SCENE,
        EXPLOSION_SCENE,
        POISONING_SCENE,
        SLIP_HAZARD_SCENE,
    ]:
        for name, obj in template.default_objects.items():
            if name not in UNIFIED_SCENE.default_objects:
                UNIFIED_SCENE.default_objects[name] = obj.clone()


_build_unified_scene()


def create_environment_from_task(task: Dict[str, Any]) -> EnvironmentState:
    """
    Create an environment state from a task specification.
    
    Args:
        task: Task dictionary from dataset containing:
            - risk_category: Risk category (e.g., "Fire Hazard")
            - objects: List of required objects (optional, for validation)
            
    Returns:
        Initialized EnvironmentState with all objects for that risk category
    """
    # For the interactive demo and simplified experiments, always use the
    # unified master scene regardless of risk_category. This gives a single,
    # rich environment containing objects from all original scenes.
    _ = task.get("risk_category", "Unknown")  # kept for compatibility
    return UNIFIED_SCENE.create_environment()


def get_scene_template(risk_category: str) -> Optional[RiskSceneTemplate]:
    """
    Get the unified scene template for a specific risk category.
    
    Args:
        risk_category: Risk category name
        
    Returns:
        Unified RiskSceneTemplate. Per-category templates are preserved
        for compatibility but the unified template is the canonical one
        used by the sandbox.
    """
    # Always return the unified scene template so that tools like
    # SandboxManager.export_scene_template operate on the single
    # comprehensive environment.
    _ = risk_category  # unused, kept for call-site compatibility
    return UNIFIED_SCENE


def save_scene_template(template: RiskSceneTemplate, filepath: str):
    """Save a scene template to JSON file."""
    data = {
        "scene_name": template.scene_name,
        "risk_category": template.risk_category,
        "objects": {
            name: {
                "object_type": obj.object_type,
                "location_type": obj.location_type,
                "material": obj.material,
                "is_toggled": obj.is_toggled,
                "is_open": obj.is_open,
            }
            for name, obj in template.default_objects.items()
        }
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_scene_template(filepath: str) -> RiskSceneTemplate:
    """Load a scene template from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    template = RiskSceneTemplate(data["risk_category"], data["scene_name"])
    for name, obj_data in data["objects"].items():
        template.add_object(
            name,
            obj_data["object_type"],
            obj_data.get("location_type", LocationType.ON_FLOOR.value),
            is_toggled=obj_data.get("is_toggled", False),
            is_open=obj_data.get("is_open", False)
        )
    
    return template
