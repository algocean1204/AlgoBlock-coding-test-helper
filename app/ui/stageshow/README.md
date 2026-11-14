# 안내 데모 (Stageshow)

처음 안내 여섯 장의 움직이는 그림과 README 맨 위 그림의 소스다. [Stageshow](https://github.com/benjitaylor/skills) 키트(React)로 만들고, 앱은 미리 빌드한 `../tour-demos.js`와 `../tour-demos.css`만 쓴다. 앱 본체는 React를 쓰지 않는다.

- `src/demos/` 여섯 장(순서는 `../app.js`의 `TOUR`와 같다), `src/hero.tsx` README 그림, `src/look.css` 앱 색을 옮긴 토큰
- `kit/`, `scripts/` Stageshow 사본(MIT, `LICENSE-stageshow.txt`, 고지는 `NOTICE-stageshow.md`). 다른 회사 로고 그림은 뺐다

## 다시 빌드하기

Node.js 20.19 이상과 Chrome이 필요하다.

```sh
npm install
npm run typecheck && npm run build        # ../tour-demos.js, ../tour-demos.css를 다시 쓴다. 두 파일을 함께 커밋한다
```

`vite.config.ts`의 `outDir: '..'`는 출력을 이 폴더의 부모인 `app/ui`에 두려는 설정이다. 그래서 빌드는 `build.outDir must not be the same directory of root or a parent directory of root` 경고를 낸다. `emptyOutDir: false`와 `copyPublicDir: false`라서 `app/ui`의 다른 파일은 지우거나 복사하지 않고, 쓰는 것은 `tour-demos.js`와 `tour-demos.css`뿐이다.

## 고친 뒤 확인하기

```sh
npm run dev                                # http://127.0.0.1:5199/?demo=0 ~ 5, ?demo=hero
node scripts/film.mjs "http://127.0.0.1:5199/?demo=0" --gate --out shots/d1.png              # 안내 창 너비
node scripts/film.mjs "http://127.0.0.1:5199/?demo=0" --gate --width 390 --out shots/d1-390.png
node scripts/film.mjs "http://127.0.0.1:5199/?demo=hero" --still --gate --pad 0 --out ../../../.github/assets/hero.png
```

여섯 장 모두 두 너비에서 마지막 줄이 `rehearsal passed`여야 한다. `--dark`는 어두운 테마, `--reduced`는 움직임 줄이기(멈춘 그림)를 찍는다.
