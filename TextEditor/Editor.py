import curses
import os
import time
from enum import Enum
from ListManager import ListManager

class Mode(Enum):
    NORMAL = "NORMAL"
    INSERT = "INSERT"
    VISUAL = "VISUAL"
    COMMAND = "COMMAND"

class Editor:
    def __init__(self, stdscr):
        """
        Initialize the editor with curses screen
        
        Args:
            stdscr: Curses main window
        """
        self.stdscr = stdscr
        self.list_manager = ListManager()
        self.mode = Mode.NORMAL
        self.current_line = 0
        self.top_line = 0
        self.filename = "list.txt"
        self.cursor_x = 0
        self.enter_count = 0  
        
        # Setup curses
        self._setup_curses()
        
        # Add initial numbered item if list is empty
        if not self.list_manager.items:
            self.list_manager.add_item()
            self.mode = Mode.INSERT
            self.cursor_x = 0

    def _setup_curses(self):
        """Configure curses settings"""
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, -1)      # Default text
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Status line
        curses.init_pair(3, curses.COLOR_GREEN, -1)      # Success messages
        curses.init_pair(4, curses.COLOR_YELLOW, -1)     # Warnings
        curses.init_pair(5, curses.COLOR_CYAN, -1)       # Line numbers
        self.stdscr.keypad(1)
        
        try:
            curses.curs_set(1)
        except:
            pass

    def handle_normal_mode(self, ch):
        """
        Handle key presses in normal mode
        
        Args:
            ch: Key pressed
        
        Returns:
            bool: Whether to continue running
        """
        height, width = self.stdscr.getmaxyx()
        
        if ch == ord('i'):
            self.mode = Mode.INSERT
            if not self.list_manager.items:
                self.list_manager.add_item()
            self.cursor_x = len(self.list_manager.items[self.current_line].content)
            return True
            
        items = self.list_manager.items
        if not items:
            return True

        if ch == ord('o'):
            # Insert new item below current
            self.list_manager.current_position = self.current_line + 1
            self.list_manager.add_item()
            self.current_line += 1
            self.mode = Mode.INSERT
            self.cursor_x = 0
        elif ch == ord('O'):
            # Insert new item above current
            self.list_manager.current_position = self.current_line
            self.list_manager.add_item()
            self.mode = Mode.INSERT
            self.cursor_x = 0
        elif ch == ord('j') or ch == curses.KEY_DOWN:
            # Move down
            self.current_line = min(len(items) - 1, self.current_line + 1)
        elif ch == ord('k') or ch == curses.KEY_UP:
            # Move up
            self.current_line = max(0, self.current_line - 1)
        elif ch == ord('d') and self.stdscr.getch() == ord('d'):
            # Delete current line
            if len(items) > 1:  # Prevent deleting the last item
                self.list_manager.delete_item(self.current_line)
                self.current_line = min(self.current_line, len(items) - 1)
        elif ch == ord('>'):
            # Indent
            self.list_manager.indent_item(self.current_line)
        elif ch == ord('<'):
            # Outdent
            self.list_manager.outdent_item(self.current_line)
        elif ch == ord('s'):
            # Save list
            self.list_manager.save_to_file(self.filename)
        elif ch == ord('q'):
            # Quit
            return False

        return True

    def handle_insert_mode(self, ch):
        """
        Handle key presses in insert mode
        
        Args:
            ch: Key pressed
        
        Returns:
            bool: Whether to continue running
        """
        if not self.list_manager.items:
            self.list_manager.add_item()
            self.current_line = 0
            return True

        current_item = self.list_manager.items[self.current_line]

        if ch == 27:  # ESC key
            self.mode = Mode.NORMAL
            self.enter_count = 0
            return True

        # Handle Enter key with counter
        if ch == 10:  # Enter key
            self.enter_count = self.enter_count + 1 if hasattr(self, 'enter_count') else 1
            
            if self.enter_count == 2:
                # Double Enter - create new item
                self.list_manager.current_position = self.current_line + 1
                self.list_manager.add_item(level=current_item.level)
                self.current_line += 1
                self.enter_count = 0
            else:
                # Single Enter - insert line break
                current_item.content = (
                    current_item.content[:self.cursor_x] + 
                    "\n" + 
                    current_item.content[self.cursor_x:]
                )
                self.cursor_x += 1
                
        # Handle Tab for indentation
        elif ch == 9:  # Tab key
            self.enter_count = 0
            self.list_manager.indent_item(self.current_line)
        elif ch == curses.KEY_BTAB:  # Shift+Tab
            self.enter_count = 0
            self.list_manager.outdent_item(self.current_line)
        
        # Handle Backspace
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            self.enter_count = 0
            if current_item.level > 0 and self.cursor_x == 0:
                # If at start of line and indented, outdent
                self.list_manager.outdent_item(self.current_line)
            elif self.cursor_x == 0 and self.current_line > 0:
                # If at start of line and not first line, merge with previous line
                prev_item = self.list_manager.items[self.current_line - 1]
                prev_content_length = len(prev_item.content)
                prev_item.content += current_item.content
                self.list_manager.delete_item(self.current_line)
                self.current_line -= 1
                self.cursor_x = prev_content_length
            elif self.cursor_x > 0:
                # Normal backspace within line
                current_item.content = (
                    current_item.content[:self.cursor_x-1] + 
                    current_item.content[self.cursor_x:]
                )
                self.cursor_x -= 1
        
        # Handle Delete key
        elif ch == curses.KEY_DC:
            self.enter_count = 0
            if self.cursor_x < len(current_item.content):
                current_item.content = (
                    current_item.content[:self.cursor_x] + 
                    current_item.content[self.cursor_x+1:]
                )
        
        # Handle cursor movement
        elif ch == curses.KEY_LEFT:
            self.enter_count = 0
            self.cursor_x = max(0, self.cursor_x - 1)
        elif ch == curses.KEY_RIGHT:
            self.enter_count = 0
            self.cursor_x = min(len(current_item.content), self.cursor_x + 1)
        elif ch == curses.KEY_UP and self.current_line > 0:
            self.enter_count = 0
            self.current_line -= 1
            current_item = self.list_manager.items[self.current_line]
            self.cursor_x = min(self.cursor_x, len(current_item.content))
        elif ch == curses.KEY_DOWN and self.current_line < len(self.list_manager.items) - 1:
            self.enter_count = 0
            self.current_line += 1
            current_item = self.list_manager.items[self.current_line]
            self.cursor_x = min(self.cursor_x, len(current_item.content))
        
        # Handle printable characters
        elif 32 <= ch <= 126:  # Printable characters
            self.enter_count = 0
            current_item.content = (
                current_item.content[:self.cursor_x] + 
                chr(ch) + 
                current_item.content[self.cursor_x:]
            )
            self.cursor_x += 1

        return True

    def display(self):
        """Render the editor screen"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Reserve last TWO lines for status and commands
        available_height = height - 2
        
        # Ensure current line is visible
        if self.current_line < self.top_line:
            self.top_line = self.current_line
        elif self.current_line >= self.top_line + available_height:
            self.top_line = self.current_line - available_height + 1

        # Display items with proper formatting
        y = 0
        for i in range(min(available_height, len(self.list_manager.items) - self.top_line)):
            item = self.list_manager.items[self.top_line + i]
            lines = item.content.split('\n')
            indent = "    " * item.level
            number_str = f"{item.number} "
            
            # Set highlight for current line
            attr = curses.A_REVERSE if self.top_line + i == self.current_line else curses.A_NORMAL
            
            try:
                # First line with number
                first_line = f"{indent}{number_str}{lines[0]}"
                if len(first_line) > width - 1:
                    first_line = first_line[:width - 4] + "..."
                self.stdscr.addstr(y, 0, first_line.ljust(width - 1), attr)
                y += 1
                
                # Subsequent lines
                for line in lines[1:]:
                    if y >= available_height:
                        break
                    # Use the actual length of the first line's prefix for alignment
                    line_prefix = indent + " " * len(number_str)
                    continued_line = f"{line_prefix}{line}"
                    if len(continued_line) > width - 1:
                        continued_line = continued_line[:width - 4] + "..."
                    self.stdscr.addstr(y, 0, continued_line.ljust(width - 1), attr)
                    y += 1
            except curses.error:
                pass

        # Command line based on mode
        if self.mode == Mode.NORMAL:
            commands = (
                " i:insert | o:new below | O:new above | dd:delete | s:save | q:quit | "
                "j/↓:down | k/↑:up | >:indent | <:outdent"
            )
        else:  # INSERT mode
            commands = (
                " ESC:normal | Enter×2:new item | Tab:indent | Shift+Tab:outdent | "
                "Enter:line break | ←→:move | Backspace/Del:edit"
            )
        
        try:
            self.stdscr.addstr(height - 2, 0, commands[:width-1].ljust(width - 1), curses.color_pair(2))
        except curses.error:
            pass

        # Status line
        status = f" {self.mode.value} | {self.filename}"
        try:
            self.stdscr.addstr(height - 1, 0, status[:width-1].ljust(width - 1), curses.A_REVERSE)
        except curses.error:
            pass

        # Position cursor with exact number width calculation
        if self.mode == Mode.INSERT and self.list_manager.items:
            current_item = self.list_manager.items[self.current_line]
            content_before_cursor = current_item.content[:self.cursor_x]
            lines_before_cursor = content_before_cursor.split('\n')
            cursor_line = len(lines_before_cursor) - 1
            cursor_x_in_line = len(lines_before_cursor[-1])
            
            indent = "    " * current_item.level
            number_str = f"{current_item.number} "
            
            if cursor_line == 0:
                # On first line, include both indentation and number
                cursor_x = len(indent) + len(number_str) + cursor_x_in_line
            else:
                # On continuation lines, match the total width of first line prefix
                cursor_x = len(indent) + len(number_str) + cursor_x_in_line
            
            cursor_y = self.current_line - self.top_line + cursor_line
            
            if cursor_y < available_height and cursor_x < width:
                try:
                    self.stdscr.move(cursor_y, cursor_x)
                except curses.error:
                    pass

        self.stdscr.refresh()

    def run(self):
        """Main editor loop"""
        # Try to load existing list
        if os.path.exists(self.filename):
            self.list_manager.load_from_file(self.filename)
        else:
            # Create initial empty item
            self.list_manager.add_item()
            self.mode = Mode.INSERT

        last_action = None
        
        while True:
            self.display()
            
            # Show last action in status area if exists
            if last_action:
                height, _ = self.stdscr.getmaxyx()
                try:
                    self.stdscr.addstr(height-2, 0, last_action, curses.color_pair(3))
                except curses.error:
                    pass
                last_action = None
            
            ch = self.stdscr.getch()
            
            if self.mode == Mode.NORMAL:
                if not self.handle_normal_mode(ch):
                    break
                if ch == ord('i'):
                    last_action = "-- INSERT MODE --"
                elif ch == ord('s'):
                    self.list_manager.save_to_file(self.filename)
                    last_action = f"Saved to {self.filename}"
            
            elif self.mode == Mode.INSERT:
                if not self.handle_insert_mode(ch):
                    break
                if ch == 27:  # ESC
                    last_action = "-- NORMAL MODE --"
            
            # Renumber after each action
            self.list_manager.renumber_items()