# 다이렉트 자동차보험 아키텍처 전략

성능·가용성·복구성 QAS별로 전략 3개와 기존 동작 그림·핵심 Component Diagram, 장단점, Trade-off 비교, 선택 근거를 담은 정적 사이트다.

장단점은 전략별 설명 문단으로 작성하고, Trade-off는 성능·신뢰성·유지보수·보안의 정성 비교표로 제시한다.

| 페이지 | 내용 | 선택 전략 |
| --- | --- | --- |
| `site/index.html` | QAS 선택 | — |
| `site/performance.html` | 성능 QAS | P1 · 복제 확장·버전별 캐시 |
| `site/availability.html` | 신뢰성·가용성 QAS | A2 · Blue-Green·호환 DB 변경 |
| `site/recovery.html` | 신뢰성·복구성 QAS | R1 · 동기 복제·일괄 DR 전환 |

## 로컬 확인

`site/index.html`을 브라우저로 열거나, 아래 명령으로 정적 서버를 실행한다.

```sh
python -m http.server 8080 --directory site
```

페이지는 HTML과 CSS로 동작한다. 서버 프로그램, API 키, 데이터베이스, 프런트엔드 패키지 설치는 필요하지 않다. 웹 글꼴을 불러오지 못하면 로컬 글꼴을 사용한다.

## 내용 수정과 재생성

- `content/strategies.json`: 기존 조사에 근거한 전략 9개와 출처 정보
- `content/qas.json`: 확정 QAS, 장단점, Trade-off 표, 선택 이유와 보완점
- `content/diagram_markup.json`: 기존 전략별 다이어그램의 인라인 SVG
- `content/components.json`: 전략별 핵심 컴포넌트와 의존 관계
- `component_diagrams.py`: 간소화 UML 그림과 단독 HTML 생성
- `site/assets/site.css`: 화면·모바일·인쇄 스타일

수정 후 Python 표준 라이브러리만으로 페이지를 다시 만든다.

```sh
python build_site.py
```

`site/`에는 배포할 파일만 들어 있다. GitHub Actions는 이 폴더만 배포한다. 공개 페이지에서 작업 PC의 절대 경로나 배포 폴더 밖의 파일을 참조하지 않는다.

저장소 루트의 `index.html`과 `.nojekyll`도 함께 생성한다. 저장소 루트가 배포되는 경우에도 `/`에서는 QAS 첫 화면이 열리며, README를 첫 화면으로 사용하지 않는다. 루트 첫 화면의 링크와 스타일은 `site/`의 파일을 참조한다.

## GitHub Pages 배포

대상 저장소는 `eddy83y/architecture-strategy`다. 기본 브랜치는 `main`으로 가정했다. 다른 기본 브랜치를 사용한다면 `.github/workflows/deploy-pages.yml`의 브랜치 설정을 맞춘다.

1. 이 폴더의 내용을 저장소 루트에 올린다. 숨김 폴더 `.github/`도 포함한다.
2. 저장소의 **Settings → Pages → Build and deployment → Source**에서 **GitHub Actions**를 선택한다.
3. `main`에 변경을 올리거나 Actions의 **Deploy QAS strategy pages → Run workflow**를 실행한다.
4. 배포 완료 후 Pages 설정이나 workflow의 배포 URL을 확인한다.

예상 프로젝트 주소는 `https://eddy83y.github.io/architecture-strategy/`다. 실제 배포가 성공하기 전에는 공개 주소로 확정하지 않는다.

워크플로는 `actions/checkout@v6`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, `actions/deploy-pages@v4`를 사용한다. 설정 근거는 [GitHub Pages 공식 배포 문서](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)다.

## 자료의 범위

기존 조사 문서 01~06과 점검 문서 07을 바탕으로 작성했다. 각 QAS 페이지에서 사용한 원자료와 확인 범위를 볼 수 있다. 비교표는 정성 판단이며 실측 점수나 보안 취약성 판정이 아니다. 최종 선정·구현·성능 시험·무중단 검증·DR 훈련의 완료 보고로 해석하지 않는다.

## Component Diagram

기존 그림 아래에 전략별 핵심 Component Diagram을 추가한다. 점선 의존 화살표는 사용하는 쪽에서 제공하는 쪽을 향한다. 센터 간 동기 복제는 별도 실선으로 구분한다. 저장소·외부 시스템·동일 컴포넌트의 실행 인스턴스는 구분해서 표시하며 상세 포트·인터페이스는 생략한다.

`site/components/p1.html`부터 `r3.html`까지 단독 열람용 HTML 9개도 함께 생성한다. 모든 그림은 창 너비에 맞춰 비례 축소한다.
