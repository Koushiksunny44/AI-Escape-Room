"""Presentation-only view selection. Never changes V1 puzzle state."""
import re

VIEWS = {
    'room': ('Room overview', 'room_preview.png'),
    'desk': ("Scientist's desk", 'inspect_desk.png'),
    'journal': ('Open journal', 'inspect_journal.png'),
    'bookshelf': ('Bookshelf', 'inspect_bookshelf.png'),
    'books': ('Four marked books', 'inspect_books.png'),
    'painting': ('Mysterious painting', 'inspect_painting.png'),
    'drawer': ('Locked drawer', 'inspect_drawer.png'),
    'terminal': ('ECHO terminal', 'inspect_terminal.png'),
    'door': ('Escape door', 'inspect_door.png'),
}

def choose_view(message, proposed=None):
    """Prefer the model's selected view, with a keyword fallback for old replies."""
    if isinstance(proposed, str) and proposed in VIEWS:
        return proposed
    m = message.lower()
    if re.search(r'\b(room|overview)\b', m) and not re.search(r'\b(desk|journal|book|books|bookshelf|painting|drawer|terminal|door)\b',m):
        return 'room'
    patterns = [('journal',r'\b(journal|diary)\b'),('books',r'\b(marked books|marked volumes|four books|four volumes)\b'),('drawer',r'\b(drawer|cabinet)\b'),('painting',r'\b(painting|raven|portrait)\b'),('terminal',r'\b(terminal|computer)\b'),('door',r'\b(door|exit)\b'),('bookshelf',r'\b(bookshelf|bookcase|books|shelf)\b'),('desk',r'\b(desk|table)\b')]
    for view, pattern in patterns:
        if re.search(pattern,m): return view
    return None
