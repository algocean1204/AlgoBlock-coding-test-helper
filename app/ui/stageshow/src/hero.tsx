// README 맨 위의 멈춘 그림. 넓은 창이 위에서 시작해 아래로 흘러나가고, 조용한 위계를 둔다.
// 블록 | 코드와 채점 결과 | 튜터와의 대화 세 칸을 한 창에 담는다. 안내 3장·1장의 부품을 그대로 쓴다.
// 글은 스택/큐 1단계 '괄호 깊이 재기'의 풀이와 그 대화.
import { Button, Check, Code, Field, Stage, Text, Window } from '../kit'
import { Block } from './demos/Tutor'
import './demos/judge.css'
import './demos/tutor.css'
import './hero.css'

const CODE = [
  'def solution(expr):',
  "    partner = {')': '(', ']': '[', '}': '{'}",
  '    stack = []',
  '    deepest = 0',
  '    for ch in expr:',
  "        if ch in '([{':",
  '            stack.append(ch)',
  '            deepest = max(deepest, len(stack))',
  '        elif ch in partner:',
]

export function Hero() {
  return (
    <Stage width={880} height={440} theme="light" className="algoblock d1 d3 hero">
      {() => (
        <Window title="AlgoBlock" className="hero-win">
          <div className="hero-body">
            <div className="d3-blocks">
              <Block n={1} name="스택 준비" kind="풀이 중에 만드는 변수" state="found" />
              <Block n={2} name="글자 하나씩 보기" kind="반복" state="found" />
              <Block n={3} name="맨 위와 짝 맞추기" kind="조건" state="found" />
              <Block n={4} kind="분기" state="current" />
              <Block n={5} kind="풀이 중에 만드는 변수" state="locked" />
            </div>
            <div className="d1-pane hero-code">
              <Code className="d1-code" lines={CODE} />
              <div className="d1-actions">
                <Button>예시 실행</Button>
                <Button>제출</Button>
              </div>
              <div className="d1-result">
                <span className="d1-line">
                  <Check on size={18} />
                  <Text className="d1-pass">통과</Text>
                  <Text className="d1-counts">정확성 20/20 · 효율성 2/2</Text>
                </span>
              </div>
            </div>
            <div className="d3-chat">
              <div className="d3-thread">
                <div className="d3-msg d3-msg--tutor">
                  <Text wrap>닫는 괄호를 만나면, 무엇과 짝을 맞춰 봐야 할까요?</Text>
                </div>
                <div className="d3-msg d3-msg--me">
                  <Text wrap>가장 마지막에 나온 여는 괄호요</Text>
                </div>
                <div className="d3-msg d3-msg--tutor">
                  <Text wrap>그 괄호를 다시 꺼내 보려면, 어디에 모아 두면 좋을까요?</Text>
                </div>
              </div>
              <div className="d3-composer">
                <Field value="" placeholder="생각나는 대로 적어 보세요" />
                <div className="d3-send">
                  <Button variant="primary">보내기</Button>
                </div>
              </div>
            </div>
          </div>
        </Window>
      )}
    </Stage>
  )
}
