// 여섯 장이 함께 쓰는 무대: 크기(안내 창 너비 660, 좁은 화면 358), 테마(앱이 정한 data-scheme을 따르고, 없으면 기기 설정), 한 번만 재생.
import { useEffect, useState } from 'react'
import { Stage, type StageProps } from '../kit'

const DARK = '(prefers-color-scheme: dark)'

export function useTheme(): 'light' | 'dark' {
  const root = document.documentElement
  const read = () => (root.dataset.scheme ? root.dataset.scheme === 'dark' : matchMedia(DARK).matches)
  const [dark, setDark] = useState(read)
  useEffect(() => {
    const media = matchMedia(DARK)
    const change = () => setDark(read())
    media.addEventListener('change', change)
    const watch = new MutationObserver(change)
    watch.observe(root, { attributes: true, attributeFilter: ['data-scheme'] })
    return () => {
      media.removeEventListener('change', change)
      watch.disconnect()
    }
  }, [])
  return dark ? 'dark' : 'light'
}

export const WIDE = { width: 660, height: 340 }
export const COMPACT = { below: 560, width: 358, height: 340 }

export function Scene<S extends object>({ name, ...props }: Omit<StageProps<S>, 'width' | 'height' | 'compact' | 'theme' | 'className' | 'play'> & { name: string }) {
  return <Stage {...WIDE} compact={COMPACT} theme={useTheme()} play="once" className={`algoblock ${name}`} {...props} />
}
