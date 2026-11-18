// 흐름 시험: 내 문제 넣기 한 화면 — 붙여 넣기 → 감지 → 두 칸 미리보기(문제부 / 입출력부) → 등록.
// 쓰는 법: node intake.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 서버는 키가 없고 모델은 부르지 않는다. 모델이 끼는 길(문제 밖 줄, 늦게 온 결과, 문제 아님)은 /api/problems/detect 응답을 고쳐 끼워 본다.
// 시험 글은 이 시험을 위해 새로 지은 문제다. 실패하면 <사진 폴더>에 화면 사진을 남기고 1로 끝난다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node intake.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const T = '\t'
const LINES = [
  '조명 켜기 횟수', '',
  '문제 설명',
  '복도에 일렬로 놓인 조명의 상태가 배열 lamps로 주어집니다. 켜진 조명은 1, 꺼진 조명은 0입니다.',
  '연속으로 m개 이상 켜진 구간마다 점검표에 한 줄을 적습니다. 구간이 길어도 한 줄만 적습니다.',
  '적어야 할 줄의 수를 return 하도록 solution 함수를 완성해 주세요.', '',
  '제한사항',
  '1 ≤ lamps의 길이 ≤ 10^5',
  'lamps의 원소는 0 또는 1입니다.',
  '1 ≤ m ≤ 1,000', '',
  '입출력 예',
  `lamps${T}m${T}result`,
  `[1, 1, 0, 1, 1, 1]${T}2${T}2`,
  `[1, 0, 1, 0]${T}2${T}0`,
  `[1, 1, 1, 1]${T}4${T}1`, '',
  '입출력 예 설명',
  '입출력 예 #1', '앞의 두 칸과 뒤의 세 칸이 각각 2칸 이상 켜져 있어 두 줄을 적습니다.',
  '입출력 예 #2', '2칸 이상 이어진 구간이 없어 0을 return 합니다.',
  '입출력 예 #3', '네 칸이 모두 이어져 한 줄을 적습니다.',
]
const SOLUTION = 'def solution(lamps, m):\n    count = run = 0\n    for x in list(lamps) + [0]:\n        if x:\n            run += 1\n        else:\n            if run >= m:\n                count += 1\n            run = 0\n    return count\n'
const NOISE = ['댓글 3개 · 공유 · 신고', '추천 문제 더 보기 · 인기 순위']
// 서버 하나를 여러 상황이 같이 쓰므로 같은 글을 두 번 등록하지 않게 상황·뷰포트마다 끝 줄에 표를 단다
const seeded = (lines, seed) => [...lines.slice(0, -1), `${lines.at(-1)} (${seed})`]
const plainOf = (seed) => seeded(LINES, seed).join('\n')
const noisyOf = (seed) => seeded([...LINES.slice(0, 22), ...NOISE, ...LINES.slice(22)], seed).join('\n')

// 웹 페이지에서 복사한 것: 메뉴·머리글·옆 칸·바닥글이 섞이고 위첨자는 <sup>이다. plain은 그 글자를 그대로 이은 것
const HTML = `<nav>홈 · 문제 목록 · 순위</nav><header>로그인 · 가입</header><article><h1>조명 켜기 횟수</h1><h2>문제 설명</h2>
<p>복도에 일렬로 놓인 조명의 상태가 배열 lamps로 주어집니다. 켜진 조명은 1, 꺼진 조명은 0입니다.</p>
<p>연속으로 m개 이상 켜진 구간마다 점검표에 한 줄을 적습니다. 구간이 길어도 한 줄만 적습니다.</p>
<p>적어야 할 줄의 수를 return 하도록 solution 함수를 완성해 주세요.</p>
<h2>제한사항</h2><ul><li>1 ≤ lamps의 길이 ≤ 10<sup>5</sup></li><li>lamps의 원소는 0 또는 1입니다.</li><li>1 ≤ m ≤ 1,000</li></ul>
<h2>입출력 예</h2><table><tr><th>lamps</th><th>m</th><th>result</th></tr>
<tr><td>[1, 1, 0, 1, 1, 1]</td><td>2</td><td>2</td></tr><tr><td>[1, 0, 1, 0]</td><td>2</td><td>0</td></tr><tr><td>[1, 1, 1, 1]</td><td>4</td><td>1</td></tr></table></article>
<aside>인기 문제 추천 · 광고 문의</aside><footer>© 예시 서비스 · 이용 약관</footer>`
const HTML_PLAIN = () => `홈 · 문제 목록 · 순위\n로그인 · 가입\n${plainOf('html').replace('10^5', '105')}\n인기 문제 추천 · 광고 문의\n© 예시 서비스 · 이용 약관`
const HTML_BAD = ['홈 · 문제 목록', '로그인 · 가입', '인기 문제 추천', '광고 문의', '이용 약관']

const MATH = ['수열 합', '', '문제 설명', '정수 수열 A_i가 주어집니다. $a_i$의 합 $S$를 구합니다. max_count와 min_count는 이름일 뿐입니다.', '$$\\sum_{i=1}^{n} a_i$$',
  '변수 이름은 `snake_case`처럼 씁니다.', '', '제한사항', '1 ≤ N ≤ 10^5', '1 ≤ A_i ≤ 10^9', '', '예제 입력 1', '3', '1 2 3', '', '예제 출력 1', '6'].join('\n')
const MONEY = '간식 하나는 $5입니다. 두 개는 $10입니다.'
const EVIL = '<img src=x onerror="window.__xss=1"> [링크](javascript:window.__xss=1)\n1 ≤ N ≤ 5\n예제 입력 1\n1\n예제 출력 1\n1'
const NOT_PROBLEM = '오늘 점심은 김치찌개였다. 국물이 시원했고 밥을 두 공기 먹었다. 후식은 과일이었다.'

const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const browser = await launch()
let failed = 0

const sleep = (ms) => new Promise((done) => setTimeout(done, ms))
const sameSet = (a, b) => a.length === b.length && a.every((x) => b.includes(x))
// 연결된 것처럼 보이게(모델을 부르는 길이 열린다. 서버는 키가 없어 실제 모델은 어디서도 불리지 않는다)
const connect = (page) => page.route('**/api/accounts', async (route) => {
  const res = await route.fetch(), data = await res.json()
  await route.fulfill({ response: res, json: { ...data, connected: true, client: 'cli' } })
})
// 감지 응답을 고쳐 끼운다: patch(data, body, calls) → 모델이 끼었을 때의 응답. fast 요청은 그대로 둘 수도 있다
const patchDetect = (page, calls, patch) => page.route('**/api/problems/detect', async (route) => {
  const body = JSON.parse(route.request().postData() || '{}')
  calls.push(body)
  const res = await route.fetch(), data = await res.json()
  await patch(data, body)
  await route.fulfill({ response: res, json: data })
})

/** 한 상황을 새 화면에서 돌린다. setup(page, rec)은 화면을 열기 전, fn(page, rec, need, seed)는 연 뒤. rec.posts는 서버로 간 POST 요청({path, body}) */
async function scenario(viewport, name, fn, setup) {
  const tag = `${viewport.width}x${viewport.height}`
  const page = await browser.newPage({ viewport })
  const problems = [], posts = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`) })
  page.on('request', (r) => { if (r.method() === 'POST' && r.url().includes('/api/')) { let body = null; try { body = JSON.parse(r.postData() || 'null') } catch {} posts.push({ path: new URL(r.url()).pathname, body }) } })
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (url.startsWith(`${new URL(base).origin}/`) || /^(data|blob|about):/.test(url)) return route.fallback()
    problems.push(`external: ${url}`)
    return route.abort()
  })
  let stuck = false
  const need = async (what, step) => { if (stuck) return; try { await step() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }
  const seed = `${name}-${tag}`
  const rec = { posts }
  if (setup) await setup(page, rec) // 연결 흉내와 감지 응답 고치기는 화면을 열기 전에 건다(화면이 처음부터 그 상태를 본다)
  await need('내 문제 넣기 화면이 열린다', async () => {
    await page.goto(`${base}/#/new`)
    await page.locator('#new-text').waitFor({ state: 'visible', timeout: 3000 })
  })
  await fn(page, rec, need, seed)
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `intake-${name}-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${name} ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${name} ${tag}`)
  await page.close()
}

const must = (cond, msg) => { if (!cond) throw new Error(msg) }
const text = (page, sel) => page.locator(sel).innerText()
const html = (page, sel) => page.locator(sel).innerHTML()
const count = (page, sel) => page.locator(sel).count()
const cards = (page) => count(page, '#case-rows .case-row')
// 고칠 수 있는 케이스 칸의 수(읽기 전용이거나 숨은 칸은 세지 않는다)
const editable = (page) => page.evaluate(() => [...document.querySelectorAll('#case-rows .case-val')].filter((el) => !el.readOnly && !el.disabled && el.getClientRects().length).length)
const waitCards = (page, n) => page.waitForFunction((k) => document.querySelectorAll('#case-rows .case-row').length === k, n, { timeout: 4000 })
const waitLine = (page, re) => page.waitForFunction((src) => { const el = document.getElementById('detect-line'); return !!el && !el.hidden && el.getClientRects().length > 0 && new RegExp(src).test(el.textContent) }, re.source, { timeout: 4000 })

for (const viewport of VIEWPORTS) {
  // 1. 한 화면: 붙여 넣기 → 감지 → 두 칸 → 등록 → 풀이 화면에서 예시 채점(키 없이)
  await scenario(viewport, 'flow', async (page, rec, need, seed) => {
    await need('걸음 표시와 3걸음 요약이 없다', async () => {
      for (const sel of ['#wsteps', '#wstep-title', '#new-next', '#new-back', '#new-summary', '[data-wstep]', '.wsteps']) must((await count(page, sel)) === 0, `${sel}이 남아 있다`)
      must(!(await page.locator('#new-form').getAttribute('data-step')), '#new-form에 data-step이 남아 있다')
    })
    await need('붙여 넣기 전에도 감지 줄·두 칸 자리가 화면 안에 틀려 보이지 않는다', async () => { must(!(await page.locator('#detect-line').isVisible()), '#detect-line이 글이 없는데 보인다') })
    await need('글을 넣으면 감지가 돌아 예시 카드 3개가 스스로 찬다(단추 없이)', async () => {
      await page.locator('#new-text').fill(plainOf(seed))
      await waitLine(page, /예시 3개/)
      await waitCards(page, 3)
      must((await page.locator('#new-title').inputValue()) === '조명 켜기 횟수', `제목이 ${await page.locator('#new-title').inputValue()}`)
      must(!(await page.locator('#case-fill').isVisible()), '‘입출력 예에서 채우기’ 단추를 눌러야 하면 안 된다')
    })
    await need('두 칸(문제부 / 입출력부)이 보이고 나뉘어 있다', async () => {
      for (const sel of ['#intake-problem', '#intake-io', '#preview']) await page.locator(sel).waitFor({ state: 'visible', timeout: 2000 })
      const problem = await text(page, '#intake-problem'), io = await text(page, '#intake-io')
      must(/복도에 일렬로/.test(problem) && /제한사항/.test(problem), '문제부에 설명과 구역 제목이 없다')
      must(!/\[1, 1, 0, 1, 1, 1\]/.test(problem), '문제부에 입출력 예가 섞여 있다')
      must(/\[1, 1, 0, 1, 1, 1\]/.test(io), '입출력부에 예시가 없다')
      must(await page.locator('#raw-edit').isVisible(), '[원문 고치기](#raw-edit)가 없다')
    })
    await need('평문 10^5가 미리보기에서 105가 되지 않는다', async () => {
      const out = await html(page, '#preview')
      must(/10\^\{?5\}?|10<sup[^>]*>\s*5\s*<\/sup>|10<\/span>[^]*?msupsub/.test(out), `10^5의 뜻이 사라졌다: ${out.slice(0, 200)}`)
    })
    await need('예시 카드는 읽기 전용이고 [고치기]로 고칠 수 있다', async () => {
      must((await editable(page)) === 0, '고치기 전에 고칠 수 있는 칸이 있다')
      await page.locator('#case-edit').click()
      must((await editable(page)) > 0, '[고치기](#case-edit) 뒤에도 고칠 수 없다')
    })
    await need('화면 안에서 깨지지 않는다(가로 넘침 없음, 두 칸·등록 단추가 닿는다)', async () => {
      must(!(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)), '가로로 넘친다')
      const vw = viewport.width, vh = viewport.height
      for (const sel of ['#intake-problem', '#intake-io', '#new-submit']) {
        await page.locator(sel).scrollIntoViewIfNeeded()
        const box = await page.locator(sel).boundingBox()
        must(box && box.x >= -1 && box.x + box.width <= vw + 1 && box.width >= (sel === '#new-submit' ? 60 : 200), `${sel} 위치가 맞지 않다 ${JSON.stringify(box)}`)
        if (sel === '#new-submit') must(box.y >= 0 && box.y + box.height <= vh + 1, `등록 단추가 화면 밖이다 ${JSON.stringify(box)}`)
      }
      if (vw >= 1366) {
        const a = await page.locator('#intake-problem').boundingBox(), b = await page.locator('#intake-io').boundingBox()
        must(b.x >= a.x + a.width - 2 && Math.abs(b.y - a.y) < 40, `1366에서 두 칸이 나란하지 않다 ${JSON.stringify([a, b])}`)
      }
    })
    await need('등록하면 풀이 화면으로 가고 요청 모양이 그대로다', async () => {
      await page.locator('#new-submit').click()
      await page.waitForURL(/#\/p\/u/, { timeout: 8000 })
      const post = rec.posts.find((x) => x.path === '/api/problems/new')
      must(post, '/api/problems/new 요청이 없다')
      const keys = Object.keys(post.body).sort()
      for (const k of ['title', 'text', 'theme', 'level', 'cases', 'language', 'mode', 'names']) must(keys.includes(k), `요청에 ${k}가 없다(${keys})`)
      const extra = keys.filter((k) => !['title', 'text', 'theme', 'level', 'cases', 'language', 'mode', 'names', 'problem', 'again'].includes(k))
      must(!extra.length, `요청에 새 칸이 생겼다: ${extra}`)
      must(post.body.problem === undefined || post.body.problem === true, `문제인데 problem이 ${post.body.problem}`)
      must(post.body.mode === 'function' && post.body.language === 'python' && post.body.title === '조명 켜기 횟수', '방식·언어·제목이 다르다')
      must(post.body.cases.length === 3 && post.body.cases.every((c) => sameSet(Object.keys(c), ['input', 'expected', 'hidden'])), `cases 모양이 다르다 ${JSON.stringify(post.body.cases)}`)
      must(sameSet(post.body.names, ['lamps', 'm']), `names ${post.body.names}`)
      must(post.body.cases[0].input === '[[1, 1, 0, 1, 1, 1], 2]' && post.body.cases[0].expected === '2', `첫 케이스 ${JSON.stringify(post.body.cases[0])}`)
      must(post.body.text.includes('복도에 일렬로') && post.body.text.includes('입출력 예 설명'), '저장하는 글이 원문과 다르다')
    })
    await need('키 없이도 예시 채점이 되고 준비 중에서 멈추지 않는다', async () => {
      await page.locator('#code').waitFor({ state: 'visible', timeout: 4000 })
      await page.locator('#code').fill(SOLUTION)
      await page.locator('#run').click()
      await page.waitForFunction(() => /예시 통과/.test(document.querySelector('#result .verdict.pass')?.textContent || ''), null, { timeout: 15000 })
      await sleep(1200)
      const check = await page.evaluate(() => document.getElementById('p-check')?.textContent || '')
      must(!/준비 중|만드는 중/.test(check), `준비 중에서 멈췄다: ${check}`)
    })
    await need('수정 화면이 같은 꼴(걸음 없음, 두 칸, 카드)이다', async () => {
      const id = page.url().split('#/p/')[1]
      await page.goto(`${base}/#/edit/${id}`)
      await page.locator('#new-submit').waitFor({ state: 'visible', timeout: 4000 })
      for (const sel of ['#wsteps', '#wstep-title', '#new-next', '#new-back', '#new-summary']) must((await count(page, sel)) === 0, `수정 화면에 ${sel}이 남아 있다`)
      for (const sel of ['#intake-problem', '#intake-io']) await page.locator(sel).waitFor({ state: 'visible', timeout: 3000 })
      await waitCards(page, 3)
      must((await editable(page)) === 0, '수정 화면의 카드도 먼저는 읽기 전용이어야 한다')
      must(/바꿔서 저장/.test(await text(page, '#new-submit')), '저장 단추 글이 다르다')
      must(await page.locator('#new-mode').isDisabled(), '수정에서 방식을 바꿀 수 있다')
      await page.locator('#new-text').fill((await page.locator('#new-text').inputValue()) + '\n덧붙인 글입니다.')
      await page.locator('#new-submit').click()
      await page.locator('#edit-confirm').waitFor({ state: 'visible', timeout: 3000 })
      await page.locator('#edit-no').click()
    })
  })

  // 2. 웹 페이지에서 복사한 글(text/html): 메뉴·머리글·옆 칸·바닥글은 빠지고 위첨자는 ^로 남는다
  await scenario(viewport, 'html', async (page, rec, need) => {
    await need('HTML 붙여 넣기를 글로 바꿔 넣는다', async () => {
      await page.evaluate(([htmlText, plainText]) => {
        const ta = document.getElementById('new-text')
        ta.focus()
        const data = new DataTransfer()
        data.setData('text/html', htmlText)
        data.setData('text/plain', plainText)
        ta.dispatchEvent(new ClipboardEvent('paste', { clipboardData: data, bubbles: true, cancelable: true }))
      }, [HTML, HTML_PLAIN()])
      await page.waitForFunction(() => document.getElementById('new-text').value.includes('복도에 일렬로'), null, { timeout: 3000 })
      const got = await page.locator('#new-text').inputValue()
      for (const bad of HTML_BAD) must(!got.includes(bad), `메뉴·머리글이 남았다: ${bad}`)
      must(got.includes('10^5') && !got.includes('105'), '위첨자가 ^로 남지 않았다')
    })
    await need('붙여 넣자 감지가 돌아 예시가 찬다', async () => {
      await waitLine(page, /예시 3개/)
      await waitCards(page, 3)
      must((await page.locator('#new-title').inputValue()) === '조명 켜기 횟수', '제목이 채워지지 않았다')
    })
  })

  // 3. 수식: $…$, $$…$$, 평문 10^5, A_i. 금액·코드·주입은 그대로이거나 무력
  await scenario(viewport, 'math', async (page, rec, need) => {
    await need('수식이 깨지지 않는다', async () => {
      await page.locator('#new-text').fill(MATH)
      await page.locator('#preview').waitFor({ state: 'visible', timeout: 4000 })
      await page.waitForFunction(() => document.querySelectorAll('#preview .katex').length >= 2, null, { timeout: 6000 })
      const out = await html(page, '#preview')
      must(await count(page, '#preview .katex-display') >= 1, '$$…$$가 따로 줄에 그려지지 않는다')
      must(/10\^\{?5\}?|10<sup[^>]*>\s*5\s*<\/sup>|10<\/span>[^]*?msupsub/.test(out) && /10\^\{?9\}?|10<sup[^>]*>\s*9\s*<\/sup>|10<\/span>[^]*?msupsub/.test(out), '10^5·10^9의 뜻이 사라졌다')
      must(/A_i|A<sub[^>]*>\s*i\s*<\/sub>|A<\/span>[^]*?msupsub/.test(out), 'A_i가 사라졌다')
      must(!/<em[\s>]|<i[\s>]/.test(out), 'A_i·max_count 같은 낱말이 기울임으로 바뀌었다')
      must(/max_count/.test(await text(page, '#preview')) && /min_count/.test(await text(page, '#preview')), 'max_count·min_count가 바뀌었다')
      must(await page.locator('#preview code', { hasText: 'snake_case' }).count() === 1, '코드 안 snake_case가 그대로가 아니다')
    })
    await need('금액의 $는 수식이 아니다', async () => {
      await page.locator('#new-text').fill(MONEY)
      await page.waitForFunction(() => /\$5/.test(document.getElementById('preview')?.textContent || ''), null, { timeout: 4000 })
      must((await count(page, '#preview .katex')) === 0, '금액이 수식으로 읽혔다')
      must(/\$10/.test(await text(page, '#preview')), '$10이 사라졌다')
    })
    await need('붙여 넣은 글 속 스크립트·javascript: 링크가 무력하다', async () => {
      await page.locator('#new-text').fill(EVIL)
      await sleep(1200)
      must((await page.evaluate(() => window.__xss)) === undefined, '붙여 넣은 글이 스크립트를 돌렸다')
      must((await count(page, '#preview a[href^="javascript:" i], #preview img, #preview [onerror]')) === 0, '위험한 태그·링크가 남았다')
    })
  })

  // 4. 문제 글이 아니다: 경고를 띄우고, 그래도 넣을 때 뒤 준비를 미룬다(problem: false). 뒤 준비 요청이 가지 않는다
  await scenario(viewport, 'notice', async (page, rec, need) => {
    await need('문제가 아닌 글은 경고를 띄운다(막지는 않는다)', async () => {
      await page.locator('#new-text').fill(NOT_PROBLEM)
      await waitLine(page, /문제 글로 보이지 않아요/)
      must(await page.locator('#new-submit').isEnabled(), '그래도 등록할 수 있어야 한다')
    })
  })
  await scenario(viewport, 'hold', async (page, rec, need, seed) => {
    await need('모델이 문제가 아니라고 하면 경고가 뜨고 예시는 그대로 찬다', async () => {
      await page.locator('#new-text').fill(plainOf(seed))
      await waitLine(page, /문제 글로 보이지 않아요/)
      await waitCards(page, 3)
    })
    await need('그래도 등록하면 problem:false로 보내고 준비를 부르지 않는다', async () => {
      await page.locator('#new-submit').click()
      await page.waitForURL(/#\/p\/u/, { timeout: 8000 })
      const post = rec.posts.find((x) => x.path === '/api/problems/new')
      must(post && post.body.problem === false, `등록 요청의 problem이 ${post && post.body.problem}`)
      await sleep(1500)
      must(!rec.posts.some((x) => x.path === '/api/problems/prepare'), '문제 아님 경고 뒤에 준비를 불렀다')
      const id = page.url().split('#/p/')[1]
      const state = await page.evaluate(async (pid) => (await (await fetch('/api/state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: pid }) })).json()).problem.hold, id)
      must(state === true, '서버가 준비를 미루지 않았다(hold)')
    })
  }, async (page, rec) => {
    await connect(page)
    await patchDetect(page, [], (data) => { data.problem = false; data.notice = '문제 글로 보이지 않아요. 그래도 등록할 수 있어요.' })
  })

  // 5. 문제 밖 줄: 줄 수를 알리고 미리보기에서 뺀다. [보기]에서 되돌린 줄만 저장하는 글에 남는다
  await scenario(viewport, 'noise', async (page, rec, need, seed) => {
    await need('문제 밖 글 줄 수를 알리고 미리보기에서 뺀다', async () => {
      await page.locator('#new-text').fill(noisyOf(seed))
      await waitLine(page, /문제 밖 글 2줄/)
      await waitLine(page, /예시 3개/)
      must(!(await text(page, '#intake-problem')).includes('댓글 3개'), '뺀 줄이 미리보기에 남았다')
      must(!(await text(page, '#intake-io')).includes('인기 순위'), '뺀 줄이 입출력부에 남았다')
    })
    await need('[보기]로 뺀 줄을 볼 수 있고 한 줄만 되돌린다', async () => {
      await page.locator('#noise-show').click()
      await page.locator('#noise-lines').waitFor({ state: 'visible', timeout: 2000 })
      const shown = await text(page, '#noise-lines')
      must(NOISE.every((line) => shown.includes(line)), `뺀 줄이 안 보인다: ${shown}`)
      const buttons = page.locator('#noise-lines [data-noise-restore]')
      must((await buttons.count()) === 2, `줄마다 되돌리기 단추([data-noise-restore])가 있어야 한다: ${await buttons.count()}`)
      await buttons.first().click()
    })
    await need('저장하는 글에는 잡음 줄이 없고 되돌린 줄은 있다', async () => {
      await page.locator('#new-submit').click()
      await page.waitForURL(/#\/p\/u/, { timeout: 8000 })
      const post = rec.posts.find((x) => x.path === '/api/problems/new')
      must(post, '등록 요청이 없다')
      must(!post.body.text.includes(NOISE[1]), '되돌리지 않은 잡음 줄이 저장하는 글에 남았다')
      must(post.body.text.includes(NOISE[0]), '되돌린 줄이 저장하는 글에서 빠졌다')
      must(post.body.text.includes('복도에 일렬로'), '문제 글까지 빠졌다')
    })
  }, async (page) => {
    await connect(page)
    await patchDetect(page, [], (data, body) => { body.text.split('\n').forEach((line, i) => { if (NOISE.includes(line)) data.kinds[i] = 'noise' }) })
  })

  // 6. 사용자가 고친 칸은 뒤에 온 모델 결과가 덮지 않는다(touched)
  let release
  const gate = new Promise((done) => { release = done })
  await scenario(viewport, 'touched', async (page, rec, need, seed) => {
    const calls = rec.calls
    await need('먼저 규칙 결과(fast)가 차고 모델 감지가 따라온다', async () => {
      await page.locator('#new-text').fill(plainOf(seed))
      await waitCards(page, 3)
      await page.waitForFunction(() => document.getElementById('new-title').value === '조명 켜기 횟수', null, { timeout: 3000 })
      for (let i = 0; i < 40 && !calls.some((c) => !c.fast); i++) await sleep(50)
      must(calls[0].fast === true, '첫 감지가 fast(규칙만)가 아니다')
      must(calls.some((c) => !c.fast), 'fast 뒤에 모델 감지(fast 없는 요청)를 부르지 않았다')
    })
    await need('고친 제목·방식·케이스는 늦게 온 결과가 덮지 않는다', async () => {
      await page.locator('#new-title').fill('내가 고친 제목')
      await page.locator('#new-more').evaluate((el) => { el.open = true })
      await page.locator('#case-edit').click()
      await page.locator('#case-expected-1').fill('7')
      release()
      await sleep(800)
      must((await page.locator('#new-title').inputValue()) === '내가 고친 제목', `제목을 덮었다: ${await page.locator('#new-title').inputValue()}`)
      must((await page.locator('#new-mode').inputValue()) === 'function', '모델 결과가 방식을 바꿨다')
      must((await page.locator('#case-expected-1').inputValue()) === '7', '케이스를 덮었다')
      must((await cards(page)) === 3, '케이스 줄 수가 바뀌었다')
    })
    await need('고친 칸은 뒤 감지 요청에 touched로 실려 간다', async () => {
      calls.length = 0
      await page.locator('#new-text').fill(plainOf(seed) + '\n마지막 줄을 덧붙였습니다.')
      for (let i = 0; i < 40 && !calls.length; i++) await sleep(50)
      must(calls.length, '글을 고쳤는데 감지를 다시 부르지 않았다')
      const touched = calls[calls.length - 1].touched || []
      must(touched.includes('title') && touched.includes('cases'), `touched에 고친 칸이 없다: ${JSON.stringify(touched)}`)
      await sleep(600)
      must((await page.locator('#new-title').inputValue()) === '내가 고친 제목', '다시 감지하며 제목을 덮었다')
    })
  }, async (page, rec) => {
    rec.calls = []
    await connect(page)
    await patchDetect(page, rec.calls, async (data, body) => {
      if (body.fast) return
      await gate // 모델 결과는 사용자가 고친 뒤에 온다
      data.title = '모델이 지은 제목'
      data.mode = 'program'
      data.suggest = {}
    })
  })

  // 7. 초안: 새로고침해도 글·제목·케이스가 남고, 걸음 값은 없다(수정 화면과 같은 꼴)
  await scenario(viewport, 'draft', async (page, rec, need, seed) => {
    await need('글을 넣고 감지가 끝난 초안이 새로고침 뒤에도 같은 화면으로 돌아온다', async () => {
      await page.locator('#new-text').fill(plainOf(seed))
      await waitCards(page, 3)
      await page.waitForFunction(() => { try { return JSON.parse(sessionStorage.getItem('algoblock.draft')).cases.length === 3 } catch { return false } }, null, { timeout: 3000 })
      const draft = await page.evaluate(() => JSON.parse(sessionStorage.getItem('algoblock.draft')))
      must(draft.step === undefined, `초안에 걸음(step)이 남아 있다: ${draft.step}`)
      must(draft.title === '조명 켜기 횟수' && draft.text.includes('복도에 일렬로'), '초안에 제목·글이 없다')
      await page.reload()
      await page.locator('#new-text').waitFor({ state: 'visible', timeout: 4000 })
      must((await page.locator('#new-text').inputValue()) === plainOf(seed), '새로고침 뒤 글이 다르다')
      must((await page.locator('#new-title').inputValue()) === '조명 켜기 횟수', '새로고침 뒤 제목이 다르다')
      await waitCards(page, 3)
      for (const sel of ['#intake-problem', '#intake-io']) await page.locator(sel).waitFor({ state: 'visible', timeout: 3000 })
      must((await count(page, '#wsteps')) === 0, '걸음 표시가 되살아났다')
    })
  })
}
await browser.close()
process.exit(failed ? 1 : 0)
