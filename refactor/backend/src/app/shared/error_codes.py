from enum import Enum


class ErrorCode(str, Enum):
    """Global error code contract for the refactor backend."""

    IGW_SESSION_001 = "IGW-SESSION-001"
    IGW_REQUEST_002 = "IGW-REQUEST-002"
    WFE_VALIDATE_001 = "WFE-VALIDATE-001"
    MEM_STORE_003 = "MEM-STORE-003"
    BT_COMPAT_003 = "BT-COMPAT-003"
