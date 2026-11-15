import { Button, Field, Roll, Text, Window } from '../../kit'
import { Scene } from '../scene'
import './connect.css'

// 6장 "AI 연결은 선택이에요". 멈춘 그림이고, 위쪽 연결 표시는 지금 실제 연결(conn)을 따른다. 글의 끝 문장과 같은 상태다.
// 진짜 글(설정 → AI 연결): 설정 · AI 연결, 연결 안내 첫 문장, API 키, 키를 붙여 넣어요, 키 넣기, 키는 이 기기에만 저장해요, AI 연결 안 됨, 이미 내는 요금제로 쓰기, ChatGPT로 로그인.

export default function Connect({ conn = '' }: { conn?: string }) {
  return (
    <Scene name="d6" initial={{}}>
      {() => (
        <Window title="AlgoBlock" className="algoblock-win">
          <div className="d6-body">
            <div className="d6-head">
              <Text className="d6-title">설정 · AI 연결</Text>
              <span className="d6-now" data-on={conn ? true : undefined}>
                <span className="d6-dot" />
                <Roll variant="fade" align="end">{conn || 'AI 연결 안 됨'}</Roll>
              </span>
            </div>
            <Text wrap className="d6-lead">연결하지 않아도 문제를 풀고 채점받을 수 있어요.</Text>
            <div className="d6-group">
              <div className="d6-key">
                <Field label="API 키" value="" placeholder="키를 붙여 넣어요" password />
                <Button>키 넣기</Button>
              </div>
              <div className="d6-lane">
                <Text className="d6-msg">키는 이 기기에만 저장해요.</Text>
              </div>
            </div>
            <div className="d6-group d6-group--next">
              <Text className="d6-legend">이미 내는 요금제로 쓰기</Text>
              <Button>ChatGPT로 로그인</Button>
            </div>
          </div>
        </Window>
      )}
    </Scene>
  )
}
