from pydantic import BaseModel, Field


class TlsCertificatePayload(BaseModel):
    certificate: str
    private_key: str
    chain: str = ""


class TlsCertificateInspection(BaseModel):
    ok: bool
    common_name: str = ""
    subject_alt_names: list[str] = Field(default_factory=list)
    expires: str = ""
    expires_in_days: int = 0
    hostname: str = ""
    hostname_matches: bool = False
    error: str = ""


class TlsCertificateStatus(BaseModel):
    available: bool
    hostname: str
    has_certificate: bool
    common_name: str = ""
    subject_alt_names: list[str] = Field(default_factory=list)
    expires: str = ""
    expires_in_days: int | None = None
    message: str = ""


class TlsCertificateApplyResult(BaseModel):
    ok: bool
    common_name: str = ""
    expires: str = ""
    expires_in_days: int = 0
    hostname: str = ""
    nginx_reloaded: bool = False
    message: str = ""
    error: str = ""
