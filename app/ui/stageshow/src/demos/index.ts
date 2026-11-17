import type { ComponentType } from 'react'
import Report from './Report'
import Connect from './Connect'

/** 안내 여섯 장의 데모. 순서는 app.js의 TOUR와 같다. null인 장은 index.html의 정적 그림(새 화면: 홈의 오늘 할 일, 어떻게 풀까요, 결과 뒤 다음 할 일, 세 걸음 넣기)을 쓴다.
    새 화면으로 그린 데모를 만들면 그 자리에 넣는다. Connect는 지금 연결(conn)을 props로 받는다 */
export const DEMOS: (ComponentType<{ conn?: string }> | null)[] = [null, null, null, null, Report, Connect]
