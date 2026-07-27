import sys, os

def check_alignment():
    # 간단한 정렬(Alignment) 체크 로직:
    # 실행 중인 계획 파일(active/*.md)이 있는지 확인하고, reviewed: true 인지 확인
    import glob
    active_plans = glob.glob(".agentos/project/exec-plans/active/*.md")
    if not active_plans:
        # 진행 중인 계획이 없는데 구현을 시도하는 경우 (사용자 의도 확인 필요)
        # 훅에서 강제로 막을지 여부 판단 (여기서는 경고 메시지만 출력)
        print("AgentOS Unified Hook [Alignment]: No active plan found. Did you confirm the design with the user?", file=sys.stderr)
        return 0

    for plan in active_plans:
        with open(plan, 'r', encoding='utf-8') as f:
            content = f.read()
            if "reviewed: true" in content.lower():
                return 0
                
    # 계획은 있지만 리뷰되지 않은 경우
    print("AgentOS Unified Hook [Alignment]: Active plan is NOT reviewed. Rule 6 violation. Please ask user to review the plan.", file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(check_alignment())
