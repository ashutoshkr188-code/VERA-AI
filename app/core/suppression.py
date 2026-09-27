from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
import hashlib
import json

class SuppressionEntry(BaseModel):
    key: str
    merchant_id: str
    trigger_id: str
    opportunity_type: str
    message_hash: str
    last_sent: datetime
    nudge_count: int = 0
    last_response: Optional[str] = None
    expires_at: Optional[datetime] = None

class SuppressionEngine:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.cooldown_hours = self.config.get('cooldown_hours', 24)
        self.max_nudges = self.config.get('max_nudges', 3)
        self._store: Dict[str, SuppressionEntry] = {}
    
    def _make_key(self, merchant_id: str, trigger_id: str, opportunity_type: str) -> str:
        return f'{merchant_id}:{trigger_id}:{opportunity_type}'
    
    def _hash_message(self, body: str) -> str:
        return hashlib.md5(body.encode()).hexdigest()[:16]
    
    def should_suppress(self, merchant_id: str, trigger_id: str, opportunity_type: str, body: str) -> tuple[bool, str]:
        key = self._make_key(merchant_id, trigger_id, opportunity_type)
        entry = self._store.get(key)
        
        if not entry:
            return False, ''
        
        # Check expiry
        if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
            del self._store[key]
            return False, ''
        
        # Check cooldown
        if datetime.now(timezone.utc) - entry.last_sent < timedelta(hours=self.cooldown_hours):
            return True, f'Cooldown active for {key}'
        
        # Check max nudges
        if entry.nudge_count >= self.max_nudges:
            return True, f'Max nudges ({self.max_nudges}) reached for {key}'
        
        # Check duplicate message
        msg_hash = self._hash_message(body)
        if msg_hash == entry.message_hash:
            return True, f'Duplicate message for {key}'
        
        return False, ''
    
    def record_send(self, merchant_id: str, trigger_id: str, opportunity_type: str, body: str, expires_at: Optional[datetime] = None):
        key = self._make_key(merchant_id, trigger_id, opportunity_type)
        msg_hash = self._hash_message(body)
        
        entry = self._store.get(key)
        if entry:
            entry.last_sent = datetime.now(timezone.utc)
            entry.message_hash = msg_hash
            entry.nudge_count += 1
            if expires_at:
                entry.expires_at = expires_at
        else:
            self._store[key] = SuppressionEntry(
                key=key,
                merchant_id=merchant_id,
                trigger_id=trigger_id,
                opportunity_type=opportunity_type,
                message_hash=msg_hash,
                last_sent=datetime.now(timezone.utc),
                nudge_count=1,
                expires_at=expires_at
            )
    
    def record_response(self, merchant_id: str, trigger_id: str, opportunity_type: str, response: str):
        key = self._make_key(merchant_id, trigger_id, opportunity_type)
        entry = self._store.get(key)
        if entry:
            entry.last_response = response
            # Reset nudge count on positive response
            if 'yes' in response.lower() or 'ok' in response.lower() or 'sure' in response.lower():
                entry.nudge_count = 0
    
    def is_auto_reply(self, merchant_id: str, trigger_id: str, opportunity_type: str, message: str) -> bool:
        key = self._make_key(merchant_id, trigger_id, opportunity_type)
        entry = self._store.get(key)
        if not entry:
            return False
        
        # Check if same message received multiple times
        auto_reply_patterns = [
            'thank you for contacting',
            'our team will respond',
            'auto reply',
            'automated response',
            'we will get back'
        ]
        msg_lower = message.lower()
        for pattern in auto_reply_patterns:
            if pattern in msg_lower:
                return True
        return False
    
    def get_state(self, merchant_id: str, trigger_id: str, opportunity_type: str) -> Optional[SuppressionEntry]:
        key = self._make_key(merchant_id, trigger_id, opportunity_type)
        return self._store.get(key)
