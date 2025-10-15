from typing import Optional
from pydantic import BaseModel, ConfigDict

class ApiChatInput(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None
    kind: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    def content(self) -> str:
        return (self.text or self.message or "").strip()

# Keep ChatIn for backward compatibility
ChatIn = ApiChatInput
