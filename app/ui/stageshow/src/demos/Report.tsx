import { Collapse, Roll, Text, Window, type Act } from '../../kit'
import { Scene } from '../scene'
import './report.css'

// 4장 "학습 보고서로 약한 곳을 찾아요". 커서 없이, 천천히 겹치며 도착하고 결과가 머문다.
// 박자: 해시 3단계가 통과로 채워지고 '강점'이 된다 → 이분탐색 2단계가 틀린 채로 남고 '더 공부'가 된다
// → 비어 있던 '더 공부할 주제' 카드에 까닭과 다음에 풀 문제가 들어온다. 한 번만 재생, 멈춘 그림은 카드가 채워진 장면.
// 진짜 글: 주제별 진행, 주제 이름, 강점·더 공부·진행 중, 더 공부할 주제와 비었을 때의 안내문, 시간 초과 까닭 문장, 다음에 풀 문제와 실제 문제 제목.

type Level = 'done' | 'tried' | 'none'
type S = { step: number }

const initial: S = { step: 0 }
const poster: S = { step: 3 }

async function script(a: Act<S>) {
  await a.wait(1100)
  a.mark('strong')
  a.put({ step: 1 })
  await a.wait(1700)
  a.mark('weak')
  a.put({ step: 2 })
  await a.wait(1500)
  a.mark('card')
  a.put({ step: 3 })
  await a.wait(3800)
}

const STATE = { strong: '강점', weak: '더 공부', progress: '진행 중' } as const

function Ladder({ name, levels, state }: { name: string; levels: Level[]; state: keyof typeof STATE }) {
  return (
    <div className="d4-row">
      <Text className="d4-name">{name}</Text>
      <span className="d4-levels">
        {levels.map((level, i) => (
          <span key={i} className="d4-lv" data-level={level}>{i + 1}</span>
        ))}
      </span>
      <span className="d4-state" data-state={state}>
        <Roll variant="fade" align="end">{STATE[state]}</Roll>
      </span>
    </div>
  )
}

export default function Report() {
  return (
    <Scene name="d4" initial={initial} poster={poster} script={script}>
      {(s) => (
        <Window title="AlgoBlock" className="algoblock-win">
          <div className="d4-body">
            <Text className="d4-label">주제별 진행</Text>
            <div className="d4-rows">
              <Ladder name="해시" levels={['done', 'done', s.step >= 1 ? 'done' : 'none', 'none', 'none']} state={s.step >= 1 ? 'strong' : 'progress'} />
              <Ladder name="이분탐색" levels={['done', s.step >= 2 ? 'tried' : 'none', 'none', 'none', 'none']} state={s.step >= 2 ? 'weak' : 'progress'} />
              <Ladder name="스택/큐" levels={['done', 'none', 'none', 'none', 'none']} state="progress" />
            </div>
            <div className="d4-card" data-weak={s.step >= 3 || undefined}>
              <Text className="d4-card-title">더 공부할 주제</Text>
              <Collapse open={s.step < 3}>
                <Text wrap className="d4-empty">아직 약한 주제로 보이는 곳이 없어요. 제출이 쌓이면 여기에 나와요.</Text>
              </Collapse>
              <Collapse open={s.step >= 3}>
                <div className="d4-found">
                  <div className="d4-why"><b>이분탐색</b>시간 초과가 2번 나왔어요. 입력 크기를 보고 방법을 고르는 연습이 필요해요.</div>
                  <Text className="d4-next">다음에 풀 문제: 가격대로 매물 세기</Text>
                </div>
              </Collapse>
            </div>
          </div>
        </Window>
      )}
    </Scene>
  )
}
