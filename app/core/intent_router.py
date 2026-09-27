from typing import Optional
from enum import Enum

class Intent(Enum):
    INTERESTED = 'interested'
    NOT_INTERESTED = 'not_interested'
    NOT_NOW = 'not_now'
    STOP = 'stop'
    QUESTION = 'question'
    AUTO_REPLY = 'auto_reply'
    ACTION_REQUEST = 'action_request'
    INFORMATION_REQUEST = 'information_request'
    CURVEBALL = 'curveball'
    AMBIGUOUS = 'ambiguous'

class IntentRouter:
    def __init__(self):
        self.interested_patterns = [
            'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'lets do it', 'let us do it',
            'go ahead', 'proceed', 'do it', 'sounds good', 'interested', 'want to',
            'please', 'send it', 'draft it', 'show me', 'tell me more'
        ]
        self.not_interested_patterns = [
            'no', 'nope', 'not interested', 'not now', 'later', 'busy', 'dont want',
            'not needed', 'unsubscribe', 'stop messaging', 'stop sending'
        ]
        self.stop_patterns = [
            'stop', 'unsubscribe', 'opt out', 'leave me alone', 'dont contact',
            'remove me', 'block', 'enough'
        ]
        self.question_patterns = [
            'what', 'how', 'why', 'when', 'where', 'which', 'who', '?',
            'can you', 'could you', 'would you', 'do you'
        ]
        self.action_request_patterns = [
            'i want to join', 'sign me up', 'activate', 'enable', 'start',
            'set up', 'create', 'make it', 'do it for me'
        ]
        self.auto_reply_patterns = [
            'thank you for contacting',
            'our team will respond',
            'auto reply',
            'automated response',
            'we will get back',
            'thanks for reaching out',
            'thank you for your message',
            'currently unavailable'
        ]
    
    def detect(self, message: str, history: list = None) -> Intent:
        msg_lower = message.lower().strip()
        
        # Check auto-reply first
        for pattern in self.auto_reply_patterns:
            if pattern in msg_lower:
                return Intent.AUTO_REPLY
        
        # Check stop
        for pattern in self.stop_patterns:
            if pattern in msg_lower:
                return Intent.STOP
        
        # Check action request
        for pattern in self.action_request_patterns:
            if pattern in msg_lower:
                return Intent.ACTION_REQUEST
        
        # Check not interested first (so 'not interested' doesn't match 'interested')
        for pattern in self.not_interested_patterns:
            if pattern in msg_lower:
                if 'not now' in msg_lower or 'later' in msg_lower:
                    return Intent.NOT_NOW
                return Intent.NOT_INTERESTED
        
        # Check interested
        for pattern in self.interested_patterns:
            if pattern in msg_lower:
                return Intent.INTERESTED

        
        # Check curveball (off-topic) first so specific words override generic questions
        curveball_keywords = ['gst', 'tax', 'filing', 'accounting', 'lawyer', 'legal', 'insurance']
        for kw in curveball_keywords:
            if kw in msg_lower:
                return Intent.CURVEBALL

        # Check question
        for pattern in self.question_patterns:
            if pattern in msg_lower:
                return Intent.QUESTION
        
        return Intent.AMBIGUOUS
    
    def route(self, intent: Intent) -> str:
        routes = {
            Intent.INTERESTED: 'action_flow',
            Intent.NOT_INTERESTED: 'graceful_exit',
            Intent.NOT_NOW: 'wait_and_retry',
            Intent.STOP: 'graceful_exit',
            Intent.QUESTION: 'answer_question',
            Intent.AUTO_REPLY: 'suppress',
            Intent.ACTION_REQUEST: 'action_flow',
            Intent.INFORMATION_REQUEST: 'provide_info',
            Intent.CURVEBALL: 'polite_redirect',
            Intent.AMBIGUOUS: 'clarify',
        }
        return routes.get(intent, 'clarify')
