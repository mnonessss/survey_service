import uuid

from pydantic import BaseModel

from app.models.enums import UserRole


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    role: UserRole
