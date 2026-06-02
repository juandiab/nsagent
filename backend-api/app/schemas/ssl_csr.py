from typing import Literal

from pydantic import BaseModel, Field


CertType = Literal["standard", "wildcard", "san"]
KeyType = Literal["rsa", "ecdsa"]
GenerationMode = Literal["csr", "self_signed"]


class GenerateSslRequest(BaseModel):
    appliance_id: str
    generation_mode: GenerationMode = "csr"
    key_name: str = Field(..., min_length=1, max_length=64)
    cert_type: CertType
    key_type: KeyType = "rsa"
    key_size: int = Field(default=2048, ge=2048, le=4096)
    key_password: str | None = None
    common_name: str = Field(..., min_length=1, max_length=128)
    country: str = Field(default="US", min_length=2, max_length=2)
    state: str = Field(default="", max_length=128)
    locality: str = Field(default="", max_length=128)
    organization: str = Field(default="", max_length=128)
    organizational_unit: str = Field(default="", max_length=128)
    email: str | None = Field(default=None, max_length=128)
    subject_alt_names: list[str] = Field(default_factory=list)
    validity_days: int = Field(default=365, ge=1, le=3650)


class GenerateSslResponse(BaseModel):
    success: bool
    message: str = ""
    generation_mode: str = "csr"
    csr: str = ""
    certificate: str = ""
    key_path: str = ""
    csr_path: str = ""
    cert_path: str = ""
    req_path: str = ""
    cert_key_name: str = ""
    key_name: str = ""
    common_name: str = ""
    cert_type: str = ""
    key_type: str = ""
    validity_days: int | None = None


# Backward-compatible aliases
GenerateCsrRequest = GenerateSslRequest
GenerateCsrResponse = GenerateSslResponse
