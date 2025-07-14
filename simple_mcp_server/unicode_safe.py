"""
Unicode-safe logging utilities for Windows compatibility.
"""

import sys
import logging
from typing import Any


def safe_log_message(message: str) -> str:
    """
    Convert Unicode characters to safe ASCII alternatives for Windows console.
    
    Args:
        message: Original message with potential Unicode characters
        
    Returns:
        Safe ASCII version of the message
    """
    # Map common Unicode characters to ASCII alternatives
    unicode_map = {
        # Test emojis
        '🧪': '[TEST]',
        '✅': '[PASS]',
        '❌': '[FAIL]',
        '🚨': '[ERROR]',
        '📊': '[STATS]',
        '📋': '[INFO]',
        '🔍': '[SEARCH]',
        '🕐': '[TIME]',
        '📄': '[FILE]',
        '⚠️': '[WARN]',
        
        # Other common emojis
        '💻': '[COMPUTER]',
        '🌐': '[WEB]',
        '🔧': '[TOOL]',
        '📝': '[NOTE]',
        '🎯': '[TARGET]',
        '🚀': '[LAUNCH]',
        '⭐': '[STAR]',
        '🔥': '[FIRE]',
        '💡': '[IDEA]',
        '🎉': '[PARTY]',
        '🎊': '[CELEBRATE]',
        '🏆': '[TROPHY]',
        '🥇': '[GOLD]',
        '🔔': '[BELL]',
        '💬': '[CHAT]',
        '📢': '[ANNOUNCE]',
        '🎭': '[MASK]',
        '🎨': '[ART]',
        '🏗️': '[BUILD]',
        '🔨': '[HAMMER]',
        '🔩': '[BOLT]',
        '⚙️': '[GEAR]',
        '🔑': '[KEY]',
        '🗝️': '[OLDKEY]',
        '🗂️': '[FOLDER]',
        '📂': '[FOLDER]',
        '📁': '[FOLDER]',
        '🗄️': '[CABINET]',
        '📊': '[CHART]',
        '📈': '[CHART_UP]',
        '📉': '[CHART_DOWN]',
        '🔢': '[NUMBERS]',
        '📐': '[RULER]',
        '🎯': '[TARGET]',
        '🏃': '[RUNNING]',
        '🏃‍♂️': '[RUNNING]',
        '🏃‍♀️': '[RUNNING]',
        '🚶': '[WALKING]',
        '🚶‍♂️': '[WALKING]',
        '🚶‍♀️': '[WALKING]',
        '🏃🏻': '[RUNNING]',
        '🏃🏼': '[RUNNING]',
        '🏃🏽': '[RUNNING]',
        '🏃🏾': '[RUNNING]',
        '🏃🏿': '[RUNNING]',
        '🌟': '[STAR]',
        '🔰': '[BEGINNER]',
        '🆕': '[NEW]',
        '🆔': '[ID]',
        '🆒': '[COOL]',
        '🆓': '[FREE]',
        '🆖': '[NG]',
        '🆗': '[OK]',
        '🆙': '[UP]',
        '🆚': '[VS]',
        '🈁': '[HERE]',
        '🈂️': '[SERVICE]',
        '🈷️': '[MONTHLY]',
        '🈶': '[NOT_FREE]',
        '🈯': '[RESERVED]',
        '🉐': '[BARGAIN]',
        '🈹': '[DISCOUNT]',
        '🈚': '[FREE_OF_CHARGE]',
        '🈲': '[PROHIBITED]',
        '🉑': '[ACCEPT]',
        '🈸': '[APPLICATION]',
        '🈴': '[PASSING]',
        '🈳': '[VACANCY]',
        '🈺': '[OPEN_FOR_BUSINESS]',
        '🈵': '[FULL]',
        '🔴': '[RED]',
        '🟠': '[ORANGE]',
        '🟡': '[YELLOW]',
        '🟢': '[GREEN]',
        '🔵': '[BLUE]',
        '🟣': '[PURPLE]',
        '🟤': '[BROWN]',
        '⚫': '[BLACK]',
        '⚪': '[WHITE]',
        '🟥': '[RED_SQUARE]',
        '🟧': '[ORANGE_SQUARE]',
        '🟨': '[YELLOW_SQUARE]',
        '🟩': '[GREEN_SQUARE]',
        '🟦': '[BLUE_SQUARE]',
        '🟪': '[PURPLE_SQUARE]',
        '🟫': '[BROWN_SQUARE]',
        '⬛': '[BLACK_SQUARE]',
        '⬜': '[WHITE_SQUARE]',
        '◼️': '[BLACK_MEDIUM_SQUARE]',
        '◻️': '[WHITE_MEDIUM_SQUARE]',
        '◾': '[BLACK_MEDIUM_SMALL_SQUARE]',
        '◽': '[WHITE_MEDIUM_SMALL_SQUARE]',
        '▪️': '[BLACK_SMALL_SQUARE]',
        '▫️': '[WHITE_SMALL_SQUARE]',
    }
    
    # Only convert if we're on Windows and the console might not support Unicode
    if sys.platform == 'win32':
        try:
            # Try to encode the message to see if it works
            message.encode('cp1252')
            # If it works, return as is
            return message
        except UnicodeEncodeError:
            # If encoding fails, replace Unicode characters
            safe_message = message
            for unicode_char, ascii_replacement in unicode_map.items():
                safe_message = safe_message.replace(unicode_char, ascii_replacement)
            return safe_message
    
    # On non-Windows systems, return original message
    return message


class SafeUnicodeFormatter(logging.Formatter):
    """
    Custom logging formatter that handles Unicode characters safely on Windows.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record, making Unicode characters safe for Windows console.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted, Unicode-safe log message
        """
        # Get the original formatted message
        formatted_message = super().format(record)
        
        # Make it safe for Windows console
        return safe_log_message(formatted_message)


def get_safe_console_handler() -> logging.StreamHandler:
    """
    Create a console handler that works safely with Unicode on Windows.
    
    Returns:
        Configured console handler
    """
    handler = logging.StreamHandler(sys.stdout)
    
    # Use our safe formatter
    formatter = SafeUnicodeFormatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    return handler
