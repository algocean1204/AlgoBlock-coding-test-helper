// 흐름 시험: 찍은 출력과 표준 오류를 넣은 풀이로 예시 실행 → 테스트마다 '터미널 출력'이 돌려준 값과 따로 보이고, 통과한 예시에 '오류'가 없으며, 복사 단추가 그 글을 넣는다.
// 쓰는 법: node terminal_output.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델·네트워크는 쓰지 않는다(예시 실행은 채점기만 돈다). 실패하면 <사진 폴더>에 화면 사진을 남기고 1로 끝난다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node terminal_output.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

// 특정 문제에 묶이지 않게: 파이썬 풀이가 실린 함수 방식 기본 문제 가운데 둘(창 크기마다 하나). 검증된 풀이에 찍는 줄만 더한다
const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const usable = builtin.filter((p) => 'level' in p && p.solutions && /^def solution\(.*\):\n/m.test(p.solutions.python || ''))
const loud = (code) => 'import sys\n' + code.replace(/^(def solution\(.*\):\n)/m, "$1    print('seen here')\n    print('debug here', file=sys.stderr)\n")
const RUNS = [[{ width: 1366, height: 689 }, usable[1]], [{ width: 1093, height: 551 }, usable[usable.length - 2]]]

const browser = await launch()
let failed = 0

for (const [viewport, problem] of RUNS) {
  const tag = `${viewport.width}x${viewport.height}`
  const page = await browser.newPage({ viewport })
  const problems = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`) })
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (url.startsWith(`${new URL(base).origin}/`) || /^(data|blob|about):/.test(url)) return route.continue()
    problems.push(`external: ${url}`)
    return route.abort()
  })
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }

  await page.goto(`${base}/#/p/${problem.id}`)
  await need('문제 제목이 보인다', () => page.waitForFunction((t) => document.getElementById('p-title')?.textContent.trim() === t, problem.title, { timeout: 5000 }))
  await need('찍는 줄을 넣은 풀이로 예시 실행', async () => {
    await page.locator('#code').fill(loud(problem.solutions.python), { timeout: 3000 })
    await page.locator('#run').click({ timeout: 3000 })
    await page.waitForFunction(() => /예시 통과/.test(document.querySelector('#result .verdict.pass')?.textContent || ''), null, { timeout: 20000 })
  })
  await need('테스트별 결과를 펼친다', async () => {
    const fold = page.locator('#result details.case-fold')
    if (!(await fold.evaluate((d) => d.open))) await fold.locator(':scope > summary').click({ timeout: 3000 }) // 안쪽 예시의 summary는 빼고
    await page.evaluate(() => document.querySelectorAll('#result details.case').forEach((d) => { d.open = true }))
  })
  await need('예시마다 터미널 출력이 돌려준 값과 따로 보인다', async () => {
    const rows = await page.evaluate(() => [...document.querySelectorAll('#result details.case')].map((d) => {
      const terms = [...d.querySelectorAll('dt')].map((dt) => dt.textContent.trim())
      const value = [...d.querySelectorAll('dt')].find((dt) => dt.textContent.trim() === '내 코드의 결과')?.nextElementSibling?.textContent || ''
      const term = d.querySelector('pre.term')
      return { terms, value, out: term?.textContent || '', err: term?.querySelector('.term-err')?.textContent || '' }
    }))
    if (!rows.length) throw new Error('예시가 없다')
    for (const row of rows) {
      if (row.terms.includes('오류')) throw new Error(`통과한 예시에 '오류'가 있다: ${JSON.stringify(row)}`)
      if (/seen here|debug here/.test(row.value)) throw new Error(`돌려준 값에 찍은 줄이 섞였다: ${row.value}`)
      if (!row.out.startsWith('seen here') || row.err !== 'debug here') throw new Error(`터미널 출력이 다르다: ${JSON.stringify(row)}`)
    }
  })
  await need('복사 단추가 터미널 글을 넣는다', async () => {
    await page.evaluate(() => { navigator.clipboard.writeText = async (t) => { window.__copied = t } })
    const box = page.locator('#result details.case').first().locator('.code-wrap')
    await box.locator('.copy').click({ timeout: 3000 })
    await page.waitForFunction(() => typeof window.__copied === 'string', null, { timeout: 3000 })
    const copied = await page.evaluate(() => window.__copied)
    if (copied !== 'seen here\ndebug here') throw new Error(`복사한 글: ${JSON.stringify(copied)}`)
  })
  await need('결과가 가로로 넘치지 않는다', async () => {
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)) throw new Error('가로로 넘친다')
  })

  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `terminal_output-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag} ${problem.id}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag} ${problem.id}`)
  await page.close()
}
await browser.close()
process.exit(failed ? 1 : 0)
