"""
Flow parser module for Featherflow
"""
import json
from typing import Dict, List, Any, Set, Tuple

def parse_flow(flow_def: Dict) -> Dict:
    """
    Parse and validate a flow definition
    
    Args:
        flow_def: Flow definition dictionary from JSON
        
    Returns:
        Validated and processed flow definition
    """
    # Validate required fields
    required_fields = ["name", "tasks"]
    for field in required_fields:
        if field not in flow_def:
            raise ValueError(f"Flow definition missing required field: {field}")
    
    # Validate tasks
    if not isinstance(flow_def["tasks"], list) or not flow_def["tasks"]:
        raise ValueError("Flow must contain at least one task")
    
    # Check for task IDs and dependencies
    task_ids = set()
    for task in flow_def["tasks"]:
        if "id" not in task:
            raise ValueError("Each task must have an ID")
        if "script" not in task:
            raise ValueError(f"Task {task['id']} missing 'script' field")
        
        task_ids.add(task["id"])
    
    # Validate dependencies
    for task in flow_def["tasks"]:
        if "depends_on" in task:
            if not isinstance(task["depends_on"], list):
                task["depends_on"] = [task["depends_on"]]
                
            for dep in task["depends_on"]:
                if dep not in task_ids:
                    raise ValueError(f"Task {task['id']} depends on non-existent task {dep}")
    
    # Check for cycles in the dependency graph
    check_for_cycles(flow_def["tasks"])
    
    return flow_def

def check_for_cycles(tasks: List[Dict]) -> None:
    """
    Check for cycles in the task dependency graph
    
    Args:
        tasks: List of task dictionaries
        
    Raises:
        ValueError: If a cycle is detected
    """
    # Build dependency graph
    graph = {task["id"]: task.get("depends_on", []) for task in tasks}
    
    # Detect cycles using DFS
    visited = set()
    rec_stack = set()
    
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                raise ValueError(f"Cycle detected in task dependencies involving {node} and {neighbor}")
        
        rec_stack.remove(node)
        return False
    
    # Run DFS from each unvisited node
    for node in graph:
        if node not in visited:
            dfs(node)

def get_execution_order(tasks: List[Dict]) -> List[str]:
    """
    Determine the execution order for tasks based on dependencies
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        List of task IDs in execution order
    """
    # Build dependency graph
    graph = {task["id"]: task.get("depends_on", []) for task in tasks}
    
    # Topological sort
    visited = set()
    temp_visited = set()
    order = []
    
    def visit(node):
        if node in temp_visited:
            raise ValueError(f"Cycle detected in task dependencies involving {node}")
        if node not in visited:
            temp_visited.add(node)
            for dep in graph[node]:
                visit(dep)
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)
    
    # Visit all nodes
    for node in graph:
        if node not in visited:
            visit(node)
    
    # Reverse to get correct order
    return list(reversed(order))