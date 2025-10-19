#!/usr/bin/env python3
"""
Claude Transcript Analyzer
Extracts todos, thinking, and work summary from Claude Code transcripts
"""
import json
import sys
import os
import hashlib

if len(sys.argv) < 2:
    print("ERROR: No transcript path provided", file=sys.stderr)
    sys.exit(1)

transcript_path = sys.argv[1]
# 세션별 보고 이력 파일
session_id = os.path.basename(transcript_path).replace('.jsonl', '')
reported_file = f"/tmp/.claude-reported-{session_id}"

try:
    with open(transcript_path, 'r') as f:
        lines = f.readlines()

    # 이전에 보고한 내용 로드
    reported_items = set()
    if os.path.exists(reported_file):
        with open(reported_file, 'r') as f:
            reported_items = set(line.strip() for line in f.readlines())

    todos_list = []
    thinkings = []
    user_requests = []
    plans = []
    files_modified = []
    bash_commands = []

    # 최근 메시지 분석 (마지막 100개 - 충분한 컨텍스트)
    for line in lines[-100:]:
        try:
            msg = json.loads(line)

            # message 필드 확인
            if 'message' not in msg:
                continue

            message = msg['message']
            role = message.get('role', '')

            # 사용자 요청 추출 (user role)
            if role == 'user':
                content = message.get('content', '')
                if isinstance(content, str) and len(content) > 20:
                    # 의미있는 요청만
                    if content not in user_requests and not content.lower() in ['ok', 'yes', '네', '확인']:
                        user_requests.append(content[:100])

            # assistant의 content 확인
            if 'content' in message:
                content = message['content']
            else:
                continue

            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue

                block_type = block.get('type', '')

                # ExitPlanMode 추출 (Plan 모드)
                if block_type == 'tool_use' and block.get('name') == 'ExitPlanMode':
                    input_data = block.get('input', {})
                    plan_text = input_data.get('plan', '')
                    if plan_text and plan_text not in plans:
                        plans.append(plan_text)

                # TodoWrite 추출
                elif block_type == 'tool_use' and block.get('name') == 'TodoWrite':
                    input_data = block.get('input', {})
                    todos = input_data.get('todos', [])
                    for todo in todos:
                        content_text = todo.get('content', '')
                        status = todo.get('status', 'pending')
                        if content_text and content_text not in [t['content'] for t in todos_list]:
                            todos_list.append({'content': content_text, 'status': status})

                # 파일 수정 추출 (Edit/Write)
                elif block_type == 'tool_use' and block.get('name') in ['Edit', 'Write']:
                    input_data = block.get('input', {})
                    file_path = input_data.get('file_path', '')
                    if file_path and file_path not in files_modified:
                        files_modified.append(file_path)

                # Bash 명령 추출
                elif block_type == 'tool_use' and block.get('name') == 'Bash':
                    input_data = block.get('input', {})
                    command = input_data.get('command', '')
                    desc = input_data.get('description', '')
                    if command and len(command) < 200:
                        bash_commands.append({'cmd': command, 'desc': desc})

                # Thinking 추출 (의미있는 것만)
                elif block_type == 'thinking':
                    thinking_text = block.get('thinking', '').strip()
                    if len(thinking_text) > 50 and thinking_text not in thinkings:
                        thinkings.append(thinking_text[:200])

        except:
            continue

    # 신규 항목만 필터링
    new_todos = []
    new_requests = []
    new_plans = []

    for todo in todos_list:
        todo_hash = hashlib.md5(todo['content'].encode()).hexdigest()
        if todo_hash not in reported_items:
            new_todos.append(todo)
            reported_items.add(todo_hash)

    for req in user_requests:
        req_hash = hashlib.md5(req.encode()).hexdigest()
        if req_hash not in reported_items:
            new_requests.append(req)
            reported_items.add(req_hash)

    for plan in plans:
        plan_hash = hashlib.md5(plan.encode()).hexdigest()
        if plan_hash not in reported_items:
            new_plans.append(plan)
            reported_items.add(plan_hash)

    # 보고 이력 저장
    with open(reported_file, 'w') as f:
        f.write('\n'.join(reported_items))

    # 실제 작업 내용 기반 요약 생성
    command_summary = ""

    # 1순위: completed todos에서 요약 생성
    completed_todos = [t for t in new_todos if t.get('status') == 'completed']
    if completed_todos:
        if len(completed_todos) == 1:
            # 단일 작업: 작업 내용 그대로 사용
            command_summary = completed_todos[0]['content'][:50]
        else:
            # 다중 작업: 개수 + 주요 작업
            main_task = completed_todos[0]['content'][:30]
            command_summary = f"{len(completed_todos)}개 작업 완료: {main_task}..."

    # 2순위: 파일 수정 기반 요약
    elif files_modified:
        file_count = len(files_modified)
        if file_count == 1:
            file_name = os.path.basename(files_modified[0])
            command_summary = f"{file_name} 수정"
        elif file_count <= 3:
            file_names = [os.path.basename(f) for f in files_modified]
            command_summary = f"{', '.join(file_names)} 수정"
        else:
            command_summary = f"{file_count}개 파일 수정"

    # 3순위: bash 명령 기반 요약
    elif bash_commands:
        # git 명령 우선
        git_cmds = [c for c in bash_commands if 'git' in c['cmd']]
        if git_cmds:
            if 'commit' in git_cmds[-1]['cmd']:
                command_summary = "Git 커밋"
            elif 'push' in git_cmds[-1]['cmd']:
                command_summary = "Git 푸시"
            else:
                command_summary = "Git 작업"
        # 테스트 명령
        elif any('test' in c['cmd'] or 'pytest' in c['cmd'] for c in bash_commands):
            command_summary = "테스트 실행"
        # 빌드 명령
        elif any('build' in c['cmd'] or 'npm' in c['cmd'] for c in bash_commands):
            command_summary = "빌드 실행"
        else:
            # 마지막 명령의 description 사용
            last_desc = bash_commands[-1].get('desc', '')
            if last_desc and len(last_desc) < 50:
                command_summary = last_desc
            else:
                command_summary = f"{len(bash_commands)}개 명령 실행"

    # 4순위: 사용자 요청 키워드 기반
    elif new_requests:
        req = new_requests[-1]
        req_lower = req.lower()

        # 키워드 매칭으로 작업 유형 추론
        if 'gitlab' in req_lower and ('푸시' in req or 'push' in req_lower):
            command_summary = "GitLab 자동 푸시"
        elif 'gitlab' in req_lower and ('저장소' in req or 'repository' in req_lower):
            command_summary = "GitLab 저장소 설정"
        elif 'hook' in req_lower and '설치' in req:
            command_summary = "Hook 시스템 설치"
        elif '분석' in req and ('코드' in req or '프로젝트' in req):
            command_summary = "프로젝트 분석"
        elif '수정' in req or 'fix' in req_lower:
            command_summary = "버그 수정"
        elif '추가' in req or 'add' in req_lower:
            command_summary = "기능 추가"
        elif '개선' in req or 'improve' in req_lower:
            command_summary = "기능 개선"
        else:
            # 사용자 요청 첫 50자 사용
            command_summary = req[:50]

    # 5순위: 기본값
    else:
        command_summary = "작업 완료"

    # 파일 작업을 투두 리스트로 변환
    work_todos = []

    if new_requests:
        req = new_requests[-1]
        req_lower = req.lower()

        # 문장 정리 (감탄사, 불필요한 기호 제거)
        req_clean = req.replace('!', '').replace('?', '').strip()

        # 키워드 기반 이해한 내용으로 정리
        if 'hook' in req_lower and ('안걸' in req or '작동' in req or '안돼' in req):
            work_todos.append("팀원 환경에서 Hook 작동 문제 진단 및 해결")
        elif 'gitlab' in req_lower:
            if '푸시' in req or 'push' in req_lower:
                work_todos.append("GitLab 저장소 생성 및 코드 푸시 작업")
            elif '생성' in req or 'create' in req_lower:
                work_todos.append("GitLab 저장소 생성")
        elif '웹사이트' in req and ('분석' in req or 'analyze' in req_lower):
            work_todos.append("웹사이트 성능 및 보안 종합 분석 수행")
        elif '분석' in req or 'analyze' in req_lower:
            if '프로젝트' in req or 'project' in req_lower:
                work_todos.append("프로젝트 구조 및 설정 분석")
            elif '환경' in req:
                work_todos.append("실행 환경 호환성 분석")
            else:
                work_todos.append("코드베이스 검토 및 분석")
        elif '검토' in req or 'review' in req_lower or '확인' in req:
            if '설치' in req:
                work_todos.append("설치 프로세스 검토 및 개선")
            elif '버전' in req:
                work_todos.append("버전 호환성 검토")
            else:
                work_todos.append("코드 품질 검토 및 개선사항 도출")
        elif '한글' in req and ('깨' in req or 'encoding' in req_lower):
            work_todos.append("한글 인코딩 문제 해결 및 크로스 플랫폼 지원")
        elif 'readme' in req_lower or '문서' in req:
            if '작성' in req or 'write' in req_lower:
                work_todos.append("팀원용 설치 가이드 문서 작성")
            else:
                work_todos.append("문서 개선 및 업데이트")
        elif 'claude' in req_lower and ('설치' in req or 'install' in req_lower):
            work_todos.append("Claude Hooks Slack 통합 시스템 설치 및 설정")
        elif '설치' in req or 'install' in req_lower:
            work_todos.append("필요 패키지 설치 및 개발 환경 구성")
        elif '업데이트' in req or 'update' in req_lower:
            work_todos.append("최신 버전으로 업데이트 적용")
        elif ('수정' in req or 'fix' in req_lower or '고쳐' in req) and '중복' in req:
            work_todos.append("중복 메시지 전송 문제 해결")
        elif '수정' in req or 'fix' in req_lower or '고쳐' in req:
            work_todos.append("코드 오류 수정 및 기능 개선")
        elif '테스트' in req or 'test' in req_lower:
            work_todos.append("기능 테스트 및 동작 검증")
        elif '배포' in req or 'deploy' in req_lower:
            work_todos.append("프로덕션 환경 배포 준비")
        elif ('모든' in req or 'all' in req_lower) and '환경' in req:
            work_todos.append("크로스 플랫폼 호환성 확보 작업")
        elif '중복' in req:
            work_todos.append("중복 보고 방지 로직 구현")

    # 사용자 명령 요약 출력 (최우선)
    if command_summary:
        print("COMMAND_SUMMARY_START")
        print(command_summary)
        print("COMMAND_SUMMARY_END")

    # 출력 - 신규 항목만
    if new_todos:
        # 모든 상태의 todos 표시 (최대 10개)
        print("TODOS_START")
        for todo in new_todos[-10:]:
            icon = "✅" if todo['status'] == 'completed' else "🔄" if todo['status'] == 'in_progress' else "⏳"
            print(f"{icon} {todo['content']}")
        print("TODOS_END")
    elif work_todos:
        print("TODOS_START")
        for idx, work in enumerate(work_todos, 1):
            print(f"{idx}. ✅ {work}")
        print("TODOS_END")
    elif files_modified:
        # todos가 없으면 파일 수정 내역 표시
        print("TODOS_START")
        for idx, file_path in enumerate(files_modified[:10], 1):
            file_name = os.path.basename(file_path)
            print(f"{idx}. 📝 {file_name}")
        if len(files_modified) > 10:
            print(f"...외 {len(files_modified) - 10}개")
        print("TODOS_END")

    if thinkings:
        # Thinking 정리 (중간 과정 제거, 결과만)
        t = thinkings[-1]

        # 불필요한 문구 제거
        clean_thinking = t
        remove_phrases = [
            '좋습니다.', '완벽합니다.', '이제', '그리고', '하지만',
            '사용자가', '제가', '해야 합니다', '하겠습니다',
            '...', '!'
        ]
        for phrase in remove_phrases:
            clean_thinking = clean_thinking.replace(phrase, '')

        # 핵심만 추출 (첫 문장만)
        clean_thinking = clean_thinking.strip().split('.')[0].strip()

        # 최소 길이 확인
        if len(clean_thinking) > 20:
            print("THINKING_START")
            print(f"• {clean_thinking}")
            print("THINKING_END")

    # Plan 출력 (새로운 계획만)
    if new_plans:
        print("PLAN_START")
        # 최신 계획만 출력 (보통 하나만 있음)
        plan = new_plans[-1]
        # Plan은 이미 잘 정리된 마크다운이므로 그대로 출력
        print(plan[:500])  # 최대 500자로 제한
        print("PLAN_END")

except Exception as e:
    print(f"ERROR:{str(e)}", file=sys.stderr)
    sys.exit(1)
