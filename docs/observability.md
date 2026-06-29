# Observability for Agent Loop Engineering — Tracing, Metrics, and Monitoring

Current Phase 3 observability scope for Cairn agent loop engineering:

- JSON trace export from `run --trace-file`
- duration metadata per execution
- retry event counts
- static cost estimation via `cost`
- Grafana starter dashboard template in [docs/grafana/cairn-runtime-dashboard.json](/Users/prantikpratimmedhi/Documents/Cairn/docs/grafana/cairn-runtime-dashboard.json)

Not built yet:

- centralized trace store
- live metrics backend
- hosted CairnLens UI
- advanced cost attribution by provider/model
