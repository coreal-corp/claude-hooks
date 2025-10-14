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
    tools_count = {}
    files_modified = set()
    files_analyzed = set()
    user_requests = []

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

                # TodoWrite 추출
                if block_type == 'tool_use' and block.get('name') == 'TodoWrite':
                    input_data = block.get('input', {})
                    todos = input_data.get('todos', [])
                    for todo in todos:
                        content_text = todo.get('content', '')
                        status = todo.get('status', 'pending')
                        if content_text and content_text not in [t['content'] for t in todos_list]:
                            todos_list.append({'content': content_text, 'status': status})

                # Thinking 추출 (의미있는 것만)
                elif block_type == 'thinking':
                    thinking_text = block.get('thinking', '').strip()
                    if len(thinking_text) > 50 and thinking_text not in thinkings:
                        thinkings.append(thinking_text[:200])

                # Tool 사용 추적
                elif block_type == 'tool_use':
                    tool_name = block.get('name', '')
                    if tool_name:
                        tools_count[tool_name] = tools_count.get(tool_name, 0) + 1

                    input_data = block.get('input', {})

                    if tool_name in ['Edit', 'Write']:
                        file_path = input_data.get('file_path', '')
                        if file_path:
                            files_modified.add(file_path.split('/')[-1])

                    elif tool_name in ['Read', 'Grep']:
                        file_path = input_data.get('file_path') or input_data.get('path', '')
                        if file_path:
                            files_analyzed.add(file_path.split('/')[-1])

        except:
            continue

    # 신규 항목만 필터링
    new_todos = []
    new_requests = []

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

    # 보고 이력 저장
    with open(reported_file, 'w') as f:
        f.write('\n'.join(reported_items))

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

    # 파일 작업을 투두로 변환 (work_todos 없을 때만)
    if not work_todos and files_modified:
        # 파일명으로 작업 유추
        modified_list = list(files_modified)[:3]
        if len(modified_list) == 1:
            work_todos.append(f"{modified_list[0]} 코드 수정")
        else:
            work_todos.append(f"{', '.join(modified_list)} 등 {len(files_modified)}개 파일 수정")

    # 출력 - 신규 항목만
    if new_todos:
        print("TODOS_START")
        for todo in new_todos[-5:]:
            icon = "✅" if todo['status'] == 'completed' else "🔄" if todo['status'] == 'in_progress' else "⏳"
            print(f"{icon} {todo['content']}")
        print("TODOS_END")
    elif work_todos:
        print("TODOS_START")
        for work in work_todos[:5]:
            print(f"✅ {work}")
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

    # 파일 정보만 출력 (도구 요약 제거)
    if files_modified:
        print(f"MODIFIED:{','.join(list(files_modified)[:10])}")
    if files_analyzed:
        print(f"ANALYZED:{','.join(list(files_analyzed)[:10])}")

except Exception as e:
    print(f"ERROR:{str(e)}", file=sys.stderr)
    sys.exit(1)
