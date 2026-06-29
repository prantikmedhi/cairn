# Cairn SEO Strategy — Ranking #1 for "Loop Engineering"

## Keyword Targets

| Keyword | Intent | Priority | Current Gap |
|---------|--------|----------|-------------|
| loop engineering | Informational/Brand | P0 | Zero presence |
| agent loop engineering | Informational | P0 | Zero presence |
| agent loop DSL | Commercial | P0 | Zero presence |
| portable agent loops | Commercial | P0 | Zero presence |
| AI agent loop | Informational | P1 | Weak |
| agent orchestration framework | Commercial | P1 | Weak |
| cairn agent loop | Brand | P1 | Existing but weak |
| define agent loops once | Long-tail | P1 | Zero presence |

## Optimizations Applied

### 1. README.md — Complete Rewrite
- Title includes "loop engineering" (H1)
- Description mentions "agent loop engineering" in first paragraph
- Architecture diagram, feature grid, and keyword-dense subheadings
- "Why Loop Engineering Matters" section as keyword anchor
- Quick Stats table for SERP snippet optimization
- All paths changed to relative (GitHub renders correctly on web)

### 2. pyproject.toml — PyPI SEO
- Description expanded to include all target keywords
- 15 keywords added for PyPI search discoverability
- Classifiers added for AI/ML topic indexing

### 3. GitHub Pages Site (docs/index.html)
- Full semantic HTML5 with proper heading hierarchy
- Meta description + meta keywords
- Open Graph tags (og:title, og:description, og:url, og:type)
- Twitter Card tags
- JSON-LD structured data: SoftwareApplication, WebSite, BreadcrumbList
- Canonical URL
- Sitemap.xml with 10 URLs
- robots.txt with sitemap reference
- .nojekyll for GitHub Pages compatibility

### 4. CairnStudio HTML Template
- Meta description with "agent loop engineering" keywords
- Open Graph + Twitter Card tags
- JSON-LD structured data (SoftwareApplication)
- Canonical URL
- Keywords meta tag

### 5. All Documentation Files
- H1 titles rewritten to include "agent loop engineering"
- Keyword-optimized subtitle lines
- Consistent branding across all markdown files

### 6. Internal Linking
- Root-relative paths where possible
- Consistent link structure across all pages

## GitHub Repository Setup (Manual Steps Required)

### Required Actions
- [ ] Set repo description to: "Universal DSL and runtime for agent loop engineering — portable AI agent loops across LangChain, LangGraph, CrewAI, AutoGen, and OpenAI"
- [ ] Add topics: `loop-engineering`, `agent-loops`, `ai-agents`, `agent-orchestration`, `langchain`, `langgraph`, `crewai`, `autogen`, `dsl`, `workflow-engine`
- [ ] Enable GitHub Pages: Settings → Pages → Deploy from branch `main`, folder `/docs`
- [ ] Set website URL in repo to `https://prantikmedhi.github.io/cairn/`
- [ ] Register `cairn.dev` domain (from schema `$id`) and configure GitHub Pages custom domain
- [ ] Create PyPI release: `python3 -m build && python3 -m twine upload dist/*`
- [ ] Add GitHub social preview image (1280×640px)

## Off-Site SEO Recommendations

### Backlink Strategy
- Post to Hacker News with tagline "Show HN: Terraform for agent loops"
- Submit to r/MachineLearning, r/LocalLLaMA, r/AIEng
- Write blog post: "The Case for a Universal Agent Loop Language"
- Create Reddit posts in LangChain, LangGraph communities
- List on awesome-langchain, awesome-agent-frameworks

### Content Marketing
- Create PyPI listing with optimized description (auto-synced from README)
- Publish "Loop Engineering 101" blog series
- Create comparison pages: "CrewAI vs LangGraph vs Cairn"
- Record demo video for YouTube

### Social Signals
- Tweet from @prantikmedhi with #AgentLoops #LoopEngineering
- Cross-post to LinkedIn AI developer groups
- Add to relevant GitHub topics and collections

## KPI Targets

| Metric | Current | 1 Month | 3 Months | 6 Months |
|--------|---------|---------|----------|----------|
| GitHub Stars | ~0 | 50+ | 200+ | 500+ |
| GitHub Pages traffic | 0 | 500/mo | 5k/mo | 20k/mo |
| "loop engineering" rank | Not indexed | Top 100 | Top 20 | Top 5 |
| PyPI downloads | 0 | 100/mo | 1k/mo | 5k/mo |
