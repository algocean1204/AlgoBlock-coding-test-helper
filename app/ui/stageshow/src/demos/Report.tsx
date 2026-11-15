import { Roll, Text, Window } from '../../kit'
import { Scene } from '../scene'
import './report.css'

// 5장 "학습 보고서로 약한 곳을 찾아요". 글이 말하는 모습(강한 주제와 더 공부할 주제가 함께 보인다)을 처음부터 멈춘 그림으로 보여 준다.
// 글에 없는 빈 상태("아직 약한 주제로 보이는 곳이 없어요")는 보이지 않는다.
// 진짜 글: 주제별 진행, 주제 이름, 강점·더 공부·진행 중, 더 공부할 주제, 시간 초과 까닭 문장, 다음에 풀 문제와 실제 문제 제목.

type Level = 'done' | 'tried' | 'none'

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
    <Scene name="d4" initial={{}}>
      {() => (
        <Window title="AlgoBlock" className="algoblock-win">
          <div className="d4-body">
            <Text className="d4-label">주제별 진행</Text>
            <div className="d4-rows">
              <Ladder name="해시" levels={['done', 'done', 'done', 'none', 'none']} state="strong" />
              <Ladder name="이분탐색" levels={['done', 'tried', 'none', 'none', 'none']} state="weak" />
              <Ladder name="스택/큐" levels={['done', 'none', 'none', 'none', 'none']} state="progress" />
            </div>
            <div className="d4-card" data-weak>
              <Text className="d4-card-title">더 공부할 주제</Text>
              <div className="d4-found">
                <div className="d4-why"><b>이분탐색</b>시간 초과가 2번 나왔어요. 입력 크기를 보고 방법을 고르는 연습이 필요해요.</div>
                <Text className="d4-next">다음에 풀 문제: 가격대로 매물 세기</Text>
              </div>
            </div>
          </div>
        </Window>
      )}
    </Scene>
  )
}
