"""Directed connectivity test for the internal memory transaction interface."""

import cocotb
from cocotb.triggers import Timer

REQUEST_DATA = 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3210
RESPONSE_DATA = 0xF0E1_D2C3_B4A5_9687_7869_5A4B_3C2D_1E0F
REQUEST_ADDRESS = 0x1234_5670
REQUEST_SIZE = 4
REQUEST_STROBE = 0xA55A


@cocotb.test()
async def request_response_payloads_and_backpressure_cross_modports(dut) -> None:
    """Check every request and response field in both ready-valid directions."""
    dut.initiator_req_valid_i.value = 1
    dut.initiator_req_write_i.value = 1
    dut.initiator_req_addr_i.value = REQUEST_ADDRESS
    dut.initiator_req_size_i.value = REQUEST_SIZE
    dut.initiator_req_wdata_i.value = REQUEST_DATA
    dut.initiator_req_wstrb_i.value = REQUEST_STROBE
    dut.initiator_rsp_ready_i.value = 0

    dut.target_req_ready_i.value = 0
    dut.target_rsp_valid_i.value = 1
    dut.target_rsp_rdata_i.value = RESPONSE_DATA
    dut.target_rsp_error_i.value = 1
    await Timer(1, unit="ns")

    assert int(dut.target_req_valid_o.value) == 1
    assert int(dut.target_req_write_o.value) == 1
    assert int(dut.target_req_addr_o.value) == REQUEST_ADDRESS
    assert int(dut.target_req_size_o.value) == REQUEST_SIZE
    assert int(dut.target_req_wdata_o.value) == REQUEST_DATA
    assert int(dut.target_req_wstrb_o.value) == REQUEST_STROBE
    assert int(dut.initiator_req_ready_o.value) == 0

    assert int(dut.initiator_rsp_valid_o.value) == 1
    assert int(dut.initiator_rsp_rdata_o.value) == RESPONSE_DATA
    assert int(dut.initiator_rsp_error_o.value) == 1
    assert int(dut.target_rsp_ready_o.value) == 0

    dut.target_req_ready_i.value = 1
    dut.initiator_rsp_ready_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.initiator_req_ready_o.value) == 1
    assert int(dut.target_rsp_ready_o.value) == 1

    dut.initiator_req_valid_i.value = 0
    dut.target_rsp_valid_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.target_req_valid_o.value) == 0
    assert int(dut.initiator_rsp_valid_o.value) == 0
