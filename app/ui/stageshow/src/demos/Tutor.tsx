import { Button, Collapse, Field, Icon, Roll, Stream, Text, Window, type Act } from '../../kit'
import { Scene } from '../scene'
import './tutor.css'

// 3장 "튜터를 연결하면, 질문으로 함께 풀어요". 보낸 말이 내려앉고, 생각하는 중, 답이 흘러나온다.
// 박자: 튜터의 질문에 답을 쓴다 → 보내기 → 튜터가 생각하는 중 → 지금 찾던 블록에 이름이 붙고 찾음으로 바뀐다 → 다음 질문.
// 한 번만 재생, 멈춘 그림은 블록이 쌓이고 다음 질문이 온 장면. 좁은 화면은 지금 블록 하나와 대화만 잡는다(생각하는 중 줄과 다음 질문은 뺀다).
// 진짜 글: 블록 종류 이름, '지금 찾는 블록', 입력 칸 안내문, '보내기', '튜터가 생각하는 중…'.
// 블록 이름과 대화는 1장과 같은 데모 전용 문제 '짝수의 개수'의 풀이를 따라 지었다(기본 문제의 블록 이름을 보여 주지 않는다).

const Q1 = 'numbers의 수를 빠짐없이 보려면, 어떻게 보면 될까요?'
const ANSWER = '앞에서부터 하나씩 꺼내 봐요'
const Q2 = '꺼낸 수가 짝수인지는 무엇으로 알 수 있을까요?'
const WORDS = Q2.split(' ').length

const BLOCKS = [
  { name: '받은 수 목록', kind: '문제에서 바로 오는 변수' },
  { name: '짝수 개수 담기', kind: '풀이 중에 만드는 변수' },
  { name: '수 하나씩 꺼내기', kind: '반복' },
]

type S = { draft: string; sent: boolean; thinking: boolean; found: boolean; asked: boolean; words: number }

const initial: S = { draft: '', sent: false, thinking: false, found: false, asked: false, words: 0 }
const poster: S = { draft: '', sent: true, thinking: false, found: true, asked: true, words: WORDS }

async function script(a: Act<S>) {
  await a.wait(800)
  a.mark('type')
  await a.type('draft', ANSWER, { interval: 50 })
  await a.wait(350)
  a.mark('send')
  await a.click({ at: 'send', x: 0.84, y: 0.64 })
  a.put({ sent: true, draft: '' })
  await a.wait(500)
  a.put({ thinking: true })
  await a.move({ at: 'rest' }, { duration: 700 })
  await a.wait(600)
  a.mark('block')
  a.put({ found: true })
  await a.wait(900)
  a.mark('ask')
  a.put({ thinking: false, asked: true })
  for (let i = 1; i <= WORDS; i++) {
    a.put({ words: i })
    await a.wait(70)
  }
  await a.wait(3200)
}

export function Block({ n, name, kind, state }: { n: number; name?: string; kind: string; state: 'found' | 'current' | 'locked' }) {
  return (
    <div className="d3-block" data-state={state}>
      <span className="d3-no">{n}</span>
      {state === 'locked' ? (
        <Text className="d3-kind">{kind}</Text>
      ) : (
        <span className="d3-names">
          <Roll className="d3-name" variant="fade">{name ?? '지금 찾는 블록'}</Roll>
          <Text className="d3-kind">{kind}</Text>
        </span>
      )}
      {state === 'locked' && <Icon name="lock" size={14} className="d3-lock" />}
    </div>
  )
}

export default function Tutor() {
  return (
    <Scene name="d3" initial={initial} poster={poster} script={script} cursor={{ at: { wide: { x: 500, y: 190 }, compact: { x: 300, y: 205 } } }}>
      {(s, _rect, layout) => {
        const third = <Block n={3} name={s.found ? BLOCKS[2].name : undefined} kind={BLOCKS[2].kind} state={s.found ? 'found' : 'current'} />
        return (
          <Window title="AlgoBlock" className="algoblock-win">
            <div className="d3-body">
              <div className="d3-blocks">
                {layout === 'wide' && <Block n={1} {...BLOCKS[0]} state="found" />}
                {layout === 'wide' && <Block n={2} {...BLOCKS[1]} state="found" />}
                {third}
                {layout === 'wide' && <Block n={4} kind="조건" state="locked" />}
              </div>
              <div className="d3-chat">
                <div className="d3-thread">
                  <span className="d3-rest" data-target="rest" />
                  <div className="d3-msg d3-msg--tutor">
                    <Text wrap>{Q1}</Text>
                  </div>
                  <Collapse open={s.sent} reveal="drop" from="below">
                    <div className="d3-next">
                      <div className="d3-msg d3-msg--me">
                        <Text wrap>{ANSWER}</Text>
                      </div>
                    </div>
                  </Collapse>
                  {layout === 'wide' && (
                    <Collapse open={s.thinking}>
                      <div className="d3-next">
                        <Text className="d3-thinking">튜터가 생각하는 중…</Text>
                      </div>
                    </Collapse>
                  )}
                  {layout === 'wide' && (
                    <Collapse open={s.asked}>
                      <div className="d3-next">
                        <div className="d3-msg d3-msg--tutor">
                          <Stream text={Q2} count={s.words} />
                        </div>
                      </div>
                    </Collapse>
                  )}
                </div>
                <div className="d3-composer">
                  <Field value={s.draft} placeholder="생각나는 대로 적어 보세요. 몰라도 괜찮아요" focused={!s.sent} />
                  <div className="d3-send">
                    <Button variant="primary" data-target="send">보내기</Button>
                  </div>
                </div>
              </div>
            </div>
          </Window>
        )
      }}
    </Scene>
  )
}
