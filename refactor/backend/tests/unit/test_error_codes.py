from app.shared.error_codes import ErrorCode


def test_error_code_contract() -> None:
    assert ErrorCode.IGW_SESSION_001.value == "IGW-SESSION-001"
    assert ErrorCode.IGW_REQUEST_002.value == "IGW-REQUEST-002"
    assert ErrorCode.WFE_VALIDATE_001.value == "WFE-VALIDATE-001"
    assert ErrorCode.MEM_STORE_003.value == "MEM-STORE-003"
    assert ErrorCode.BT_COMPAT_003.value == "BT-COMPAT-003"
    assert ErrorCode.NTF_CHANNEL_001.value == "NTF-CHANNEL-001"
    assert ErrorCode.NTF_FORMAT_002.value == "NTF-FORMAT-002"
    assert ErrorCode.NTF_SEND_003.value == "NTF-SEND-003"
    assert ErrorCode.NTF_RETRY_004.value == "NTF-RETRY-004"
