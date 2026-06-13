from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class ProspectInput:
    prospect_name: str
    company_name: str
    prospect_role: str
    tone: str
    company_website: Optional[str] = None
    linkedin_summary: Optional[str] = None
    additional_notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_valid(self) -> bool:
        return all([
            self.prospect_name.strip(),
            self.company_name.strip(),
            self.prospect_role.strip(),
            self.tone in ["friendly", "formal", "direct", "consultative", "executive"]
        ])


@dataclass
class GeneratedEmail:
    subject_line: str
    email_body: str
    call_to_action: str
    word_count: int = 0
    generation_time_ms: int = 0
    model_used: str = "llama3-8b-8192"
    prospect_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.word_count = len(self.email_body.split())


@dataclass
class ResearchData:
    company_name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    value_proposition: Optional[str] = None
    recent_news: Optional[str] = None
    raw_text: Optional[str] = None
    research_successful: bool = False
    error_message: Optional[str] = None
from typing import Optional
from datetime import datetime
import uuid


