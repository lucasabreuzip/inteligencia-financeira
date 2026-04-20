from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    job_id: str = Field(min_length=1)
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=15, ge=1, le=50)
    # session_id e gerado pelo cliente (UUID em localStorage). O backend carrega
    # historico do Postgres por (job_id, session_id); cliente nao envia history.
    session_id: str = Field(min_length=1, max_length=64)


class ChatHistoryResponse(BaseModel):
    job_id: str
    session_id: str
    messages: list[ChatMessage]


class ChatSource(BaseModel):
    id: str
    valor: float
    data: str
    status: str
    cliente: str
    descricao: str
    score: float | None = None


class ToolCallLog(BaseModel):
    name: str
    args: dict = Field(default_factory=dict)
    ok: bool = True
    summary: str | None = None


class GroundingInfo(BaseModel):
    cited: list[str] = Field(default_factory=list)
    verified: list[str] = Field(default_factory=list)
    unverified: list[str] = Field(default_factory=list)
    is_grounded: bool = True


class ChatResponse(BaseModel):
    job_id: str
    question: str
    answer: str
    sources: list[ChatSource]
    tools_used: list[ToolCallLog] = Field(default_factory=list)
    grounding: GroundingInfo = Field(default_factory=GroundingInfo)
