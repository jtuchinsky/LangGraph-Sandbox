import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel


class DialogueMessage(BaseModel):
    """Сообщение в диалоге"""
    timestamp: datetime
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None


class DialogueSession(BaseModel):
    """Сессия диалога"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[DialogueMessage] = []
    context_summary: Optional[str] = None
    user_preferences: Dict[str, Any] = {}
    session_metadata: Dict[str, Any] = {}


class ContextMemory:
    """Система запоминания контекста диалога"""
    
    def __init__(self, storage_path: str = "memory_storage", max_sessions: int = 100):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.max_sessions = max_sessions
        self.sessions: Dict[str, DialogueSession] = {}
        self.load_sessions()
    
    def create_session(self, session_id: str, user_preferences: Dict[str, Any] = None) -> DialogueSession:
        """Создать новую сессию диалога"""
        now = datetime.now()
        session = DialogueSession(
            session_id=session_id,
            created_at=now,
            last_activity=now,
            user_preferences=user_preferences or {}
        )
        
        self.sessions[session_id] = session
        self.save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[DialogueSession]:
        """Получить сессию по ID"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try to load from storage
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                session = DialogueSession(**data)
                self.sessions[session_id] = session
                return session
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
        
        return None
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Добавить сообщение в сессию"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        message = DialogueMessage(
            timestamp=datetime.now(),
            role=role,
            content=content,
            metadata=metadata
        )
        
        session.messages.append(message)
        session.last_activity = datetime.now()
        
        # Update context summary periodically
        if len(session.messages) % 10 == 0:
            self.update_context_summary(session)
        
        self.save_session(session)
        return True
    
    def get_recent_messages(self, session_id: str, limit: int = 20) -> List[DialogueMessage]:
        """Получить последние сообщения из сессии"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.messages[-limit:]
    
    def get_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Получить контекст разговора в виде строки"""
        session = self.get_session(session_id)
        if not session:
            return "No conversation history found."
        
        context_parts = []
        
        # Add context summary if available
        if session.context_summary:
            context_parts.append(f"Previous conversation summary: {session.context_summary}")
        
        # Add recent messages
        recent_messages = self.get_recent_messages(session_id, max_messages)
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                timestamp = msg.timestamp.strftime("%H:%M")
                context_parts.append(f"[{timestamp}] {msg.role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def update_context_summary(self, session: DialogueSession):
        """Обновить краткое содержание контекста (можно использовать LLM)"""
        if not session.messages:
            return
        
        # Simple summarization - in production, use LLM
        recent_content = []
        for msg in session.messages[-20:]:  # Last 20 messages
            recent_content.append(f"{msg.role}: {msg.content[:100]}")
        
        session.context_summary = f"Recent topics discussed: {'; '.join(recent_content[:5])}"
    
    def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """Обновить предпочтения пользователя"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        session.user_preferences.update(preferences)
        self.save_session(session)
    
    def get_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """Получить предпочтения пользователя"""
        session = self.get_session(session_id)
        return session.user_preferences if session else {}
    
    def search_messages(self, session_id: str, query: str, limit: int = 10) -> List[DialogueMessage]:
        """Поиск сообщений по содержимому"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        query_lower = query.lower()
        matching_messages = []
        
        for msg in session.messages:
            if query_lower in msg.content.lower():
                matching_messages.append(msg)
                if len(matching_messages) >= limit:
                    break
        
        return matching_messages
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Получить статистику сессии"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        stats = {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "total_messages": len(session.messages),
            "duration": str(session.last_activity - session.created_at)
        }
        
        # Count messages by role
        role_counts = {}
        for msg in session.messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1
        stats["message_counts"] = role_counts
        
        return stats
    
    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Очистить старые сессии"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session.last_activity < cutoff_date:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.remove_session(session_id)
        
        print(f"Cleaned up {len(sessions_to_remove)} old sessions")
    
    def remove_session(self, session_id: str):
        """Удалить сессию"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    def save_session(self, session: DialogueSession):
        """Сохранить сессию в файл"""
        try:
            session_file = self.storage_path / f"{session.session_id}.json"
            
            # Convert to dict with proper datetime serialization
            session_data = session.model_dump()
            session_data['created_at'] = session.created_at.isoformat()
            session_data['last_activity'] = session.last_activity.isoformat()
            
            for message in session_data['messages']:
                message['timestamp'] = datetime.fromisoformat(message['timestamp']).isoformat() if isinstance(message['timestamp'], str) else message['timestamp'].isoformat()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
    
    def load_sessions(self):
        """Загрузить все сессии из файлов"""
        try:
            for session_file in self.storage_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert datetime strings back to datetime objects
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['last_activity'] = datetime.fromisoformat(data['last_activity'])
                    
                    for message in data['messages']:
                        message['timestamp'] = datetime.fromisoformat(message['timestamp'])
                    
                    session = DialogueSession(**data)
                    self.sessions[session.session_id] = session
                    
                except Exception as e:
                    print(f"Error loading session from {session_file}: {e}")
                    
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Экспортировать сессию"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        if format == "json":
            session_data = session.model_dump()
            session_data['created_at'] = session.created_at.isoformat()
            session_data['last_activity'] = session.last_activity.isoformat()
            
            for message in session_data['messages']:
                if isinstance(message['timestamp'], datetime):
                    message['timestamp'] = message['timestamp'].isoformat()
            
            return json.dumps(session_data, ensure_ascii=False, indent=2)
        
        elif format == "text":
            lines = [
                f"Session: {session.session_id}",
                f"Created: {session.created_at}",
                f"Last Activity: {session.last_activity}",
                f"Total Messages: {len(session.messages)}",
                "",
                "Messages:"
            ]
            
            for msg in session.messages:
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{timestamp}] {msg.role}: {msg.content}")
            
            return "\n".join(lines)
        
        return None