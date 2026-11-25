// 흐름 시험: 혼자 풀기의 해설 → 정답 코드에 문법 색이 칠해지고, 복사 단추가 정답 코드를 그대로 넣는다.
// 쓰는 법: node solution_code.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델·네트워크는 쓰지 않는다(해설은 기본 문제에 실린 글이다). 실패하면 <사진 폴더>에 화면 사진을 남기고 1로 끝난다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node solution_code.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

// 특정 문제에 묶이지 않게: 파이썬 풀이가 실린 기본 문제 가운데 처음과 마지막(주제·길이가 다르다)
const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const withPython = builtin.filter((p) => p.solutions && p.solutions.python && 'level' in p)
// 창 크기마다 다른 문제 하나(넓은 창, 좁은 창)
const RUNS = [[{ width: 1366, height: 689 }, withPython[0]], [{ width: 1093, height: 551 }, withPython[withPython.length - 1]]]

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
  await need('해설을 연다', async () => {
    // 해설 칸이 이미 열려 있지 않으면 연다. 다른 흐름이 같은 서버에서 이 문제를 통과시켰으면 '해설 보기', 아니면 '포기하고 해설 보기' → '그래도 해설 보기'
    if (await page.locator('#rail-sol').isVisible()) await page.locator('#rail-sol').click({ timeout: 3000 })
    if (await page.locator('#solo-box details.solution').count()) return // 해설이 이미 열려 있다
    const open = page.locator('#solo-open, #solo-force')
    await open.first().waitFor({ state: 'visible', timeout: 3000 })
    if (await page.locator('#solo-open').count()) await page.locator('#solo-open').click({ timeout: 3000 })
    else {
      await page.locator('#solo-force').click({ timeout: 3000 })
      await page.locator('#solo-force-yes').click({ timeout: 3000 })
    }
  })
  await need('풀이 해설과 정답 코드를 펼친다(통과한 문제는 접혀 있다)', async () => {
    const details = page.locator('#solo-box details.solution')
    await details.waitFor({ state: 'attached', timeout: 5000 })
    if (!(await details.evaluate((d) => d.open))) await details.locator('summary').click({ timeout: 3000 })
  })
  const code = page.locator('#solo-box details.solution .code-wrap pre.code')
  await need('정답 코드가 보인다', () => code.waitFor({ state: 'visible', timeout: 5000 }))
  await need('정답 코드에 문법 색이 있다', async () => {
    const painted = await code.locator('span[class^="t-"]').count()
    if (!painted) throw new Error('색을 칠한 글이 없다')
  })
  await need('색을 칠해도 글은 원래 코드와 같다', async () => {
    const text = await code.evaluate((pre) => pre.textContent)
    if (text !== problem.solutions.python.replace(/\s+$/, '')) throw new Error('글이 달라졌다')
  })
  await need('복사 단추가 정답 코드를 그대로 넣는다', async () => {
    // 시험 브라우저의 클립보드 권한과 상관없이 넣는 글을 본다
    await page.evaluate(() => { navigator.clipboard.writeText = async (t) => { window.__copied = t } })
    const copy = page.locator('#solo-box details.solution .code-wrap .copy')
    await copy.click({ timeout: 3000 })
    await page.waitForFunction(() => typeof window.__copied === 'string', null, { timeout: 3000 })
    const copied = await page.evaluate(() => window.__copied)
    if (copied !== problem.solutions.python.replace(/\s+$/, '')) throw new Error('복사한 글이 정답 코드와 다르다')
    if ((await copy.textContent()).trim() !== '복사했어요') throw new Error('복사했다는 표시가 없다')
  })
  await need('복사 단추가 코드 상자 안에 있다', async () => {
    const [box, btn] = await Promise.all([code.boundingBox(), page.locator('#solo-box details.solution .code-wrap .copy').boundingBox()])
    if (!box || !btn || btn.x < box.x || btn.x + btn.width > box.x + box.width + 1 || btn.y < box.y) throw new Error(`단추 자리 ${JSON.stringify(btn)} / 상자 ${JSON.stringify(box)}`)
  })

  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `solution_code-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag} ${problem.id}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag} ${problem.id}`)
  await page.close()
}
await browser.close()
process.exit(failed ? 1 : 0)
