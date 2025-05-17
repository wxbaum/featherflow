#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Display utilities for Featherflow CLI
"""

import sys
import time
import curses
import shutil
from datetime import datetime, timedelta

def format_time_delta(delta):
    """Format a timedelta into a readable string"""
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def colorize(text, color=None, style=None):
    """
    Add ANSI color codes to text
    
    Args:
        text (str): Text to colorize
        color (str): Color name (red, green, yellow, blue, magenta, cyan)
        style (str): Text style (bold, underline)
        
    Returns:
        str: Colorized text
    """
    # Check if terminal supports colors
    if not sys.stdout.isatty():
        return text
    
    colors = {
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    
    styles = {
        "bold": "1",
        "underline": "4",
    }
    
    codes = []
    if color and color in colors:
        codes.append(colors[color])
    if style and style in styles:
        codes.append(styles[style])
    
    if not codes:
        return text
    
    return f"\033[{';'.join(codes)}m{text}\033[0m"

def status_indicator(status):
    """Get a colored status indicator"""
    if status == "running":
        return colorize("●", "green")
    elif status == "success":
        return colorize("✓", "green")
    elif status == "failed":
        return colorize("✗", "red")
    elif status == "pending":
        return colorize("○", "yellow")
    else:
        return colorize("?", "blue")

def draw_progress_bar(percentage, width=20):
    """Draw a progress bar"""
    filled_width = int(width * percentage / 100)
    empty_width = width - filled_width
    
    bar = "█" * filled_width + "░" * empty_width
    
    if percentage < 30:
        return colorize(bar, "red")
    elif percentage < 70:
        return colorize(bar, "yellow")
    else:
        return colorize(bar, "green")

def dashboard_view(scheduler_instance):
    """
    Display an interactive dashboard view of the scheduler
    
    Args:
        scheduler_instance (Scheduler): The scheduler instance
    """
    try:
        # Initialize curses
        stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_CYAN, -1)
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        stdscr.timeout(1000)  # Refresh every 1000ms
        
        while True:
            # Check if screen size is adequate
            height, width = stdscr.getmaxyx()
            if height < 20 or width < 80:
                stdscr.clear()
                stdscr.addstr(0, 0, "Terminal too small. Min size: 80x20")
                stdscr.refresh()
                key = stdscr.getch()
                if key == ord('q'):
                    break
                continue
            
            # Clear the screen
            stdscr.clear()
            
            # Draw the header
            header = "FEATHERFLOW SCHEDULER DASHBOARD"
            stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "=" * width)
            
            # Get data from the scheduler
            schedules = scheduler_instance.schedule_manager.get_all_schedules()
            running_flows = scheduler_instance.running_flows
            
            # Display overview info
            now = datetime.now()
            stdscr.addstr(3, 2, f"Status: ", curses.A_BOLD)
            if scheduler_instance.is_running():
                stdscr.addstr(3, 10, "RUNNING", curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.addstr(3, 10, "STOPPED", curses.color_pair(2) | curses.A_BOLD)
            
            stdscr.addstr(4, 2, f"Schedules: {len(schedules)}")
            stdscr.addstr(5, 2, f"Running flows: {len(running_flows)}")
            
            # Display next scheduled flows
            stdscr.addstr(7, 2, "UPCOMING FLOWS:", curses.A_BOLD)
            if schedules:
                # Sort by next run time
                upcoming = sorted(
                    [s for s in schedules if s.enabled and s.next_run],
                    key=lambda s: s.next_run
                )
                
                for i, schedule in enumerate(upcoming[:5]):  # Show up to 5 upcoming
                    time_until = schedule.next_run - now
                    time_str = format_time_delta(time_until)
                    
                    row = 9 + i
                    if row >= height - 1:
                        break
                        
                    stdscr.addstr(row, 4, f"{schedule.flow_name}: ")
                    if time_until.total_seconds() < 60:  # Less than a minute
                        stdscr.addstr(f"in {time_str}", curses.color_pair(3) | curses.A_BOLD)
                    else:
                        stdscr.addstr(f"in {time_str}")
                    stdscr.addstr(f" ({schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                stdscr.addstr(9, 4, "No schedules defined")
            
            # Display running flows
            max_name_len = 20
            stdscr.addstr(15, 2, "RUNNING FLOWS:", curses.A_BOLD)
            if running_flows:
                # Header
                stdscr.addstr(17, 4, "FLOW".ljust(max_name_len))
                stdscr.addstr(17, 4 + max_name_len + 2, "RUNTIME".ljust(15))
                stdscr.addstr(17, 4 + max_name_len + 2 + 15 + 2, "STATUS")
                
                for i, (flow_name, flow_info) in enumerate(running_flows.items()):
                    row = 18 + i
                    if row >= height - 1:
                        break
                        
                    # Truncate flow name if too long
                    display_name = flow_name
                    if len(display_name) > max_name_len:
                        display_name = display_name[:max_name_len-3] + "..."
                    
                    # Calculate runtime
                    elapsed = now - flow_info["start_time"]
                    runtime = format_time_delta(elapsed)
                    
                    # Display flow info
                    stdscr.addstr(row, 4, display_name.ljust(max_name_len))
                    stdscr.addstr(row, 4 + max_name_len + 2, runtime.ljust(15))
                    stdscr.addstr(row, 4 + max_name_len + 2 + 15 + 2, "●", curses.color_pair(1))
                    stdscr.addstr(" Running")
            else:
                stdscr.addstr(17, 4, "No flows currently running")
            
            # Footer
            stdscr.addstr(height - 2, 0, "=" * width)
            stdscr.addstr(height - 1, 2, "Press 'q' to exit, 'r' to refresh")
            
            # Refresh the screen
            stdscr.refresh()
            
            # Handle key input
            key = stdscr.getch()
            if key == ord('q'):
                break
    finally:
        # Clean up curses
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

def print_schedule_status(scheduler_instance):
    """
    Print a colorful status report of the scheduler
    
    Args:
        scheduler_instance (Scheduler): The scheduler instance
    """
    if scheduler_instance.is_running():
        print(colorize("● Scheduler is running", "green", "bold"))
        
        # Show active schedules
        schedules = scheduler_instance.schedule_manager.get_all_schedules()
        if schedules:
            print(f"\nMonitoring {colorize(str(len(schedules)), 'cyan')} schedules")
            
            # Create a table-like structure
            terminal_width = shutil.get_terminal_size().columns
            header = f"{'FLOW NAME':<20} {'SCHEDULE':<20} {'NEXT RUN':<25} {'STATUS':<10}"
            print(f"\n{colorize(header, style='bold')}")
            print("-" * min(len(header), terminal_width))
            
            # Show next upcoming schedule
            upcoming = sorted(
                [s for s in schedules if s.enabled and s.next_run],
                key=lambda s: s.next_run
            )
            
            for schedule in upcoming[:10]:  # Show top 10
                now = datetime.now()
                next_run_str = schedule.next_run.strftime("%Y-%m-%d %H:%M:%S")
                time_until = schedule.next_run - now
                minutes_until = int(time_until.total_seconds() / 60)
                
                # Format status with color
                if schedule.running:
                    status = colorize("● Running", "green")
                elif not schedule.enabled:
                    status = colorize("○ Disabled", "yellow")
                elif minutes_until < 5:
                    status = colorize("○ Pending", "cyan")
                else:
                    status = colorize("○ Scheduled", "blue")
                
                # Format row
                flow_name = schedule.flow_name
                if len(flow_name) > 20:
                    flow_name = flow_name[:17] + "..."
                
                cron_expr = schedule.cron_expression
                if len(cron_expr) > 20:
                    cron_expr = cron_expr[:17] + "..."
                
                print(f"{flow_name:<20} {cron_expr:<20} {next_run_str:<25} {status}")
            
            # Show currently running flows
            running_flows = scheduler_instance.running_flows
            if running_flows:
                print(f"\n{colorize('RUNNING FLOWS', style='bold')}:")
                running_header = f"{'FLOW NAME':<20} {'STARTED AT':<20} {'RUNTIME':<15}"
                print(f"{colorize(running_header, style='bold')}")
                print("-" * min(len(running_header), terminal_width))
                
                for flow_name, flow_info in running_flows.items():
                    start_time = flow_info["start_time"]
                    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
                    elapsed = datetime.now() - start_time
                    runtime = format_time_delta(elapsed)
                    
                    # Format flow name
                    if len(flow_name) > 20:
                        flow_name = flow_name[:17] + "..."
                    
                    print(f"{flow_name:<20} {start_str:<20} {runtime:<15}")
        else:
            print(colorize("\nNo schedules defined", "yellow"))
            
        print(f"\nStatistics:")
        print(f"  Check interval: {scheduler_instance.check_interval} seconds")
        # We need to add a _start_time attribute to the Scheduler class
        uptime = datetime.now() - getattr(scheduler_instance, '_start_time', datetime.now())
        print(f"  Uptime: {format_time_delta(uptime)}")
    else:
        print(colorize("○ Scheduler is not running", "red"))
        print("\nStart the scheduler with: featherflow scheduler start")