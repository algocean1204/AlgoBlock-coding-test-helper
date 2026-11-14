// 앱이 불러 쓰는 입구. app.js가 안내를 열 때 tour-demos.js를 불러오고 AlgoBlockTourDemos.show(칸, 장 번호)를 부른다.
import { createRoot, type Root } from 'react-dom/client'
import { DEMOS } from './demos'
import './look.css'

const roots = new WeakMap<Element, Root>()
let run = 0

/** el 안에 index번째 장의 데모를 처음부터 틀어 준다. 같은 장을 다시 부르면 처음부터 다시 튼다. */
export function show(el: HTMLElement, index: number) {
  const Demo = DEMOS[index]
  if (!Demo) return
  let root = roots.get(el)
  if (!root) roots.set(el, (root = createRoot(el)))
  root.render(<Demo key={`${index}:${++run}`} />)
}

/** 안내를 닫을 때: 데모를 내린다. */
export function clear(el: HTMLElement) {
  roots.get(el)?.unmount()
  roots.delete(el)
}

/** 그 장에 움직이는 데모가 있는가(없으면 app.js가 정적 그림을 보인다). */
export function has(index: number) {
  return !!DEMOS[index]
}

export const count = DEMOS.length
