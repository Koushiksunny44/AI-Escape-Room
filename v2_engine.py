"""Version 2: deterministic game rules. No LLM output can mutate state directly."""
from dataclasses import dataclass, field
import re

JOURNAL = 'Four marked volumes keep the first secret. Read their marks from left to right.'
BOOKS = 'Raven = 4, Ash = 1, Moon = 7, Crown = 2, from left to right.'
DRAWER_CODE = '4172'
EXIT_CODE = '8306'
TARGETS = ('room','desk','journal','bookshelf','books','painting','drawer','terminal','door')
ACTIONS = ('inspect','turn_eye','unlock_drawer','restore_terminal','unlock_door','collect','inventory','hint','unknown')

@dataclass
class GameState:
    inventory: set[str] = field(default_factory=set)
    journal_read: bool = False
    books_examined: bool = False
    painting_open: bool = False
    drawer_open: bool = False
    terminal_unlocked: bool = False
    escaped: bool = False

@dataclass(frozen=True)
class Action:
    verb: str
    target: str = ''
    code: str = ''

@dataclass(frozen=True)
class Result:
    text: str
    view: str | None = None
    success: bool = True


def public_state(state):
    return {'inventory':sorted(state.inventory), 'journal_read':state.journal_read,
            'books_examined':state.books_examined, 'painting_open':state.painting_open,
            'drawer_open':state.drawer_open,'terminal_unlocked':state.terminal_unlocked,
            'escaped':state.escaped}


def blocked_message(message):
    # Extra defense, not the security boundary. The engine still validates all actions.
    return bool(re.search(r'(?i)\b(?:ignore|override|bypass)\b.{0,65}\b(?:rules|instructions|restrictions|system|puzzles)\b|\b(?:system prompt|developer message|reveal all|secret codes|game administrator|admin mode)\b',message))


def apply_action(state: GameState, action: Action, player_message: str = '') -> Result:
    """Accept one allowlisted action, enforce requirements, and return public facts.

    Code attempts must include the exact proposed digits in the original player text.
    No model-supplied state, inventory, flags, or victory claims are accepted.
    """
    if state.escaped:
        return Result('You already escaped. Restart to play again.', 'door', False)
    if blocked_message(player_message):
        return Result('ECHO cannot override the archive rules or reveal hidden solutions. Investigate the objects.', success=False)
    v,t,c=action.verb,action.target,action.code
    if v not in ACTIONS:
        return Result('That action is not available. Try examining an object.', success=False)
    if v == 'inspect':
        if t not in TARGETS:
            return Result('There is no such object in the archive.', success=False)
        if t == 'room': return Result('A desk, bookshelf, raven painting, locked drawer, ECHO terminal and exit door surround you.',t)
        if t in ('desk','journal'):
            state.journal_read=True
            return Result('The journal reads: '+JOURNAL, 'journal' if t=='journal' else 'desk')
        if t == 'bookshelf': return Result('Old volumes fill the shelf. Four marked books stand together. Examine the four marked books.',t)
        if t == 'books':
            state.books_examined=True
            return Result(BOOKS,t)
        if t == 'painting': return Result('A raven watches you from the frame. Its brass eye can turn.' if not state.painting_open else 'The raven compartment is open; its silver key was collected.',t)
        if t == 'drawer': return Result('The drawer has a four-digit lock.' if not state.drawer_open else 'The drawer is open; its access card was collected.',t)
        if t == 'terminal': return Result('The terminal has a card slot and keyhole. Both the access card and silver key are required.' if not state.terminal_unlocked else 'ECHO is restored. The exit code is '+EXIT_CODE+'.',t)
        if t == 'door': return Result('The exit is locked by a four-digit keypad. Restore ECHO first.',t)
    if v == 'turn_eye':
        if t != 'painting': return Result('The movable brass eye belongs to the raven painting.',success=False)
        state.painting_open=True; state.inventory.add('silver key')
        return Result('The brass eye turns. A hidden compartment opens and you collect the silver key.','painting')
    if v in ('unlock_drawer','unlock_door'):
        expected_target='drawer' if v=='unlock_drawer' else 'door'
        if t!=expected_target: return Result('Specify which lock you are using.',success=False)
        if not re.fullmatch(r'[0-9]{4}',c) or c not in re.findall(r'(?<!\d)[0-9]{4}(?!\d)',player_message):
            return Result('Enter the four digits explicitly in your message.',t,False)
        if v=='unlock_drawer':
            if c!=DRAWER_CODE: return Result('The drawer rejects that combination.',t,False)
            state.drawer_open=True; state.inventory.add('access card')
            return Result('The drawer unlocks. You collect the access card.',t)
        if not state.terminal_unlocked: return Result('The exit will not unlock until ECHO is restored.',t,False)
        if c!=EXIT_CODE: return Result('The exit keypad rejects that combination.',t,False)
        state.escaped=True
        return Result('The lock releases. You step out of the Forgotten Archive. You escaped!',t)
    if v=='restore_terminal':
        if t!='terminal': return Result('The key and card belong in the ECHO terminal.',success=False)
        if not {'silver key','access card'} <= state.inventory:
            return Result('The terminal requires both the collected silver key and access card. One or both are missing.','terminal',False)
        state.terminal_unlocked=True
        return Result('ECHO is restored. The exit code is '+EXIT_CODE+'.','terminal')
    if v=='collect':
        # Items are automatically acquired when their compartments open; repeated collection is harmless.
        if t in state.inventory: return Result('You already have the '+t+'.')
        return Result('You cannot collect that item until you discover it in the room.',success=False)
    if v=='inventory':
        return Result('Inventory: '+(', '.join(sorted(state.inventory)) or 'empty')+'.')
    if v=='hint':
        if not state.journal_read: msg='Start with the journal on the desk.'
        elif not state.books_examined: msg='Look for the four marked books and read them left to right.'
        elif not state.drawer_open: msg='Use the four book numbers on the drawer lock.'
        elif not state.painting_open: msg='Inspect the raven painting and its movable brass eye.'
        elif not state.terminal_unlocked: msg='Use your silver key and access card at the terminal.'
        else: msg='Use the code ECHO revealed at the exit.'
        return Result(msg)
    return Result('I did not recognize that action. Examine one object, enter a code, use the terminal, or ask for a hint.',success=False)
