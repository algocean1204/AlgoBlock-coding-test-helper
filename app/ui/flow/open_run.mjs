// 흐름 시험: 기본 문제 열기 → 예시 실행 → 결과 보임.
// 쓰는 법: node open_run.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델·네트워크는 쓰지 않는다(예시 실행은 채점기만 돈다). 실패하면 <사진 폴더>에 화면 사진을 남기고 1로 끝난다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node open_run.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

// 기본 문제의 검증된 풀이로만 기대를 세운다(모델이 쓴 기대값을 쓰지 않는다). 특정 문제에 묶이지 않게 첫 파이썬 문제를 쓴다.
const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const problem = builtin.find((p) => p.solutions && p.solutions.python)

const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const browser = await launch()
let failed = 0

for (const viewport of VIEWPORTS) {
  const tag = `${viewport.width}x${viewport.height}`
  const page = await browser.newPage({ viewport })
  const problems = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`) })
  // 서버 밖으로 나가는 요청은 막고 실패로 적는다(외부 주소로 새는 것이 없어야 한다)
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (url.startsWith(`${new URL(base).origin}/`) || /^(data|blob|about):/.test(url)) return route.continue()
    problems.push(`external: ${url}`)
    return route.abort()
  })
  // 한 걸음이 실패하면 뒤 걸음은 기다리지 않는다(앞이 막히면 뒤도 막혀 시간만 쓴다)
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }

  await page.goto(`${base}/#/p/${problem.id}`)
  // 1. 문제 열림
  await need('문제 제목이 보인다', () => page.waitForFunction((t) => document.getElementById('p-title')?.textContent.trim() === t, problem.title, { timeout: 5000 }))
  // 좁은 창(1180px 미만)에서는 문제 글이 위 띠로 접혀 있다. 사용자처럼 '문제 펼치기'로 읽고 다시 접는다
  const peek = page.locator('#problem-peek')
  const narrow = await peek.isVisible()
  await need('문제를 펼친다(좁은 창)', async () => { if (narrow) await peek.click() })
  await need('문제 본문이 보인다', () => page.locator('#p-text').waitFor({ state: 'visible', timeout: 2000 }))
  await need('문제를 다시 접는다(좁은 창)', async () => { if (narrow) await peek.click() })
  await need('코드 칸이 보인다(방식 탭이 없는 직접 쓰기여도)', async () => { await page.locator('#code').waitFor({ state: 'visible', timeout: 2000 }) })
  // 2. 풀이를 넣고 예시 실행
  await need('코드를 넣는다', async () => { await page.locator('#code').fill(problem.solutions.python) })
  await need('예시 실행 단추가 눌린다', async () => {
    const run = page.locator('#run')
    await run.waitFor({ state: 'visible', timeout: 2000 })
    if (await run.isDisabled()) throw new Error('모델 없이도 예시 실행은 잠기면 안 된다')
    await run.click()
  })
  // 3. 결과 보임
  await need('결과 칸이 보인다', () => page.locator('#result').waitFor({ state: 'visible', timeout: 15000 }))
  await need('예시 통과 글이 있다', () => page.waitForFunction(() => /예시 통과/.test(document.querySelector('#result .verdict.pass')?.textContent || ''), null, { timeout: 15000 }))
  await need('예시 통과 글이 화면 안에 보인다', async () => {
    const box = await page.locator('#result .verdict.pass').boundingBox()
    const height = await page.evaluate(() => window.innerHeight)
    if (!box || box.y < 0 || box.y + box.height > height) throw new Error(`화면 밖(${JSON.stringify(box)}, 높이 ${height})`)
  })
  await need('테스트별 결과가 들어 있다', async () => { if (!(await page.locator('#result details.case-fold').count())) throw new Error('없음') })
  await need('결과가 뷰포트 안에서 닿는다(가로 넘침 없음)', async () => {
    const wide = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)
    if (wide) throw new Error('가로로 넘친다')
    const box = await page.locator('#result').boundingBox()
    if (!box || box.width < 50) throw new Error('결과 칸이 너무 좁다')
  })
  await need('오류 알림이 없다', async () => { if (await page.locator('#result .note.error').count()) throw new Error('결과에 오류 알림') })
  // 4. 성능 수치: window.__ab.perf는 나중 PR에서 생긴다. 없으면 건너뛴다
  const perf = await page.evaluate(() => (window.__ab && window.__ab.perf ? window.__ab.perf : null))
  if (perf) {
    const limit = { press_to_paint_ms: 200, send_to_clear_ms: 100, rerender_ms: 50, long_tasks: 2 } // 설계의 CI 여유 값
    for (const [k, max] of Object.entries(limit)) if (typeof perf[k] === 'number' && perf[k] > max) problems.push(`perf ${k}=${perf[k]} > ${max}`)
  } else console.log(`${tag}: perf 건너뜀(window.__ab.perf 없음)`)

  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `open_run-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.close()
}
await browser.close()
process.exit(failed ? 1 : 0)
