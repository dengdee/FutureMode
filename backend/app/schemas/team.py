from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class TeamUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class InvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    role: str = Field(default="member", pattern="^(admin|member)$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

class InvitationSummary(BaseModel):
    id: UUID
    team_id: UUID
    email: str
    role: str
    status: str


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|member)$")


class TeamSummary(BaseModel):
    id: UUID
    name: str
    role: str

