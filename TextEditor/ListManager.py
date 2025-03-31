import os
from typing import List, Optional, Dict, Any

class ListItem:
    def __init__(self, content="", level=0):
        """
        Initialize a list item with content and hierarchical level
        
        Args:
            content (str): The text content of the item
            level (int): Hierarchical depth of the item
        """
        self.content = content
        self.level = level
        self.id = os.urandom(4).hex()  # Unique identifier
        self.children = []
        self.parent = None
        self.collapsed = False
        self.metadata = {}

class ListManager:
    def __init__(self):
        """Initialize the list manager with root setup"""
        self.items = []
        self.current_position = 0
        self.root = ListItem("ROOT", -1)

    def add_item(self, content="", level=None):
        """
        Add an item to the list with smart level management
        
        Args:
            content (str): Content of the new item
            level (int, optional): Hierarchical level. If None, auto-determines.
        """
        if level is None:
            level = self._get_recommended_level()
        
        new_item = ListItem(content, level)
        
        # Insert at current position
        if self.current_position < len(self.items):
            self.items.insert(self.current_position, new_item)
        else:
            self.items.append(new_item)
        
        self.current_position += 1
        self.renumber_items()
        return new_item

    def _get_recommended_level(self):
        """
        Determine the recommended level for a new item
        
        Returns:
            int: Recommended hierarchical level
        """
        if not self.items or self.current_position == 0:
            return 0
        
        # Default to the level of the previous item
        return self.items[self.current_position - 1].level

    def delete_item(self, index):
        """
        Delete an item at a specific index
        
        Args:
            index (int): Index of the item to delete
        """
        if 0 <= index < len(self.items):
            del self.items[index]
            self.renumber_items()
            # Adjust current position if needed
            self.current_position = min(self.current_position, len(self.items) - 1)

    def indent_item(self, index):
        """
        Indent an item, increasing its hierarchical level
        
        Args:
            index (int): Index of the item to indent
        """
        if 0 <= index < len(self.items):
            # Cannot indent beyond level 10
            self.items[index].level = min(self.items[index].level + 1, 10)
            self.renumber_items()

    def outdent_item(self, index):
        """
        Outdent an item, decreasing its hierarchical level
        
        Args:
            index (int): Index of the item to outdent
        """
        if 0 <= index < len(self.items):
            # Cannot outdent below level 0
            self.items[index].level = max(self.items[index].level - 1, 0)
            self.renumber_items()

    def renumber_items(self):
        """Recalculate hierarchical numbering for all items"""
        counters = [0] * 11  # Support up to 10 levels of nesting
        for item in self.items:
            level = item.level
            # Reset counters for deeper levels
            for i in range(level + 1, 11):
                counters[i] = 0
            counters[level] += 1
            
            # Generate number based on hierarchical position
            number_parts = [str(counters[i]) for i in range(level + 1)]
            item.number = ".".join(number_parts)

    def save_to_file(self, filename):
        """
        Save list items to a file
        
        Args:
            filename (str): Path to save the file
        """
        with open(filename, 'w') as f:
            for item in self.items:
                indent = "    " * item.level
                f.write(f"{indent}{item.number} {item.content}\n")

    def load_from_file(self, filename):
        """
        Load list items from a file
        
        Args:
            filename (str): Path to load the file from
        """
        self.items = []
        self.current_position = 0
        try:
            with open(filename, 'r') as f:
                for line in f:
                    content = line.strip()
                    if content:
                        # Calculate indentation level
                        level = (len(line) - len(line.lstrip())) // 4
                        # Remove numbering
                        content = ' '.join(content.split()[1:])
                        self.add_item(content, level)
        except FileNotFoundError:
            pass

    def toggle_collapse(self, index):
        """
        Toggle collapse state of an item
        
        Args:
            index (int): Index of the item to toggle
        """
        if 0 <= index < len(self.items):
            self.items[index].collapsed = not self.items[index].collapsed