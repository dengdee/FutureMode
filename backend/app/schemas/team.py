from uuid import UUID

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(owner|admin|member)$")


class TeamSummary(BaseModel):
    id: UUID
    name: str
    role: str

