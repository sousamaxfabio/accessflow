from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GitHubMember(BaseModel):
    model_config = ConfigDict(extra="ignore")

    login: str = Field(min_length=1)
    id: int = Field(gt=0)
    avatar_url: HttpUrl
    html_url: HttpUrl


class GitHubMembersResult(BaseModel):
    organization: str = Field(min_length=1)
    members: list[GitHubMember]
    pages_fetched: int = Field(ge=1)
    truncated: bool = False
