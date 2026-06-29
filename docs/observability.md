# Observability for Agent Loop Engineering — Tracing, Metrics, and Monitoring

Current Phase 3 observability scope for Cairn agent loop engineering:

- JSON trace export from `run --trace-file`
- hosted trace publish via `run --trace-endpoint`
- duration metadata per execution
- retry event counts
- static cost estimation via `cost`
- hosted CairnLens summary API and UI at `/lens`
- Grafana starter dashboard template in [docs/grafana/cairn-runtime-dashboard.json](/Users/prantikpratimmedhi/Documents/Cairn/docs/grafana/cairn-runtime-dashboard.json)

Not built yet:

- advanced cost attribution by provider/model
