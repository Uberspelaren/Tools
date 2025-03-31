import curses
from Editor import Editor

def setup_colors():
    """Initialize color pairs for the editor"""
    curses.start_color()
    curses.use_default_colors()
    
    # Basic colors
    curses.init_pair(1, curses.COLOR_WHITE, -1)      # Default text
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Status line
    curses.init_pair(3, curses.COLOR_GREEN, -1)      # Success messages
    curses.init_pair(4, curses.COLOR_YELLOW, -1)     # Warnings
    curses.init_pair(5, curses.COLOR_CYAN, -1)       # Line numbers

def main(stdscr):
    """
    Main entry point for the list editor
    
    Args:
        stdscr: Curses main window
    """
    # Basic setup
    curses.curs_set(1)  # Show cursor
    stdscr.keypad(1)    # Enable keypad
    setup_colors()
    
    # Create editor
    editor = Editor(stdscr)
    
    # Show welcome message
    height, width = stdscr.getmaxyx()
    welcome_msg = "Welcome to List Editor - Press 'i' for insert mode, 'q' to quit"
    stdscr.addstr(0, 0, welcome_msg.center(width)[:width-1], curses.color_pair(3))
    stdscr.refresh()
    curses.napms(5000)  # Show welcome message for 5 seconds
    
    # Main loop
    try:
        editor.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    except Exception as e:
        # Clean up curses
        curses.endwin()
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    # Wrap the main function with curses
    curses.wrapper(main)