"""대화 원칙을 규칙으로 지킨다. 금지 표현, 인용 확인, 말풍선 검사, 유형별 대체 질문.

대화 원칙
1. 판정을 먼저 말하지 않는다. 첫 문장은 사용자 말의 가정, 빠진 경우, 근거를 겨누는 질문이다.
2. 근거를 가르게 한다. 의자는 사용자에게 근거 수준을 묻고, 튜터가 주장할 때(피드백)는 확신 표시를 붙인다.
3. 생각을 닫는 말을 쓰지 않는다(금지 표현 목록).
진행 안내(이음말, 앞말)는 화면 상태를 알리는 고정 문구라 예외다.
"""

import re
import sys
from difflib import SequenceMatcher

from .solution import _WORDS, body_lines, bound_names, frame_flags

BANNED = (
    "정답", "맞아요", "맞습니다", "틀렸어요", "완벽", "훌륭", "잘했어요", "좋아요", "좋은 질문", "좋은 생각",
    "전적으로", "말씀하신 게 맞", "정말 그렇", "분명히 그렇", "당연히",
)

# 원칙 1: 첫 문장 맨 앞에서만 보는 동의·칭찬 여는 말. 이음말·앞말은 검사 뒤에 붙어(turn/graph.py check_reply) 걸리지 않는다
AGREE_OPENERS = (
    "맞아요", "맞습니다", "맞아", "좋아요", "좋습니다", "정확해요", "정확합니다", "잘했어요", "잘하셨어요", "훌륭",
    "네,", "네.", "네!", "그렇죠", "바로 그거",
)
_AGREE = re.compile(r"좋은 (관찰|생각|질문|지적|접근|시도)|잘 (짚|보|찾)|훌륭|정확히")  # '좋은 관찰이에요.'(디버그)


def agree_opening(text: str, problem: str = "") -> bool:
    """첫 문장 맨 앞이 동의·칭찬인가(문항 글 인용은 뺀다)."""
    head = without_problem_quotes(text, problem).lstrip()
    return head.startswith(AGREE_OPENERS) or bool(_AGREE.match(head))

# 사용자가 하지 않은 판단을 인정했다('잘 모르겠어요'에 '…을 짚으셨는데, 그 판단은 맞는 방향입니다').
# 판단을 맞다고 하는 평서문은 늘 판정이다(원칙 1). 사용자 말에 생각이 담기지 않았으면 그 말에 기대는 문장('짚으셨는데', '말씀하신 대로')도 없는 판단을 지어낸 것이다
_VERDICT = re.compile(r"(?:판단|생각|방향|짐작|추측|짚은\s*것)[은는이가]?\s*(?:맞|옳|정확)(?!는지|은지|을지|는가|을까)"
                      r"|(?:맞는|옳은|정확한)\s*(?:방향|판단|생각|짐작)|제대로\s*짚|잘\s*짚")
# 판단을 받는 동사만 본다: '따라가 보셨나요?', '앞에서 찾으신 값은…?'은 한 일을 묻는 말이지 판단을 인정하는 말이 아니다
_CREDIT = re.compile(r"(?:짚|말씀하|말하|판단하|짐작하|생각하)(?:으)?(?:셨|신)|짚었")
# 학습자의 가정을 되짚는 문장에 붙은 동의 말('말씀하신 대로 …라고 가정하셨네요'). 되짚는 말이 맞다고 인정하는 것처럼 들린다
# 문장 첫머리의 '말씀하신 대로 …(평서)'나 '그렇죠.' 홀로만 본다. '가정하신 대로라면 …인데 실제로는 …'처럼 가정과 실제를 견주는 조건·반박은 동의가 아니다
_LEAN_AGREE = re.compile(r"^\s*(?:(?:말씀(?:하신)?|말하신|짚으신)\s*(?:대로|처럼)(?!\s*(?:라면|하면|이면|면))|그렇죠\s*[.!]?\s*$)")
_NO_CLAIM = re.compile(r"모르|몰라|글쎄|헷갈|감이\s*안|막혔")
NO_CLAIM_CHARS = 15  # 공백을 뺀 사용자 말이 이보다 짧고 막힌 말이면 인정할 판단이 없다


def unsaid_credit(text: str, user: str = "") -> list[str]:
    """사용자가 하지 않은 판단을 인정한 문장들. 판단을 맞다고 하는 평서문은 늘, 생각이 담기지 않은 사용자 말('잘 모르겠어요') 뒤에는 그 말에 기대는 문장도."""
    plain = re.sub(r"\s+", "", user or "")
    empty = not plain or (len(plain) < NO_CLAIM_CHARS and bool(_NO_CLAIM.search(plain)))
    return [part for part in sentences(text)
            if ((_VERDICT.search(part) or _LEAN_AGREE.search(part)) and not part.rstrip().endswith(("?", "？"))) or (empty and _CREDIT.search(part))]


# 물음 어미: 물음표, '~나요', '~까(요)'('~니까'는 빼고), '~(인·는·건·은·한·뭔)가요', '~죠', 뜻 묻기('뭐예요', '뭐야', '뭔데'), 반말 '~나'('맞나'. '하나'·'그러나'는 빼고)
_ASKED = re.compile(r"(?:[?？]|나요|(?<!니)까요?|(?:인|는|건|은|한|뭔)가요|죠|뭐예요|뭐에요|뭐야|뭔데|(?<!하)(?<!그러)나)\s*$")


def _asked_parts(text: str) -> list[str]:
    """사용자 말을 문장·줄로 나눠 물음인 것만(asked_count와 여럿 물음 검사가 같은 나눔을 쓴다)."""
    # 백틱·펜스 코드 구간만 뺀다(코드 모양 줄을 통째로 지우면 'x = a ? b : c 에서 ? 는 뭐죠?'가 0개였다).
    # 문장 끝은 글자 바로 뒤의 문장 부호다: 앞에 공백이 있는 '?'(코드 속 삼항 연산, '? 는')는 문장을 끊지 않는다
    plain = _CODE_SPAN.sub(" ", text or "")
    parts = [part.strip() for part in re.split(r"(?<=[^\s][.?!？])\s+|\n", plain) if part.strip()]
    return [part for part in parts if _ASKED.search(part)]


def asked_count(text: str) -> int:
    """사용자 말 속 물음의 수(문장·줄마다 물음표나 물음 어미로 끝나는가)."""
    return len(_asked_parts(text))


# 물음에서 핵심 낱말을 고를 때 빼는 것: 물음 어미로 끝나는 낱말, 흔한 말
_ASK_WORD = re.compile(r"(?:나요|까요?|가요|죠|예요|에요|뭐야|뭔데|해요|어요|아요|세요|니다)$")
_COMMON = {"그리고", "그런데", "그러면", "그럼", "어떻게", "어떤", "무엇", "무슨", "이거", "이게", "그거", "그게", "저거", "근데", "혹시", "정말", "진짜",
           "방법", "생각", "때문", "경우", "부분", "하나", "이것", "그것", "여기", "거기", "아니", "그냥", "이렇게", "그렇게", "어디", "언제", "누가",
           "다음", "다음엔", "다음에", "그다음", "아니면", "뭔가", "이건", "그건", "저건"}
_PARTICLE = re.compile(r"(?:(?<=[가-힣])(?:에는|에서|으로|에게|한테|이랑|하고|보다|부터|까지|처럼|께서|에는|엔)|(?<=[가-힣]{2})(?:은|는|이|가|을|를|에|의|도|로|와|과|만|별|마다))$")
_DEFERRED = re.compile(r"다음\s*(?:차례|번|에)|나중에|먼저[^.?!？]*?(?:보고|볼게|보겠|살펴)")  # 하나를 미뤘다고 말한 답


def asks_ignored(text: str, user: str) -> bool:
    """물음이 둘 이상인 사용자 말에 답이 그 물음들의 핵심 낱말(코드 이름·백틱 조각·한글 낱말)을 하나도 다루지 않았는가.
    하나라도 다뤘거나 하나를 미뤘다고 말한 답, 낱말을 뽑지 못한 물음은 통과한다(오탐을 피한다).
    영문 이름은 대소문자를 무시하고, 한글 낱말은 조사를 떼고 앞 두 글자(줄기)로 견준다('정렬해야'↔'정렬하면')."""
    if asked_count(user) < 2:
        return False
    parts = _asked_parts(user)
    words = {_PARTICLE.sub("", word)[:2] for part in parts for word in re.findall(r"[가-힣]{2,}", part)
             if word not in _COMMON and not _ASK_WORD.search(word)}
    words |= {span.strip("` ").lower() for span in re.findall(r"`[^`\n]+`", user or "")}
    names = {name.lower() for part in parts for name in re.findall(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*", part)}  # 'k'처럼 한 글자 이름도(낱말 경계로 찾는다)
    words.discard("")
    body = (text or "").lower()
    return (bool(words) or bool(names)) and not _DEFERRED.search(body) and not any(word in body for word in words) \
        and not any(re.search(rf"(?<![a-z0-9_]){re.escape(name)}(?![a-z0-9_])", body) for name in names)


DEFER_TAIL = "다른 물음은 다음 차례에 이어 봐요."


def defer_ask(text: str, user: str) -> str:
    """물음이 여럿인데 답이 하나도 받지 않았으면 답 앞에 미룸 문장을 붙인다(답 본문은 그대로, 못 받은 물음은 다음 차례에 many_asks_line이 잇는다)."""
    if not asks_ignored(text, user):
        return text
    many = "여럿이라" if asked_count(user) > 2 else "둘이라"
    return f"물음이 {many} 하나씩 볼게요. {DEFER_TAIL} {text}"


def deferred_user(said) -> list[str]:
    """블록이 바뀌는 차례용: 답을 받은 가장 나중 학습자 말을 recent 꼴로 돌려준다(저장 상태 없이 대화 기록에서 읽는다).
    물음이 여럿이었는지는 many_asks_line이 본다(엔진이 미룸 문장을 붙였든 모델이 스스로 미뤘든 같다).
    블록 코드 확인 글(판정 표시)은 학습자 말로 치지 않는다. 그 말 뒤에 다른 블록의 튜터 말(새 블록의 첫 질문)이 있으면 이미 넘긴 것이라 넘기지 않는다."""
    said = list(said)
    k = next((i for i in range(len(said) - 2, -1, -1) if said[i].role == "user" and not (said[i].move or "").startswith(CHECKED)
              and said[i + 1].role == "service"), -1)
    if k < 0 or not said[k].text or any(m.role == "service" and m.block_index != said[k].block_index for m in said[k + 1:]):
        return []
    return [f"사용자: {said[k].text}"]


def many_asks_line(text: str, recent: list[str] | None = None) -> list[str]:
    """사용자 말에 물음이 여럿이면 질문 프롬프트에 넣을 지시. 둘 가운데 하나만 받았다.
    답을 먼저 주지 않는 원칙은 그대로다: 받는다는 것은 개념을 풀어 주거나 볼 곳을 좁혀 주는 것이다.
    지난 사용자 말에 물음이 여럿이었다면(recent의 '사용자: …') 아직 받지 못한 물음으로 돌아오게 한다(대화 기록이 곧 상태다)."""
    n = asked_count(text)
    lines = [f"사용자 말에 물음이 {n}개 있다. 물음마다 한 구절씩 받는다(개념을 풀어 주거나 볼 곳을 좁혀 준다. 답·고칠 곳은 말하지 않는다). "
             "하나만 받을 때는 그 하나를 먼저 본다고 말하고, 나머지 물음은 다음에 보겠다고 한 구절로 남긴다."] if n > 1 else []
    last = next((m.split(": ", 1)[1] for m in reversed(recent or []) if m.startswith("사용자: ")), "")
    if asked_count(last) > 1:
        lines.append(f"지난번 사용자 말에도 물음이 여럿이었다: {last!r}. 앞의 튜터 말이 받지 못한 물음이 있으면 이번에 그 물음으로 돌아와 한 구절로 받는다.")
    return lines


OPEN_LEAD = "다음 블록을 열었어요. "  # 이음말
KIND_LABEL = {"var_from_problem": "문제에서 바로 오는 변수", "var_during": "풀이 중에 만드는 변수", "loop": "반복", "condition": "한 가지를 따지는 조건", "branch": "경우 나누기"}


def kind_word(kind: str) -> str:
    """블록 종류를 말로(모델에 영어 꼬리표 `var_during`를 넘기지 않는다)."""
    return KIND_LABEL.get(kind, kind)


def open_lead(mode: str, kind: str) -> str:
    """새 블록 이음말. 의자는 블록 이름(답)을 가리고 종류만 알려 준다: 종류(변수·반복·조건·분기)가 스스로 묻는 순서의 뼈대다."""
    if mode == "chair" and kind in KIND_LABEL:
        return f"다음은 '{KIND_LABEL[kind]}' 블록이에요. "
    return OPEN_LEAD
REPLAN_LEAD = "말한 방법으로 블록을 다시 짰어요. "  # 사용자 방향을 따른다(설계: 사용자의 사고 방향 우선). 동의로 시작하지 않는다
STUCK_LEAD = "막혔다면 이 블록 채우기로 코드를 받아 보고 넘어가도 돼요. "  # 사다리 꼭대기에서 두 번 막혔을 때 앞말
RETRY_LEAD = "이 코드로는 아직 넘어가지 않아요. "  # 블록 코드 판정 N일 때 앞말
CHECKED = "check:"  # 블록 코드 확인에 낸 사용자 글의 move 앞말. 뒤에 판정 Y·N·?(확인 전)이 붙는다
# 블록 코드 확인의 실행이 진입 함수 없이 끝났다(이어 붙이기의 잘못. 사용자 탓이 아니다). '확인 전'으로 두고 넘어갈 길을 말한다
CANNOT_RUN = "이 블록을 이어서 돌려 보지 못했어요. 맞다고 생각하면 '이대로 넘어가기'로 다음 블록을 열 수 있어요."
# 튜터의 풀이(블록을 나눈 코드)가 없거나 예시를 통과하지 못했다: 그 코드와 이어 돌린 결과는 내 블록의 판정이 될 수 없다. 블록은 '확인 전'으로 두고 넘어간다(틀린 수에 넣지 않는다)
UNVERIFIED = "튜터의 풀이를 이 문제의 예시로 확인하지 못해서, 이 블록을 이어 돌려 확인할 수 없어요. 코드를 끝까지 쓴 뒤 '실행'이나 '제출'로 확인해 주세요."
SKIPPED = "이 블록은 확인하지 않고 넘어왔어요(확인 전). 코드를 끝까지 쓴 뒤 '모아서 실행'이나 제출로 확인해 주세요."  # '이대로 넘어가기'
# '끝까지 내 방식으로 쓰기'(넘어가기 말 SKIPPED 뒤에 붙는다). 다르게 썼다고 단정하지 않는다
OWN_WAY = "남은 블록을 모두 열었어요. 블록 이름은 튜터가 푼 차례라 참고만 해요. 블록마다 확인하려면 '튜터 차례로 돌아가기'를 눌러요."
ALONE_OK = "지금까지 쓴 코드만으로 이미 통과해요. 남은 블록은 건너뛰고 '모아서 실행'이나 제출로 가도 돼요."  # 튜터의 코드 없이 내 블록만 이어 돌렸다
MALFORMED = "판정을 받지 못했어요. 다시 확인해 주세요."  # 모델의 답이 형식에 맞지 않았다
# 등록할 때 '답이 여럿일 수 있음'을 켠 문제에서 값이 달랐다: 예시의 답 하나와 견줄 뿐이라 맞는지 모른다(제출과 블록 확인이 같이 쓴다. 블록은 '확인 전')
MANY_ANSWERS = "예시와 다른 답이에요. 이 문제는 답이 여럿일 수 있어서 맞는지 가릴 수 없어요."
# 확인 전인 내 블록의 글이 들어간 실행이 통과하지 못했다: 어느 블록 때문인지 모른다('확인 전'. 틀린 수·힌트를 붙이지 않는다)
UNCHECKED_IN = "이 실행에는 확인 전인 {blocks}번 블록의 내 코드가 들어 있어서, 어느 블록 때문인지는 알 수 없어요."
ALONE_LEAD = "내 코드만으로 돌렸더니"  # 튜터의 코드 없이 내 블록만 이은 프로그램이 통과하지 못했다
# 실행하지 못해 모델이 코드를 읽고 통과시켰다: 실행으로 확인한 통과와 다르게 말한다(진행은 막지 않는다)
UNRUN = "이 블록은 실행하지 못해서({why}) 코드를 읽고 본 판단이에요."
UNRUN_NO = "읽어 보니 아직 안 맞는 것 같지만 실행으로 확인하지는 못했어요."
UNRUN_WHY = {"toolchain_missing": "이 기기에 이 언어를 실행할 도구가 없어요", "unsupported_signature": "이 문제의 인자 형은 아직 돌릴 수 없어요",
             "no_cases": "이 문제에 돌려 볼 케이스가 없어요"}


def fence(text, rows: int = 10) -> str:
    """여러 줄 출력을 줄을 지킨 글상자(```)로: 말 안에 줄을 펴 넣지 않는다(화면이 글상자로 그린다). 너무 길면 앞쪽 rows줄만."""
    lines = str(text if text is not None else "").strip("\n").split("\n")
    return "```\n" + "\n".join(lines[:rows] + (["…"] if len(lines) > rows else [])) + "\n```"


def unrun_why(status: str) -> str:
    """채점하지 못한 까닭(채점 결과의 status)을 사용자의 말로. 모르는 까닭은 한 가지 말로 한다."""
    return UNRUN_WHY.get(status, "이 코드를 돌리지 못했어요")


UNRUN_FIX = {"toolchain_missing": " 그 도구를 설치하면 실행으로 확인할 수 있어요."}  # 사용자가 고칠 수 있는 까닭만
EXAMPLES_ONLY = "공개 예시로만 확인했어요."  # 문제에 숨은 테스트가 없다: 통과가 약하다는 것을 말한다
ANSWER_LEAD = "답 코드는 드리지 않아요. 지금 블록만 보고 싶다면 블록 칸의 '이 블록 채우기'를 쓸 수 있어요. "  # 답을 달라고 할 때 앞말
FILL_TIP = "막히면 블록 칸의 '이 블록 채우기'로 이 블록만 볼 수 있어요. "  # 같은 블록에서 내용 없는 답이 두 번 이어졌을 때 앞말(한 블록에 한 번)
BACK_LEAD = "지금 문제로 돌아갈게요. "  # 문제와 무관한 말일 때 앞말
HARD_LEAD = "한 걸음 더 작게 나눠 볼게요. "  # 어렵다는 짧은 말 뒤 앞말(다음 저장 힌트가 더 작은 질문이다)
# 가이드 마지막 블록 코드 통과(진행 안내, 묻지 않는다). 의자에서 말로만 찾아 코드 칸이 빈 블록이 있을 수 있어 어느 경우에도 맞게 쓴다
ALL_FILLED = "블록을 끝까지 열었어요. 코드 칸이 빈 블록이 있으면 채운 뒤, 이어 붙인 코드로 실행하거나 제출해 보세요."

WITHDRAWN = "뒤 블록 {n}개는 다시 확인해 주세요."  # 앞 블록을 고쳐 뒤 블록의 통과를 물렸다


def rename_note(pairs: list[list[str]]) -> str:
    """블록 코드가 계획과 다른 이름으로 통과했을 때 통과 말 뒤에 붙이는 안내([내 이름, 튜터 코드의 이름]. 이름 바꾸기 표에 처음 든 짝만 온다).
    'conveyor'로 통과한 뒤 '이 블록 채우기'로 채운 블록('belt')과 모으니 NameError였다. 어긋난다는 안내가 없었다.
    코드 이름 뒤 조사를 어림하면 틀렸다('remaining라고', 'cnt, r라고'). 이름을 괄호에 넣어 조사가 붙지 않게 쓴다."""
    if not pairs:
        return ""
    # '이름(`a`, `b`)을 차례대로 다른 이름(`c`, `d`)으로'는 어느 이름이 어느 이름인지 알기 어려웠다. 짝마다 화살표로 쓴다
    shown = ", ".join(f"`{a}` → `{b}`" for a, b in pairs)
    return (f"같은 값을 튜터의 코드는 다른 이름으로 써요(내 이름 → 튜터의 이름: {shown}). 이름이 달라도 이어서 돌아가요. "
            "뒤 블록을 '이 블록 채우기'로 채우면 튜터의 코드를 내 이름으로 바꿔 넣어요.")

FALLBACK = {
    "replan": "말한 방법에서 가장 먼저 정해야 할 것은 무엇일까요?",
    "open": "이 블록에서 무엇을 정해야 다음으로 갈 수 있을까요?",
    "clue": "문제 글에서 아직 쓰지 않은 조건을 하나 골라 보면, 그 조건은 무엇을 하라고 하나요?",
    "trace": "가장 작은 입력 하나를 손으로 따라가면 여기서 무엇이 필요해지나요?",
    "assume": "방금 말한 방법이 늘 통한다고 본 근거는 무엇인가요?",
    "edge": "입력이 비어 있거나 같은 값이 여러 번 나오면 그 방법은 어떻게 될까요?",
    "basis": "그렇게 생각한 까닭이 문제 글에 있나요, 아니면 짐작인가요?",
    "recap": "첫 블록부터 순서대로 무엇을 정했는지 말해 볼까요?",
    "blank": "이 빈칸에는 무엇이 들어가야 할까요?",
    "tool": "어떤 자료구조를 쓰면 이 빈칸이 채워질까요?",
    "shape": "이 빈칸을 말로 한 줄 써 보면 어떤 모양일까요?",
    "run": "채운 블록을 이어 예제 하나로 돌리면 무엇이 나올까요?",
    "verify": "그 생각대로 문제 예시의 첫 입력을 손으로 따라가 보면 무엇이 나오나요?",
    "followup": "이 인용에서 어느 부분이 막혔는지 한 문장으로 말해 줄 수 있을까요?",
    "term": "어느 부분이 낯선지 하나만 짚어 주면, 그것부터 같이 볼까요?",
    "close": "막히는 줄이 생기면 제출한 뒤 틀린 곳을 같이 찾을 수 있어요. 이제 찾은 순서대로 코드 칸에 옮겨 적고 제출해 볼까요?",
}

_QUOTES = re.compile(r"'([^']+)'|‘([^’]+)’|\"([^\"]+)\"|“([^”]+)”")
_SINGLE = re.compile(r"'([^']+)'|‘([^’]+)’")
_HANGUL = re.compile(r"[가-힣]")
_ENGLISH = re.compile(r"[A-Za-z]+(?:[ ,]+[A-Za-z]+){4,}")  # 영어 다섯 낱말 이상 = 모델의 지시문·메모가 샌 것
_NOTE = re.compile(r"(하자|보자|묻자|이끌자|시키자)[.。]?(\s|$)")  # '…따라가 보게 하자' 같은 모델의 계획 메모
# '…라고 물었어요.', '…된다"고 했어요.', '…제대로 짚었네요.'
_ECHO = re.compile(r"((이)?시군요|계시군요|(말해|알려|짚어) 주셨(어요|네요|습니다)|짚었(어요|네요)|짚으셨(네요|어요|군요)|물으셨(어요|네요|군요)|말씀이(시)?군요"
                   r"|라고 물었어요|고 (했|하셨)어요)[.!]?$")  # 사용자 말을 되받는 첫 문장
_CODE_SPAN = re.compile(r"```.*?```|`[^`\n]*`", re.S)
_CODE_LINE = re.compile(r"[\w)\]]\s*=[^=]|[(\[]\s*['‘\"]")  # 대입, 또는 괄호 바로 뒤 따옴표가 있는 줄은 코드 모양이다


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def in_problem(phrase: str, problem: str) -> bool:
    """공백을 모두 지우고 부분 일치로 본다. '...'·'…'로 줄인 인용은 조각마다 본다(줄인 인용의 따옴표가 벗겨졌다)."""
    pieces = [_squash(piece) for piece in re.split(r"\.{3}|…", phrase or "") if _squash(piece)]
    return bool(pieces) and all(piece in _squash(problem) for piece in pieces)


def _cut_in_word(piece: str, problem: str) -> bool:
    """문제 글에서 이 조각이 나오는 자리가 모두 낱말 중간(앞 글자가 글자·숫자)이다. '번째로 빌려지는'('k번째로'에서 떼었다)."""
    chars = _squash(piece)
    if not chars:
        return False
    starts = [found.start() for found in re.finditer(r"\s*".join(map(re.escape, chars)), problem or "")]
    return bool(starts) and all(at > 0 and (problem[at - 1].isalnum() or problem[at - 1] == "_") for at in starts)


def broken_quotes(text: str, problem: str, cut: bool = False) -> list[str]:
    """문제 글을 인용했는데 깨진 구절. 낱말 중간에서 떼어 시작했거나, cut이면 '…'로 줄인 것(저장 질문은 문장을 그대로 인용한다).
    문제 글에 없는 인용은 quotes_ok가 본다."""
    found = []
    for match in _SINGLE.finditer(without_code(text or "")):
        phrase = next(group for group in match.groups() if group is not None)
        if not _HANGUL.search(phrase) or not in_problem(phrase, problem):
            continue
        whole = _squash(phrase) in _squash(problem)  # 문제 글 자체의 '…'(수열 줄임)는 줄인 인용이 아니다
        pieces = [phrase] if whole else [piece for piece in re.split(r"\.{3}|…", phrase) if _squash(piece)]
        if (cut and len(pieces) > 1) or any(_cut_in_word(piece, problem) for piece in pieces):
            found.append(phrase)
    return found


def without_problem_quotes(text: str, problem: str) -> str:
    """문항 글을 그대로 인용한 따옴표 구간은 금지 표현 검사에서 뺀다."""

    def drop(match):
        phrase = next(group for group in match.groups() if group is not None)
        return "" if in_problem(phrase, problem) else match.group(0)

    return _QUOTES.sub(drop, text or "")


def banned_in(text: str, problem: str = "") -> list[str]:
    body = without_problem_quotes(text, problem)
    return [word for word in BANNED if word in body]


def near_quote(phrase: str, said: str) -> bool:
    """사용자 말을 조금 줄이거나 어미만 바꿔 인용한 것('이름을 세면 돼요' → '이름을 세면 된다')을 받아 준다."""
    a, b = _squash(phrase), _squash(said)
    if not a or not b:
        return False
    match = SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return match.size >= 0.6 * len(a)


def quotes_ok(text: str, problem: str, said: str = "", double: bool = False) -> bool:
    """작은따옴표(double이면 큰따옴표도)로 감싼 한글 구절이 모두 문항 글(과 허용한 글)에 있으면 참. 인용이 없어도 참.

    한글이 없는 구절('(]', 'a')은 예시 값이라 보지 않는다.
    """
    for match in (_QUOTES if double else _SINGLE).finditer(text or ""):
        phrase = next(group for group in match.groups() if group is not None)
        if _HANGUL.search(phrase) and not in_problem(phrase, problem) and not near_quote(phrase, said):
            return False
    return True


def sentences(text: str) -> list[str]:
    return [part for part in re.split(r"(?<=[.?!？])\s+", (text or "").strip()) if part.strip()]


def question_count(text: str) -> int:
    """물음표로 끝나는 문장 수. 따옴표 안의 물음표(사용자 말 인용)는 문장 끝이 아니라 세지 않는다."""
    return sum(part.rstrip().endswith(("?", "？")) for part in sentences(text))


def one_question(text: str) -> str:
    """질문이 여럿이면 마지막 질문만 남긴다(설명 문장은 그대로). 초보자는 한 번에 한 가지만 답할 수 있다."""
    parts = sentences(text)
    asks = [i for i, part in enumerate(parts) if part.rstrip().endswith(("?", "？"))]
    if len(asks) > 1:  # 지운 앞 질문에 기대던 잇는 말('아니면 …?')은 뗀다(끊긴 문장)
        parts[asks[-1]] = re.sub(r"^(아니면|그리고|또는|혹은)\s+", "", parts[asks[-1]])
    return " ".join(part for i, part in enumerate(parts) if i not in asks[:-1])


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"(?<=[.?!？])\s+", (text or "").strip()) if part.strip()])


_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\d.])")


def _told_terms(reference: str, language: str) -> tuple[set[str], list[str], set[str]]:
    """블록 알맹이가 정하는 것: (대입한 이름, 그 줄 주석의 한글 구절, 숫자 상수). 틀 줄과 내장 이름은 빠진다."""
    rows = (reference or "").splitlines()
    mark = "#" if language == "python" else "//"
    notes = [row.split(mark, 1)[1] for row, skip in zip(rows, frame_flags(rows, language, False)) if not skip and mark in row]
    phrases = [part.strip() for note in notes for part in re.split(r"[,:()/]", note) if len(_squash(part)) >= 4 and _HANGUL.search(part)]
    body = body_lines(reference, language)
    return bound_names(body), phrases, set(_NUMBER.findall(" ".join(body)))


def _tells(sentence: str, terms) -> bool:
    """평서문 하나가 블록의 대입·조건을 말로 옮겼는가: 이름(또는 주석 구절) 둘 이상(블록에 하나뿐이면 하나)과 블록의 숫자 상수가 함께 나온다."""
    names, phrases, numbers = terms
    total = len(names) + len(phrases)
    if not total or sentence.rstrip().endswith(("?", "？")) or not numbers & set(_NUMBER.findall(sentence)):
        return False
    squashed = _squash(sentence)
    hits = sum(bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", sentence)) for name in names)
    hits += sum(SequenceMatcher(None, _squash(p), squashed, autojunk=False).find_longest_match(0, len(_squash(p)), 0, len(squashed)).size
                >= 0.75 * len(_squash(p)) for p in phrases)
    return hits >= min(2, total)


def told_sentences(text: str, reference: str, language: str, problem: str) -> list[str]:
    """지금 블록의 답을 말한 평서문들. 문제 글을 인용한 구간과 코드 구간(문법 예시)은 보지 않는다."""
    terms = _told_terms(reference, language)
    return [part for part in sentences(text) if _tells(without_code(without_problem_quotes(part, problem)), terms)]


def names_block(name: str, body: str, problem: str) -> bool:
    """사용자 말에 답하는 가이드 턴의 뒤 블록 이름 검사: 이름 전체가 낱말 첫머리에서 그대로 나오고(뒤의 조사는 된다),
    문제 글에 없는 핵심 낱말이 둘 이상일 때만 참. 5차 실제 모델 확인: '먼저 내리기 때문입니다'가 블록 이름 '먼저 내리기'에 걸렸다."""
    words = name.split()
    core = [word for word in words if not in_problem(word, problem)]
    return len(core) >= 2 and bool(re.search(r"(?<![\w])" + r"\s+".join(map(re.escape, words)), body))


def reply_problems(
    text: str, *, move: str, problem: str, reference: str = "", later_names: list[str] = (), said: str = "", language: str = "python",
    loose_names: bool = False, user: str = "",
) -> list[str]:
    """말풍선 검사. 위반 이유 목록(비면 통과). said는 인용해도 되는 사용자 말·앞 대화(clue는 문항 글만).
    loose_names: 뒤 블록 이름을 names_block으로 좁혀 본다(가이드가 사용자 말에 답할 때. 의자는 블록 이름이 찾을 답이라 그대로)."""
    body = (text or "").strip()
    found = []
    if not body:
        return ["비었음"]
    if "```" in body:
        found.append("코드 펜스")
    if banned_in(body, problem):
        found.append("금지 표현")
    if agree_opening(body, problem):
        found.append("동의로 시작")
    if sentence_count(body) > 3:
        found.append("3문장 초과")
    if not body.rstrip().endswith(("?", "？")):
        found.append("질문으로 끝나지 않음")
    if question_count(body) > 1:
        found.append("질문 여럿")  # 눈높이 실패의 대부분이 한 말에 질문 둘·셋이었다
    for line in (reference or "").splitlines():
        # 공백 빼고 5자 이상인 줄만 본다. 더 짧은 줄('}', 'i += 1')은 평범한 말과 겹쳐 오탐이 난다
        if len(re.sub(r"\s+", "", line)) >= 5 and line.strip() in body:
            found.append("참고 코드")
            break
    if reference and told_sentences(body, reference, language, problem):
        found.append("답을 말함")
    if any(name.strip() and (names_block(name, body, problem) if loose_names else name.strip() in body) for name in later_names):
        found.append("뒤 블록 이름")
    if not quotes_ok(without_code(body), problem, "" if move == "clue" else said):
        found.append("문제 글에 없는 인용")
    if broken_quotes(body, problem):
        found.append("깨진 인용")
    plain = without_problem_quotes(body, f"{problem}\n{said}")
    if _NOTE.search(plain):
        found.append("3인칭 메모")  # '사용자는 …하게 하자' 같은 모델 메모가 샌 것
    if _ENGLISH.search(plain):
        found.append("영어 지시문")
    if unsaid_credit(body, user):
        found.append("말하지 않은 판단 인정")  # user: 이번 사용자 말(인정할 판단이 있는지 본다)
    return found


def outside_code(text: str, fix, code=lambda span: span) -> str:
    """코드 구간(백틱·펜스 안, 코드 모양 줄)은 code로(기본은 그대로), 나머지 글에는 fix를 쓴다. 문법 예시의 문자열 따옴표가 벗겨졌다."""
    spans, rest = _CODE_SPAN.findall(text), _CODE_SPAN.split(text)

    def prose(part: str) -> str:
        return "\n".join(code(line) if _CODE_LINE.search(line) else fix(line) for line in part.split("\n"))

    return prose(rest[0]) + "".join(code(span) + prose(part) for span, part in zip(spans, rest[1:]))


def without_code(text: str) -> str:
    """코드 구간을 지운 글. 인용 검사와 답 말하기 검사는 문법 예시 코드를 보지 않는다(문법 예시의 문자열이 '문제 글에 없는 인용'에 걸렸다)."""
    return outside_code(text or "", lambda line: line, lambda span: " ")


# 말의 맨 앞에서 사용자 말을 되받는 절: '방금 "모르겠어요"라고 하셨는데,' / '답 코드를 달라고 했으니,'
# ''…안 돼요?'라고 물으셨는데,'. 인용 안의 물음표처럼 공백이 뒤따르지 않는 문장 부호는 절을 끊지 않는다
_ECHO_CLAUSE = re.compile(r"^(?:[^.?!？]|[.?!？](?=\S))*?(?:(?:라고|라는|다고)\s*(?:말씀하셨|하셨|했|물으셨|물었|질문하셨)(?:는데|으니까|으니|지만|고)"
                          r"|[을를]\s*(?:해\s*)?달라[\"'”’]?고\s*(?:하셨|했)(?:으니|는데|지만))\s*[,，]\s*")
_ECHO_LEAN = re.compile(r"그 (말|질문|생각)[이은을]")  # 지운 되받기 문장에 기대는 첫머리(첫 쉼표까지 뗀다)
_LEANS = re.compile(r"(그 (부탁|말|요청|질문|물음)|그것|그건|그래서|그러니)")  # 지운 절에 기대는 문장의 첫머리
# 프롬프트 지시를 말로 옮긴 문장. 실제 모델 확인: '"답을 달라"고 했으니 안내 문장은 앞에 따로 붙고, 저는 … 질문 한 문장만 씁니다.'
_META = re.compile(r"안내 (문장|말)|지금 블[록럭](만 봅|을 겨[눈눠])|(질문|말) 한 문장만|부탁에는 답하지 않")
_CONNECTIVE = re.compile(r"^(그러면|그러니까|그러니|그렇다면|그럼|다만|하지만)\s*,?\s*")  # 앞 말이 없는데 잇는 첫머리('다만 지금은…'으로 질문을 돌렸다)
# 시키는 문장('…적어 보세요. 특히 …확인해 보면 어떨까요?' 요청 둘). '…라고 (생각)해 봅시다'는 가정이라 시키는 말이 아니다
_ORDER = re.compile(r"(?<![라다]고 해 )(?<![라다]고 생각해 )(?<![라다]고 가정해 )(보세요|주세요|봅시다)[.!]?$")
_ORDER_LEAN = re.compile(r"^(특히|그리고|그때)\s*,?\s*")  # 지운 시키는 문장에 기대는 첫머리


def _asks(parts: list[str]) -> bool:
    return any(part.rstrip().endswith(("?", "？")) for part in parts)


def drop_echo(text: str) -> str:
    """사용자 말을 되받는 첫 절·첫 문장을 지운다. 남는 글에 질문이 있을 때만(원칙 1. 이음말·앞말은 검사 뒤에 붙어 여기 오지 않는다).
    절을 지운 뒤 남은 첫 문장이 그 절에 기대면('그 부탁에는 답하지 않고 …') 그 문장도 지운다."""
    clause = _ECHO_CLAUSE.match(text)
    if clause:
        rest = sentences(text[clause.end():])
        if rest and _LEANS.match(rest[0]):
            rest = rest[1:]
        if _asks(rest):
            text = " ".join(rest)
    parts = sentences(text)
    if len(parts) > 1 and _ECHO.search(parts[0].strip()) and _asks(parts[1:]):
        parts = parts[1:]
        if _ECHO_LEAN.match(parts[0]) and "," in parts[0]:  # '그 말이 맞는지보다 먼저, …'(지운 문장에 기댄다)
            parts[0] = parts[0].split(",", 1)[1].strip()
    kept = [part for part in parts if not (_META.search(part) and not part.rstrip().endswith(("?", "？")))]
    if kept != parts and _asks(kept):
        parts = kept
    asks = [i for i, part in enumerate(parts) if part.rstrip().endswith(("?", "？"))]
    kept = [part for i, part in enumerate(parts) if not (asks and i < asks[-1] and _ORDER.search(part.strip()))]  # 질문 앞의 시키는 문장
    if kept != parts:
        parts = [_ORDER_LEAN.sub("", kept[0]), *kept[1:]]
    return _CONNECTIVE.sub("", " ".join(parts))


def drop_told(text: str, reference: str, language: str, problem: str) -> str:
    """지금 블록의 답을 말한 평서문을 지운다. 남는 글에 질문이 있을 때만. 지운 문장은 표준 오류에 남긴다(지나치게 지우는지 보려고)."""
    told = told_sentences(text, reference, language, problem) if reference else []
    rest = [part for part in sentences(text) if part not in told]
    if not told or not _asks(rest):
        return text
    print(f"[talk] 답을 말한 문장을 지움: {' / '.join(told)}", file=sys.stderr)
    return " ".join(rest)


def repair(text: str, problem: str, said: str = "", move: str = "", reference: str = "", language: str = "python", user: str = "") -> str:
    """모델을 다시 부르지 않고 고칠 수 있는 위반을 고친다. 되받는 첫 절·문장, 블록의 답을 말한 평서문, 근거 없는 따옴표는 지우고,
    마지막 물음표 뒤 글은 자르고, 뒤 세 문장만 남긴다. 근거 질문(basis)은 사용자 말을 인용해 묻는 것이 설계라 되받기를 지우지 않는다."""

    def unquote(match):
        phrase = next(group for group in match.groups() if group is not None)
        if _HANGUL.search(phrase) and not in_problem(phrase, problem) and not near_quote(phrase, said):
            return phrase
        return match.group(0)

    body = outside_code((text or "").strip(), lambda part: _SINGLE.sub(unquote, part))
    body = re.sub(r"사용자(?:님)?(?:께서는|께서|가|는|의 말처럼|의)?\s*", "", body)  # 상대를 '사용자'라 부르지 않는다(프롬프트 낱말이 샌 것)
    if move != "basis":
        body = drop_echo(body)
    body = drop_told(body, reference, language, problem)
    credit = unsaid_credit(body, user)
    if credit and _asks([part for part in sentences(body) if part not in credit]):  # 하지 않은 판단을 인정한 문장은 지운다(질문이 남을 때만)
        body = _CONNECTIVE.sub("", " ".join(part for part in sentences(body) if part not in credit))
    last = max(body.rfind("?"), body.rfind("？"))
    if last >= 0:
        body = body[: last + 1]
    return " ".join(sentences(one_question(body))[-3:])


def note_fallback(where: str, problems: list[str], text: str) -> None:
    """대체 질문이 나간 까닭을 표준 오류에 한 줄 남긴다(어느 규칙에 걸렸는지 알 수 있게)."""
    print(f"[{where}] 대체 질문: {', '.join(problems)} | {' '.join((text or '').split())[:160]}", file=sys.stderr)


_NAME = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]+(?![A-Za-z0-9_])")


def code_names(text: str, code: str, problem: str) -> list[str]:
    """말에 나온 코드 이름 가운데 문제 글에 없는 것('day일까지 점검이 몇 번인지': day는 참고 코드의 인자 이름이다). 코드 구간(백틱)은 보지 않는다."""
    names = set(_NAME.findall(code or "")) - set(_NAME.findall(problem or ""))
    return sorted(set(_NAME.findall(without_code(text or ""))) & names)


_OWN_NAME = re.compile(r"(?<![\w.])[A-Za-z_]\w+")  # 두 글자 이상, 점 뒤(메서드·속성)는 아닌 이름


def code_leaks(text: str, code: str, language: str) -> bool:
    """말의 코드 구간·코드 모양 줄이 이 문제의 코드를 옮겼는가. 되묻기 답(term)의 문법 예가 이 문제의 변수와 답 줄을 썼다.
    code의 이름(예약어·내장 이름, 대문자로 시작하는 형·클래스 이름은 뺀다)을 쓰거나, 공백을 빼고 견줘 code의 줄을 담으면 참.
    한 글자 이름과 예약어만 같은 예('for x in fruits:')는 거짓이다."""
    parts = []
    outside_code(text or "", lambda line: line, lambda span: parts.append(span) or span)
    words = _WORDS["python" if language == "python" else "other"]
    names = {name for name in _OWN_NAME.findall(code or "") if name not in words and not name[0].isupper()}
    # 견줄 줄: 끝의 ':', ';', '{'를 뗀 5자 이상, 예약어가 아닌 이름이 있는 줄('} else {', 'else:'는 뺀다)
    rows = [row for row in (_squash(line).rstrip(":;{") for line in (code or "").splitlines())
            if len(row) >= 5 and any(word not in words for word in re.findall(r"[A-Za-z_]\w*", row))]
    return any(names & set(_OWN_NAME.findall(part)) or any(row in _squash(part) for row in rows) for part in parts)


SAME_HINT = 0.8  # 공백을 뺀 두 질문이 이만큼 같으면 같은 질문을 되풀이한 것이다


def repeated_hints(hints: list[str]) -> bool:
    """한 블록의 저장 질문 가운데 거의 같은 둘이 있다(첫 질문과 다음 힌트가 같은 문장이었다)."""
    rows = [_squash(hint) for hint in hints if _squash(hint)]
    return any(SequenceMatcher(None, a, b, autojunk=False).ratio() >= SAME_HINT for i, a in enumerate(rows) for b in rows[i + 1 :])


def hint_problems(hint: str, *, problem: str, reference: str, later_names: list[str], clue: bool, code: str = "") -> list[str]:
    """계획에 저장할 의자 질문 검사. 3문장 제한은 보지 않는다(1–2문장으로 만들게 지시).
    code: 계획의 모든 참고 코드(문제 글에 없는 코드 이름을 거른다)."""
    found = reply_problems(hint, move="clue", problem=problem, reference="", later_names=later_names)  # 저장 질문의 인용은 모두 문항 글이어야 한다
    found = [item for item in found if item != "3문장 초과"]
    if reference.strip() and reference.strip() in hint:
        found.append("참고 코드")
    if "깨진 인용" not in found and broken_quotes(hint, problem, cut=True):
        found.append("깨진 인용")  # 줄인 인용('…')은 저장 질문에서만 막는다(대화는 줄인 인용을 받아 왔다)
    if code_names(hint, code or reference, problem):
        found.append("문제 글에 없는 코드 이름")
    return found
