"""Corporate identity boundary. Local Django passwords are only for loopback demos."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class IdentityClaims:
    subject: str
    issuer: str
    email: str
    display_name: str

class CorporateIdentityAdapter(Protocol):
    def verify_token(self, token: str) -> IdentityClaims: ...
    def provision_memberships(self, claims: IdentityClaims) -> None: ...

class UnconfiguredCorporateOIDC:
    def verify_token(self, token: str) -> IdentityClaims:
        raise RuntimeError('Corporate OIDC issuer, client, claim mapping and trust configuration are not approved.')
    def provision_memberships(self, claims: IdentityClaims) -> None:
        raise RuntimeError('Corporate role provisioning and site membership rules are not approved.')
