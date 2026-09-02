# tests/test_escalation.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute() / "core-engine"))
from harness_loop import detect_promise, detect_escalation, HarnessLoop
from loop_state import LoopState


def test_detect_promise_true():
    assert detect_promise("<promise>HARNESS_COMPLETE</promise>", "HARNESS_COMPLETE")

def test_detect_promise_with_surrounding_text():
    output = "작업 완료.\n<promise>HARNESS_COMPLETE</promise>\n감사합니다."
    assert detect_promise(output, "HARNESS_COMPLETE")

def test_detect_promise_false():
    assert not detect_promise("아직 진행 중", "HARNESS_COMPLETE")

def test_detect_promise_wrong_value():
    assert not detect_promise("<promise>OTHER</promise>", "HARNESS_COMPLETE")

def test_detect_escalation_true():
    assert detect_escalation("## [ESCALATION] 에이전트 판단 요청")

def test_detect_escalation_case_insensitive():
    assert detect_escalation("[escalation] 소문자도 감지")

def test_detect_escalation_false():
    assert not detect_escalation("정상 진행 중")

def test_oscillation_detection(tmp_path):
    """주기-2 사이클 감지 테스트"""
    state = LoopState(cli="claude", prompt="test")
    state_file = tmp_path / "state.md"
    history = tmp_path / "HISTORY.md"
    history.write_text("")
    state.to_file(state_file)
    loop = HarnessLoop(state_file=state_file, history_file=history)

    out_a = "output A"
    out_b = "output B"
    assert not loop._detect_oscillation(out_a)  # 1
    assert not loop._detect_oscillation(out_b)  # 2
    assert not loop._detect_oscillation(out_a)  # 3
    assert loop._detect_oscillation(out_b)       # 4 → A,B,A,B 패턴
