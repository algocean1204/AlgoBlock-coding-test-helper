// 개발용 미리 보기: /?demo=0..5 (안내 여섯 장) 또는 /?demo=hero (README 그림). film.mjs가 이 쪽을 찍는다.
import { createRoot } from 'react-dom/client'
import { DEMOS } from './demos'
import { Hero } from './hero'
import './look.css'
import './preview.css'

const name = new URLSearchParams(location.search).get('demo') ?? '0'
const Demo = name === 'hero' ? Hero : DEMOS[Number(name)]
const host = document.getElementById('example')!
host.dataset.demo = name
if (Demo) createRoot(host).render(<Demo />) // 정적 그림을 쓰는 장(null)은 비워 둔다
