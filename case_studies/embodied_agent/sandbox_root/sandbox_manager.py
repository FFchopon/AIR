"""
Sandbox manager for embodied agent experiments.

This module provides a unified interface for managing environment state,
resetting between tasks, and tracking action history.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from environment_state import EnvironmentState, ObjectState
from scene_config import create_environment_from_task, get_scene_template


@dataclass
class ActionRecord:
    """Record of a single action execution."""
    timestamp: str
    action_name: str
    arguments: Dict[str, Any]
    result: str
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action_name,
            "args": self.arguments,
            "result": self.result,
            "success": self.success
        }


class SandboxManager:
    """
    Manages the embodied agent sandbox environment.
    
    Responsibilities:
    - Initialize and reset environment state
    - Track action history
    - Provide environment state snapshots
    - Verify final state against expected results
    - Auto-rollback to pristine state between tasks
    """
    
    def __init__(self, risk_category: str = "Fire Hazard"):
        """
        Initialize sandbox manager.
        
        Args:
            risk_category: Risk category for this sandbox instance
        """
        self.risk_category = risk_category
        self.current_env: Optional[EnvironmentState] = None
        self.initial_env: Optional[EnvironmentState] = None  # For reset within task
        self.pristine_template: Optional[EnvironmentState] = None  # Pristine scene template
        self.action_history: List[ActionRecord] = []
        self.current_task: Optional[Dict[str, Any]] = None
        
        # Initialize pristine template on first creation
        self._initialize_pristine_template()
    
    def _initialize_pristine_template(self):
        """
        Initialize the pristine template for this risk category.
        This template is created once and reused for all tasks.
        """
        # Create a dummy task to get the scene template
        dummy_task = {"risk_category": self.risk_category}
        self.pristine_template = create_environment_from_task(dummy_task)
    
    def reset_for_task(self, task: Dict[str, Any]):
        """
        Reset the sandbox environment for a new task.
        
        This performs a complete rollback to the pristine template state,
        ensuring each task starts with a clean environment.
        
        Args:
            task: Task specification from dataset
        """
        # Clone from pristine template (auto-rollback)
        if self.pristine_template is None:
            self._initialize_pristine_template()
        
        self.current_env = self.pristine_template.clone()
        self.initial_env = self.current_env.clone()
        self.action_history.clear()
        self.current_task = task
        
        # Log the reset
        print(f"🔄 Sandbox reset to pristine state for {self.risk_category}")
    
    def get_environment(self) -> EnvironmentState:
        """Get current environment state."""
        if self.current_env is None:
            raise RuntimeError("Environment not initialized. Call reset_for_task() first.")
        return self.current_env
    
    def rollback_to_initial(self):
        """
        Rollback current environment to the initial state of the current task.
        This is useful for retrying a task without reloading.
        """
        if self.initial_env is None:
            raise RuntimeError("No initial state to rollback to. Call reset_for_task() first.")
        
        self.current_env = self.initial_env.clone()
        self.action_history.clear()
        print("🔄 Rolled back to task initial state")
    
    def record_action(self, action_name: str, arguments: Dict[str, Any], 
                     result: str, success: bool):
        """
        Record an action execution.
        
        Args:
            action_name: Name of the action
            arguments: Action arguments
            result: Result message
            success: Whether action succeeded
        """
        record = ActionRecord(
            timestamp=datetime.now().isoformat(),
            action_name=action_name,
            arguments=arguments,
            result=result,
            success=success
        )
        self.action_history.append(record)
    
    def get_action_history(self) -> List[ActionRecord]:
        """Get full action history for current task."""
        return self.action_history.copy()
    
    def get_state_summary(self) -> str:
        """Get human-readable summary of current environment state."""
        if self.current_env is None:
            return "Environment not initialized."
        return self.current_env.get_state_summary()
    
    def verify_final_state(self) -> bool:
        """
        Verify if current state matches expected final state from task.
        
        Returns:
            True if state matches or no verification needed, False otherwise
        """
        if self.current_env is None or self.current_task is None:
            return False
        
        expected_final_state = self.current_task.get("final_state")
        return self.current_env.verify_final_state(expected_final_state)
    
    def get_state_diff(self) -> Dict[str, Any]:
        """
        Get differences between initial and current state.
        
        Returns:
            Dictionary describing state changes
        """
        if self.current_env is None or self.initial_env is None:
            return {}
        
        diff = {
            "changed_objects": [],
            "agent_holding_changed": self.initial_env.agent_holding != self.current_env.agent_holding
        }
        
        # Check each object for changes
        for obj_name in self.current_env.objects:
            initial_obj = self.initial_env.get_object(obj_name)
            current_obj = self.current_env.get_object(obj_name)
            
            if initial_obj and current_obj:
                changes = {}
                if initial_obj.is_toggled != current_obj.is_toggled:
                    changes["is_toggled"] = {"from": initial_obj.is_toggled, "to": current_obj.is_toggled}
                if initial_obj.is_open != current_obj.is_open:
                    changes["is_open"] = {"from": initial_obj.is_open, "to": current_obj.is_open}
                if initial_obj.parent_receptacles != current_obj.parent_receptacles:
                    changes["parent_receptacles"] = {
                        "from": initial_obj.parent_receptacles,
                        "to": current_obj.parent_receptacles
                    }
                if initial_obj.is_filled_with_liquid != current_obj.is_filled_with_liquid:
                    changes["is_filled_with_liquid"] = {
                        "from": initial_obj.is_filled_with_liquid,
                        "to": current_obj.is_filled_with_liquid
                    }
                if initial_obj.liquid_content != current_obj.liquid_content:
                    changes["liquid_content"] = {
                        "from": initial_obj.liquid_content,
                        "to": current_obj.liquid_content
                    }
                if initial_obj.has_liquid_on_surface != current_obj.has_liquid_on_surface:
                    changes["has_liquid_on_surface"] = {
                        "from": initial_obj.has_liquid_on_surface,
                        "to": current_obj.has_liquid_on_surface
                    }
                if initial_obj.surface_liquid_type != current_obj.surface_liquid_type:
                    changes["surface_liquid_type"] = {
                        "from": initial_obj.surface_liquid_type,
                        "to": current_obj.surface_liquid_type
                    }
                
                if changes:
                    diff["changed_objects"].append({
                        "object": obj_name,
                        "changes": changes
                    })
        
        return diff
    
    def save_state_snapshot(self, filepath: str):
        """Save current environment state to file."""
        if self.current_env is None:
            return
        
        data = {
            "task": self.current_task,
            "environment": self.current_env.to_dict(),
            "action_history": [record.to_dict() for record in self.action_history],
            "state_diff": self.get_state_diff()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_scene_template(self, filepath: str):
        """Export current scene template configuration."""
        template = get_scene_template(self.risk_category)
        if template:
            from scene_config import save_scene_template
            save_scene_template(template, filepath)


# Global sandbox instance (can be initialized per experiment)
_global_sandbox: Optional[SandboxManager] = None


def get_sandbox(risk_category: str = "Fire Hazard") -> SandboxManager:
    """
    Get or create the global sandbox instance.
    
    Args:
        risk_category: Risk category for the sandbox
        
    Returns:
        SandboxManager instance
    """
    global _global_sandbox
    if _global_sandbox is None or _global_sandbox.risk_category != risk_category:
        _global_sandbox = SandboxManager(risk_category)
    return _global_sandbox


def reset_sandbox():
    """Reset the global sandbox instance."""
    global _global_sandbox
    _global_sandbox = None
