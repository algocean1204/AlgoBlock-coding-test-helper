// 흐름 시험: 두 튜터 방식에서 대화 없이 지금 블록 코드 칸에 코드를 쓰고 '블록 코드 확인'으로 다음 블록을 연다.
// 쓰는 법: node chair_write.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 가짜 모델의 응답 대본은 같은 이름의 chair_write.json이 준다(test_flow.py가 읽어 건다. 뷰포트마다 쓰므로 두 벌씩 적고, 남으면 실패다).
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node chair_write.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

// 기본 문제의 미리 만든 블록 계획(참고 코드)에서 블록 코드를 꺼낸다. 특정 문제에 묶이지 않게 계획이 둘 이상인 첫 파이썬 문제를 쓴다.
const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const planned = (p) => p.language === 'python' && p.ready && p.ready.plan && p.ready.plan.blocks.length > 1
const problem = builtin.find(planned)
// 근거 질문은 생각할 거리가 있는 블록(반복·조건·분기)에서만 나온다: 말로 찾는 흐름은 첫 블록이 그런 문제를 쓴다
const thinking = builtin.find((p) => planned(p) && ['loop', 'condition', 'branch'].includes(p.ready.plan.blocks[0].kind))
// 튜터 코드가 만드는 변수 이름: 의자에서 찾기 전 블록의 확인 말에 나오면 답이 샌다
const HIDDEN = [...new Set(problem.ready.plan.blocks.flatMap((b) => [...b.reference.matchAll(/^\s*([A-Za-z_]\w*)\s*=/gm)].map((m) => m[1])))]
const WRITE = /코드 칸에 코드로 적고/
const BASIS = /문제 글에 있나요/

const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const browser = await launch()
let failed = 0

/** 한 흐름(방식 × 뷰포트)을 새 화면에서 돌린다. 한 걸음이 실패하면 뒤 걸음은 기다리지 않는다. */
async function flow(name, viewport, steps, problem) {
  const tag = `${name}-${viewport.width}x${viewport.height}`
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
  const reset = await page.request.post(`${base}/api/reset`, { data: { id: problem.id } })
  if (!reset.ok()) problems.push(`reset ${reset.status()}`)
  await page.goto(`${base}/#/p/${problem.id}`)
  const t = {
    page, need,
    blocks: () => page.locator('#blocks > li'),
    current: () => page.locator('#blocks > li.block[aria-current="step"]'),
    tutorSays: () => page.locator('#chat-log .msg.tutor'),
    pick: async (way) => {
      const narrow = await page.locator('#problem-peek').isVisible()
      if (narrow) { await page.locator('#problem-peek').click(); await page.locator('#problem-peek').click() } // 좁은 창: 접힌 문제 띠를 한 번 폈다 접는다
      await page.locator(`#way-tabs [data-way="${way}"]`).click() // 탭 한 번으로 바로 시작한다(시작 단추가 없다)
      await page.locator('#chat-log .msg.tutor').first().waitFor({ state: 'visible', timeout: 10000 })
    },
    write: async (code) => { await t.current().locator('textarea.codey').fill(code) },
    check: async () => { await t.current().locator('[data-check]').click() },
    // 보낸 뒤 튜터의 답이 다 올 때까지 기다린다(기다리는 동안 보낸 말은 화면이 받지 않는다)
    say: async (text) => {
      const before = await page.locator('#chat-log .msg.tutor:not(.pending)').count()
      await page.locator('#say').fill(text)
      await page.locator('#send').click()
      await page.waitForFunction((n) => !document.querySelector('#chat-log .msg.tutor.pending') && document.querySelectorAll('#chat-log .msg.tutor:not(.pending)').length > n, before, { timeout: 10000 })
    },
    lastSaid: () => page.locator('#chat-log .msg.tutor:not(.pending)').last().innerText(),
  }
  await steps(t)
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `chair_write-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.close()
}

/** 코드 칸이 지금 블록에 있고 두 단추가 보인다: 틀린 코드를 확인받아 실패해도 갇히지 않는다. */
async function stuckOptions(t) {
  const { need } = t
  await need('지금 블록에 코드 칸이 있다', () => t.current().locator('textarea.codey').waitFor({ state: 'visible', timeout: 3000 }))
  await need('틀린 코드로 블록 코드 확인이 눌린다', async () => { await t.write('x = 1'); await t.check() })
  await need('‘이대로 넘어가기’가 지금 블록에 보인다', () => t.current().locator('[data-skip]').waitFor({ state: 'visible', timeout: 10000 }))
  await need('‘끝까지 내 방식으로 쓰기’가 지금 블록에 보인다', () => t.current().locator('[data-own]').waitFor({ state: 'visible', timeout: 3000 }))
}

/** 맞는 코드를 쓰고 확인하면 통과해 다음 블록의 첫 질문(말)이 보이고, 그 전에는 다음 블록이 잠겨 있다. */
async function passOpensNext(t, first) {
  const { need, page } = t
  await need('통과 전에는 다음 블록이 잠겨 있다', async () => { if (!(await t.blocks().nth(1).evaluate((el) => el.classList.contains('is-locked')))) throw new Error('잠기지 않았다') })
  const before = await t.tutorSays().count().catch(() => 0)
  await need('맞는 코드로 블록 코드 확인이 눌린다', async () => { await t.write(first); await t.check() })
  await need('통과해 다음 블록이 열린다', () => page.waitForFunction(() => !document.querySelectorAll('#blocks > li')[1]?.classList.contains('is-locked'), null, { timeout: 15000 }))
  await need('다음 블록의 첫 질문이 대화에 더해진다', () => page.waitForFunction((n) => document.querySelectorAll('#chat-log .msg.tutor').length > n, before, { timeout: 5000 }))
}

for (const viewport of VIEWPORTS) {
  const first = problem.ready.plan.blocks[0].reference
  await flow('chair-write', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('찾기 전 블록의 이름이 가려져 있다', async () => { if ((await t.current().locator('.block-name').innerText()).trim() !== '지금 찾는 블록') throw new Error('이름이 보인다') })
    await need('‘블록은 찾는 대로 열려요’ 안내가 없다', async () => { if (/찾는 대로/.test(await page.locator('#blocks-note').innerText())) throw new Error('안내가 남아 있다') })
    await stuckOptions(t)
    await need('결과 줄과 튜터의 말에 튜터 코드의 이름이 없다', async () => {
      const said = `${await t.current().locator('.block-result').innerText()}\n${await t.lastSaid()}`
      const told = HIDDEN.filter((n) => new RegExp(`\\b${n}\\b`).test(said))
      if (told.length) throw new Error(told.join(', '))
    })
    await need('‘끝까지 내 방식으로 쓰기’는 먼저 묻는다', async () => {
      await t.current().locator('[data-own]').click()
      await t.current().locator('[data-own-no]').click()
      await t.current().locator('[data-own]').waitFor({ state: 'visible', timeout: 3000 })
    })
    await passOpensNext(t, first)
  }, problem)
  await flow('chair-say', viewport, async (t) => {
    const { need } = t
    const first = thinking.ready.plan.blocks[0].reference
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('내 생각을 말한다', () => t.say('값을 하나씩 보면서 조건에 맞는 것만 골라요'))
    await need('근거를 묻는 말이 온다', async () => { if (!BASIS.test(await t.lastSaid())) throw new Error('근거 질문이 아니다') })
    await need('근거를 말한다', () => t.say('문제 글에 그렇게 적혀 있어요'))
    await need('코드로 적으라는 말이 온다', async () => { if (!WRITE.test(await t.lastSaid())) throw new Error('코드로 적으라는 말이 아니다') })
    await need('그 블록의 이름이 드러난다', async () => { if (/지금 찾는 블록/.test(await t.current().locator('.block-name').innerText())) throw new Error('이름이 가려진 채다') })
    await need('다음 블록은 말로 열리지 않는다', async () => { if (!(await t.blocks().nth(1).evaluate((el) => el.classList.contains('is-locked')))) throw new Error('다음 블록이 열렸다') })
    await need('주 단추가 ‘블록 코드 확인’이다', async () => {
      const main = t.current().locator('[data-check].primary')
      await main.waitFor({ state: 'visible', timeout: 3000 })
      if (!/블록 코드 확인/.test(await main.innerText())) throw new Error('다른 글')
    })
    await need('그 블록 칸에 쓰고 확인하면 통과한다', async () => { await t.write(first); await t.check(); await t.page.waitForFunction(() => !document.querySelectorAll('#blocks > li')[1]?.classList.contains('is-locked'), null, { timeout: 15000 }) })
  }, thinking)
  await flow('guide-write', viewport, async (t) => {
    const { need } = t
    await need('튜터와 차례로를 시작한다', () => t.pick('guide'))
    await stuckOptions(t)
    await passOpensNext(t, first)
  }, problem)
}
await browser.close()
process.exit(failed ? 1 : 0)
