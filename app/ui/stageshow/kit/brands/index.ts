/** 이 프로젝트는 다른 회사 로고를 쓰지 않아 원본 키트의 로고 그림을 싣지 않았다(빈 등록부). */
export type BrandAsset = {
  name: string
  category: 'Payments' | 'Banks' | 'Apps' | 'Crypto'
  light: string
  dark: string
  tileArtwork?: string
  tileBackground?: string
  proportion: number
  scale: number
}

export const brandMarks: Record<string, BrandAsset> = {}

export type BrandName = string
