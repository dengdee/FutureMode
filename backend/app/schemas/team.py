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
    email: str = Field(min_length=3, max_length=320)
    role: str = Field(default="member", pattern="^(admin|member)$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

class InvitationSummary(BaseModel):
    id: UUID
    team_id: UUID
    email: str | None = None
    recipient_user_id: UUID | None = None
    recipient_name: str | None = None
    role: str
    status: str


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|member)$")


class TeamSummary(BaseModel):
    id: UUID
    name: str
    role: str

