import pytest

from app.integrations.ER302_Reader import ER302_Reader


def test_process_blocks_length_limit_mapped():
    reader = ER302_Reader(port='/dev/null', baud=9600)

    # Simulate card operations and data reads
    reader.select_card = lambda uid: True
    reader.auth_block = lambda block, key_type=0, key=None: True
    reader.read_block = lambda block: [i % 256 for i in range(16)]

    uids = [0xDE, 0xAD, 0xBE, 0xEF]
    payload = {'block': 0, 'length': 32, 'key': 'FFFFFFFFFFFF'}

    result = reader.processBlocks(uids, payload)
    assert result['status'] is True
    assert result['readerstatus'] == 'CARD_VALID'

    # 32 bytes should be 64 hex chars
    assert isinstance(result['memData'], str)
    assert len(result['memData']) == 64


def test_write_memory_process_reject_trailer_block():
    reader = ER302_Reader(port='/dev/null', baud=9600)
    reader.select_card = lambda uid: True
    reader.write_block = lambda block, data, key_type, key: True

    payload = {'block': 3, 'key': 'FFFFFFFFFFFF', 'data': 'AA' * 16}

    output = reader.write_memory_process([0xDE, 0xAD, 0xBE, 0xEF], payload)
    assert output['status'] is False
    assert output['readerstatus'] == 'BAD_REQUEST'
    assert 'Cannot write trailer block' in output['message']
