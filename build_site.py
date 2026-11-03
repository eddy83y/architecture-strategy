"""Build the GitHub Pages site with Python's standard library only."""
from pathlib import Path
from html import escape as e
import json
import hashlib
import re
from component_diagrams import build as build_component_diagrams

ROOT = Path(__file__).resolve().parent
SITE = ROOT/'site'
CONTENT = ROOT/'content'
QAS = json.loads((CONTENT/'qas.json').read_text(encoding='utf-8'))
RESEARCH = json.loads((CONTENT/'strategies.json').read_text(encoding='utf-8'))
FIGURES = json.loads((CONTENT/'diagram_markup.json').read_text(encoding='utf-8'))
STRATEGIES = {s['id']:s for s in RESEARCH['strategies']}
CSS_VERSION = hashlib.sha256((SITE/'assets/site.css').read_bytes()).hexdigest()[:12]
FIGURES = {sid: svg.replace('<svg ', '<svg style="display:block;width:100%;max-width:100%;min-width:0;height:auto" ', 1) for sid, svg in FIGURES.items()}


def nav(current='index'):
    links=[('index','index.html','전체 QAS')]+[(q['slug'],q['slug']+'.html','QAS '+q['number']) for q in QAS]
    return '<nav class="primary-nav" aria-label="주요 메뉴">'+''.join(f'<a href="{href}"'+(' aria-current="page"' if key==current else '')+f'>{e(name)}</a>' for key,href,name in links)+'</nav>'


def shell(title,description,body,current='index'):
    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{e(description,quote=True)}"><meta name="theme-color" content="#f5f5f5">
<title>{e(title)} | 자동차보험 아키텍처 전략</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&family=Noto+Sans+KR:wght@400;500;600;700&family=Noto+Serif+KR:wght@400&display=swap">
<link rel="stylesheet" href="assets/site.css?v={CSS_VERSION}"></head><body>
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="site-header"><div class="header-inner"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">A</span><span>Architecture Strategy<small>다이렉트 자동차보험 시스템</small></span></a>{nav(current)}</div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div><strong>다이렉트 자동차보험 · 아키텍처 전략</strong><p>외부 공개 출처를 참고한 설계 검토 · 2026-11-02</p></div><a href="index.html">전체 QAS로 돌아가기 ↑</a></footer>
</body></html>'''


def home():
    rows=[]
    for q in QAS:
        rows.append(f'''<a class="qas-row" href="{q['slug']}.html" aria-describedby="intro-{q['slug']}"><span class="row-number">{q['number']}</span><div class="row-content"><p class="eyebrow">{e(q['attribute'])}</p><h2>{q['name']}</h2><p id="intro-{q['slug']}">{e(q['summary'])}</p></div><div class="row-choice"><span>선택 전략</span><strong>{q['selected']}</strong><p>{e(q['short_choice'])}</p></div><span class="row-arrow" aria-hidden="true">↗</span></a>''')
    body='''<section class="home-intro"><div><p class="eyebrow">QUALITY ATTRIBUTE SCENARIOS</p><h1>다이렉트 자동차보험<br>아키텍처 전략</h1><p class="lead">세 가지 품질 요구사항을 기준으로 전략을 비교하고,<br class="desktop-break"> 선택 근거와 검증할 조건을 정리했다.</p></div><div class="intro-meta"><span>검토 범위</span><p><strong>3</strong> QAS</p><p><strong>9</strong> 통합 전략</p><p><strong>3</strong> 선택 결과</p></div></section>
<section class="home-qas" aria-labelledby="qas-list-title"><div class="section-heading"><h2 id="qas-list-title">QAS 선택</h2><p>요구사항부터 비교·선택까지, QAS별로 확인할 수 있다.</p></div>'''+''.join(rows)+'''</section>
<section class="reading-guide"><h2>자료를 읽는 순서</h2><ol><li><span>01</span>확정 요구사항</li><li><span>02</span>전략 3개와 다이어그램</li><li><span>03</span>장단점·Trade-off</li><li><span>04</span>선택 이유와 보완점</li></ol><p>각 전략은 Style·Pattern·Tactics를 함께 고려했다.</p></section>'''
    (SITE/'index.html').write_text(shell('QAS 선택','성능·가용성·복구성 QAS별 아키텍처 전략, 장단점과 trade-off 비교, 선택 근거.',body),encoding='utf-8')


def requirement(q):
    metrics=''.join(f'<div><strong>{e(value)}</strong><span>{e(label)}</span></div>' for value,label in q['metrics'])
    conditions=''.join(f'<li>{e(line)}</li>' for line in q['conditions'])
    return f'''<section class="requirements" id="requirements"><div class="section-heading"><h2>확정 요구사항</h2><span class="section-label">QAS {q['number']}</span></div><div class="metrics">{metrics}</div><p class="scenario">{e(q['scenario'])}</p><details class="conditions" open><summary>측정 범위와 공통 설계 조건</summary><ul>{conditions}</ul></details></section>'''


def strategy(s,q):
    sid=s['id']; chosen=sid==q['selected']
    rows=''.join(f'<tr><th scope="row">{label}</th><td>{e(s[key])}</td></tr>' for label,key in [('Style','style'),('Pattern','pattern'),('Tactics','tactics')])
    citations=' · '.join(f'<a href="#source-{key}">{key}</a>' for key in s['evidence'])
    return f'''<article class="strategy" id="{sid.lower()}"><div class="strategy-heading"><span class="strategy-id">{sid}</span><h3>{e(s['title'])}</h3>{'<span class="selected-tag">선택 전략</span>' if chosen else ''}</div><p class="strategy-intro">{e(s['intro'])}</p><div class="table-wrap"><table class="spt"><caption class="sr-only">{sid}의 Style, Pattern, Tactics</caption><tbody>{rows}</tbody></table></div><dl class="strategy-notes"><div><dt>동작</dt><dd>{e(s['flow'])}</dd></div><div><dt>QAS 연결</dt><dd>{e(s['fit'])}</dd></div><div><dt>적용 한계</dt><dd>{e(s['limits'])}</dd></div></dl><p class="citations">근거 {citations}</p><figure><div class="figure-heading"><span>{sid} 구조와 동작</span></div><div class="diagram-container">{FIGURES[sid]}</div><figcaption>{e(s['diagram'])}</figcaption></figure>{component_figure(sid)}</article>'''


def component_figure(sid):
    figure=COMPONENT_FIGURES[sid]
    return f'<figure class="component-overview"><div class="figure-heading"><span>{sid} 핵심 Component Diagram</span><a class="component-open" href="components/{sid.lower()}.html" target="_blank" rel="noopener noreferrer">그림만 보기 ↗</a></div><div class="diagram-container">{figure["svg"]}</div><figcaption>{e(figure["note"])}</figcaption></figure>'


def pros_cons(q):
    analyses=[]
    for sid in q['ids']:
        analysis=q['pros_cons'][sid]
        analyses.append(f'''<div class="strategy-analysis"><h3><a href="#{sid.lower()}">{sid}</a> {e(STRATEGIES[sid]["title"])}</h3><p><strong>장점.</strong> {e(analysis["pros"])}</p><p><strong>단점.</strong> {e(analysis["cons"])}</p></div>''')
    return '<section id="pros-cons"><div class="section-heading"><h2>전략별 장단점</h2><span class="section-label">PROS & CONS</span></div>'+''.join(analyses)+'</section>'


def comparison(q):
    columns=''.join(f'<th scope="col"'+(' class="chosen-col"' if sid==q['selected'] else '')+f'><a href="#{sid.lower()}">{sid}</a><span>{e(STRATEGIES[sid]["title"])}</span></th>' for sid in q['ids'])
    rows=[]
    labels={'+':'유리','o':'중립 또는 상쇄','-':'불리하거나 관리 부담 증가'}
    for label,values in q['ratings'].items():
        cells=''.join(f'<td'+(' class="chosen-col"' if q['ids'][i]==q['selected'] else '')+f'><span class="rating" aria-label="{labels[value]}">{value}</span></td>' for i,value in enumerate(values))
        rows.append(f'<tr><th scope="row">{label}</th>{cells}</tr>')
    return f'''<section id="comparison"><div class="section-heading"><h2>Trade-off 비교</h2><span class="section-label">QUALITATIVE COMPARISON</span></div><p class="legend" id="rating-legend"><span><b>+</b> 유리</span><span><b>o</b> 중립·상쇄</span><span><b>-</b> 불리·관리 부담 증가</span></p><div class="table-wrap"><table class="tradeoff" aria-describedby="rating-legend comparison-note"><caption class="sr-only">{q['name']} QAS의 전략 3개 정성 비교</caption><thead><tr><th scope="col">비교 항목</th>{columns}</tr></thead><tbody>{''.join(rows)}</tbody></table></div><div class="comparison-notes" id="comparison-note"><p>{e(q['comparison_note'])}</p><p>기호를 단순 합산하지 않고 요구 충족 가능성과 구현·운영 부담을 함께 판단했다. 보안의 ‘-’는 보호할 API·저장소·권한이 늘어난다는 의미다.</p></div></section>'''


def decision(q):
    return f'''<section class="decision" id="decision"><p class="eyebrow">선택 전략 · {q['selected']}</p><h2>{e(STRATEGIES[q['selected']]['title'])}</h2><p class="decision-reason">{e(q['decision'])}</p><div class="decision-detail"><div><h3>받아들이는 Trade-off</h3><p>{e(q['decision_tradeoff'])}</p></div><div><h3>보완점·개선점</h3><p>{e(q['improvements'])}</p></div></div><a class="text-link" href="#{q['selected'].lower()}">선택 전략 다시 보기 ↑</a></section>'''


def sources(q):
    keys=sorted({key for sid in q['ids'] for key in STRATEGIES[sid]['evidence']},key=lambda x:int(x[1:]))
    entries=[]
    for key in keys:
        ref=RESEARCH['evidence'][key]
        label=f'<a href="{e(ref["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{e(ref["label"])} ↗</a>' if ref['url'] else e(ref['label'])
        entries.append(f'<li id="source-{key}"><span>{key}</span><div><strong>{label}</strong><p>{e(ref["level"])}</p></div></li>')
    return '<section class="sources" id="sources"><div class="section-heading"><h2>조사 근거와 적용 범위</h2><span class="section-label">SOURCES</span></div><p>아래 외부 공개 출처를 참고했다. 구조의 조합과 비교·선택은 프로젝트 QAS에 적용한 설계 판단이며, 외부 출처의 직접 권고나 구현·실측 검증 결과는 아니다.</p><ol class="source-list">'+''.join(entries)+'</ol></section>'


def qas_page(q):
    links=[('requirements','요구사항'),('strategies','전략 3개'),('pros-cons','장단점'),('comparison','Trade-off'),('decision','선택 근거·보완점'),('sources','조사 근거')]
    toc='<nav class="section-nav" aria-label="이 페이지의 목차">'+''.join(f'<a href="#{key}">{label}</a>' for key,label in links)+'</nav>'
    header=f'''<section class="page-intro"><a class="breadcrumb" href="index.html">← 전체 QAS</a><p class="eyebrow">QAS {q['number']} / {e(q['attribute'])}</p><h1>{q['name']}</h1><p class="lead">{e(q['summary'])}</p><a class="choice-summary" href="#decision"><span>검토 결과 <strong>{q['selected']}</strong></span><span>{e(q['choice_summary'])}</span><b aria-hidden="true">↓</b></a></section>'''
    overview='<section id="strategies"><div class="section-heading"><h2>Style·Pattern·Tactics 통합 전략</h2><span class="section-label">3 ALTERNATIVES</span></div><p>같은 QAS를 달성하기 위한 세 가지 대안이다. 각 전략의 구조와 동작을 먼저 살펴본 뒤 장단점과 Trade-off를 비교한다.</p>'+''.join(strategy(STRATEGIES[sid],q) for sid in q['ids'])+'</section>'
    index=QAS.index(q)
    next_q=QAS[(index+1)%len(QAS)]
    next_link=f'<nav class="next-page" aria-label="다음 QAS"><a href="index.html">← 전체 QAS</a><a href="{next_q["slug"]}.html">다음 QAS · {next_q["name"]} →</a></nav>'
    body=header+toc+requirement(q)+overview+pros_cons(q)+comparison(q)+decision(q)+sources(q)+next_link
    (SITE/(q['slug']+'.html')).write_text(shell(q['name']+' QAS',q['summary'],body,q['slug']),encoding='utf-8')


def main():
    global COMPONENT_FIGURES
    COMPONENT_FIGURES=build_component_diagrams(ROOT,STRATEGIES)
    SITE.mkdir(exist_ok=True)
    (SITE/'assets').mkdir(exist_ok=True)
    (SITE/'.nojekyll').write_text('',encoding='utf-8')
    home()
    # A branch-root Pages deployment must also have an HTML entry point.
    # Keep fragment links on this page and rebase only local file links.
    entry=(SITE/'index.html').read_text(encoding='utf-8')
    entry=re.sub(r'\b(href|src)="(?!https?://|#|/)([^"]+)"',r'\1="site/\2"',entry)
    (ROOT/'index.html').write_text(entry,encoding='utf-8')
    (ROOT/'.nojekyll').write_text('',encoding='utf-8')
    for q in QAS:
        qas_page(q)
    error='<section class="page-intro"><p class="eyebrow">404</p><h1>페이지를 찾을 수 없습니다.</h1><p class="lead">첫 화면에서 QAS를 다시 선택해 주세요.</p><a class="text-link" href="index.html">전체 QAS로 이동 →</a></section>'
    (SITE/'404.html').write_text(shell('페이지를 찾을 수 없습니다','QAS 선택 화면으로 돌아가기',error),encoding='utf-8')
    print(json.dumps({'pages':5+len(COMPONENT_FIGURES),'component_diagrams':len(COMPONENT_FIGURES),'qas':len(QAS),'strategies':len(STRATEGIES),'selected':[q['selected'] for q in QAS],'site':str(SITE)},ensure_ascii=False))


if __name__=='__main__':
    main()
