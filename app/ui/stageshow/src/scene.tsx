// 여섯 장이 함께 쓰는 무대: 크기(안내 창 너비 660, 좁은 화면 358), 테마(기기 설정을 따름), 한 번만 재생.
import { useEffect, useState } from 'react'
import { Stage, type StageProps } from '../kit'

const DARK = '(prefers-color-scheme: dark)'

export function useTheme(): 'light' | 'dark' {
  const [dark, setDark] = useState(() => matchMedia(DARK).matches)
  useEffect(() => {
    const media = matchMedia(DARK)
    const change = () => setDark(media.matches)
    media.addEventListener('change', change)
    return () => media.removeEventListener('change', change)
  }, [])
  return dark ? 'dark' : 'light'
}

export const WIDE = { width: 660, height: 340 }
export const COMPACT = { below: 560, width: 358, height: 340 }

export function Scene<S extends object>({ name, ...props }: Omit<StageProps<S>, 'width' | 'height' | 'compact' | 'theme' | 'className' | 'play'> & { name: string }) {
  return <Stage {...WIDE} compact={COMPACT} theme={useTheme()} play="once" className={`algoblock ${name}`} {...props} />
}
