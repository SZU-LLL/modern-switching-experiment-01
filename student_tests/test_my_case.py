"""自拟反例：验证部分发送的记录不能误记为完成。

构造一个200bit记录、128bit容量的场景，
第一个tick只能发128bit，记录剩余72bit，不能算完成。
"""
from collections import deque
from src.models import Config, Pending
from src.part1_circuit import serve_circuit
from src.part2_packet import serve_packet


def test_partial_send_not_completed_circuit():
    """电路交换：200bit记录在128bit容量下，第一个tick只发128，不完成。"""
    cfg = Config(users=2, ticks=10, slot_bits=128)
    p = Pending(user=0, arrival_tick=0, payload_bits=200, remaining_wire_bits=200)
    queues = [deque([p]), deque()]
    sent, completed = serve_circuit(queues, tick=0, cfg=cfg)
    assert sent == 128
    assert len(completed) == 0
    assert p.remaining_wire_bits == 72
    assert len(queues[0]) == 1  # 还在队列里


def test_partial_send_not_completed_packet():
    """分组交换：96bit payload + 32bit头 = 128bit wire，一个tick刚好发完。"""
    cfg = Config(users=2, ticks=10, slot_bits=128)
    p = Pending(user=0, arrival_tick=0, payload_bits=96, remaining_wire_bits=128)
    q = deque([p])
    sent, completed = serve_packet(q, tick=0, cfg=cfg)
    assert sent == 128
    assert len(completed) == 1
    assert len(q) == 0


def test_circuit_does_not_steal_slots():
    """电路交换：当前用户空闲时，其他用户不能借用其时隙。"""
    cfg = Config(users=2, ticks=10, slot_bits=128)
    other = Pending(user=1, arrival_tick=0, payload_bits=100, remaining_wire_bits=100)
    queues = [deque(), deque([other])]
    sent, completed = serve_circuit(queues, tick=0, cfg=cfg)  # tick=0服务user0
    assert sent == 0
    assert len(completed) == 0
    assert len(queues[1]) == 1  # user1的记录还在等待
