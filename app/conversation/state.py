from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import sqlite3
import json
import uuid

class EngagementState(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    WAITING = "waiting"
    ENDED = "ended"
    SUPPRESSED = "suppressed"

class ConversationState(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    current_opportunity: Optional[str] = None
    last_message: Optional[str] = None
    message_history: List[Dict[str, Any]] = []
    intent: Optional[str] = None
    engagement_state: EngagementState = EngagementState.NEW
    nudge_count: int = 0
    last_action: Optional[str] = None
    language: str = "en"
    suppression_state: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ConversationRepository:
    def __init__(self, db_path: str = "vera.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                merchant_id TEXT NOT NULL,
                customer_id TEXT,
                current_opportunity TEXT,
                last_message TEXT,
                message_history TEXT,
                intent TEXT,
                engagement_state TEXT,
                nudge_count INTEGER DEFAULT 0,
                last_action TEXT,
                language TEXT DEFAULT 'en',
                suppression_state TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def save(self, state: ConversationState):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO conversations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state.conversation_id,
            state.merchant_id,
            state.customer_id,
            state.current_opportunity,
            state.last_message,
            json.dumps(state.message_history),
            state.intent,
            state.engagement_state.value,
            state.nudge_count,
            state.last_action,
            state.language,
            state.suppression_state,
            json.dumps(state.metadata),
            state.created_at.isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def get(self, conversation_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM conversations WHERE conversation_id = ?', (conversation_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return ConversationState(
            conversation_id=row[0],
            merchant_id=row[1],
            customer_id=row[2],
            current_opportunity=row[3],
            last_message=row[4],
            message_history=json.loads(row[5]) if row[5] else [],
            intent=row[6],
            engagement_state=EngagementState(row[7]),
            nudge_count=row[8],
            last_action=row[9],
            language=row[10],
            suppression_state=row[11],
            metadata=json.loads(row[12]) if row[12] else {},
            created_at=datetime.fromisoformat(row[13]),
            updated_at=datetime.fromisoformat(row[14])
        )
    
    def get_by_merchant(self, merchant_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM conversations WHERE merchant_id = ? ORDER BY updated_at DESC', (merchant_id,))
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append(ConversationState(
                conversation_id=row[0],
                merchant_id=row[1],
                customer_id=row[2],
                current_opportunity=row[3],
                last_message=row[4],
                message_history=json.loads(row[5]) if row[5] else [],
                intent=row[6],
                engagement_state=EngagementState(row[7]),
                nudge_count=row[8],
                last_action=row[9],
                language=row[10],
                suppression_state=row[11],
                metadata=json.loads(row[12]) if row[12] else {},
                created_at=datetime.fromisoformat(row[13]),
                updated_at=datetime.fromisoformat(row[14])
            ))
        return result

class StateManager:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository
    
    def create_conversation(self, merchant_id: str, customer_id: Optional[str] = None, opportunity: Optional[str] = None, conversation_id: Optional[str] = None):
        state = ConversationState(
            conversation_id=conversation_id or str(uuid.uuid4()),
            merchant_id=merchant_id,
            customer_id=customer_id,
            current_opportunity=opportunity
        )
        self.repository.save(state)
        return state
    
    def update_state(self, conversation_id: str, **kwargs):
        state = self.repository.get(conversation_id)
        if not state:
            return None
        
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        
        state.updated_at = datetime.now()
        self.repository.save(state)
        return state
    
    def add_message(self, conversation_id: str, from_role: str, body: str, intent: Optional[str] = None):
        state = self.repository.get(conversation_id)
        if not state:
            return
        
        state.message_history.append({
            'timestamp': datetime.now().isoformat(),
            'from': from_role,
            'body': body,
            'intent': intent
        })
        state.last_message = body
        if intent:
            state.intent = intent
        state.updated_at = datetime.now()
        self.repository.save(state)
    
    def get_state(self, conversation_id: str):
        return self.repository.get(conversation_id)
    
    def end_conversation(self, conversation_id: str, reason: str = ""):
        self.update_state(conversation_id, engagement_state=EngagementState.ENDED, last_action=reason)