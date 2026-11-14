import { Button, Field, Roll, States, Text, Window, type Act } from '../../kit'
import { Scene } from '../scene'
import './connect.css'

// 6장 "AI 연결은 선택이에요". 칸에 쓰고, 단추를 누르면 그 자리에서 확정된다.
// 박자: API 키 칸을 눌러 키를 붙여 넣는다 → '키 넣기'를 누른다 → 칸 아래 줄이 '키를 넣었어요.'로 바뀌고
// 위쪽 연결 표시가 '연결 안 됨'에서 'Claude API 키'로 바뀐다. 한 번만 재생, 멈춘 그림은 연결된 장면.
// 진짜 글: AI 연결, 연결 안내 첫 문장, API 키, 키를 붙여 넣어요, 키 넣기, 키는 이 기기에만 저장해요, 키를 넣었어요,
// 연결 안 됨, Claude API 키, ChatGPT 로그인.

const KEY = 'my-claude-api-key'

type S = { key: string; focus: boolean; saved: boolean }

const initial: S = { key: '', focus: false, saved: false }
const poster: S = { key: KEY, focus: false, saved: true }

async function script(a: Act<S>) {
  await a.wait(800)
  a.mark('focus')
  await a.click({ at: 'key', x: 0.7, y: 0.5 })
  a.put({ focus: true })
  await a.wait(300)
  a.mark('type')
  await a.type('key', KEY, { interval: 40 })
  await a.wait(400)
  a.mark('save')
  await a.click({ at: 'save', x: 0.8, y: 0.64 })
  a.put({ focus: false, saved: true })
  await a.wait(3600)
}

export default function Connect() {
  return (
    <Scene name="d6" initial={initial} poster={poster} script={script} cursor={{ at: { wide: { x: 500, y: 250 }, compact: { x: 250, y: 290 } } }}>
      {(s) => (
        <Window title="AlgoBlock" className="algoblock-win">
          <div className="d6-body">
            <div className="d6-head">
              <Text className="d6-title">AI 연결</Text>
              <span className="d6-now" data-on={s.saved || undefined}>
                <span className="d6-dot" />
                <Roll variant="fade" align="end">{s.saved ? 'Claude API 키' : '연결 안 됨'}</Roll>
              </span>
            </div>
            <Text wrap className="d6-lead">연결하지 않아도 문제를 풀고 채점받을 수 있어요.</Text>
            <div className="d6-group">
              <div className="d6-key">
                <Field label="API 키" value={s.key} placeholder="키를 붙여 넣어요" password focused={s.focus} status={s.saved ? 'valid' : undefined} box={{ 'data-target': 'key', 'data-cursor': 'ibeam' }} />
                <Button data-target="save">키 넣기</Button>
              </div>
              <div className="d6-lane">
                <States
                  value={s.saved ? 'saved' : 'hint'}
                  align="start"
                  states={{
                    hint: <Text className="d6-msg">키는 이 기기에만 저장해요.</Text>,
                    saved: <Text className="d6-msg d6-msg--ok">키를 넣었어요.</Text>,
                  }}
                />
              </div>
            </div>
            <div className="d6-group d6-group--next">
              <Text className="d6-legend">ChatGPT 로그인</Text>
              <Text className="d6-msg">연결 안 됨</Text>
            </div>
          </div>
        </Window>
      )}
    </Scene>
  )
}
