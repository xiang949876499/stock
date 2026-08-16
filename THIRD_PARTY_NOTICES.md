# Third-Party Notices and Data-Use Boundaries

Last reviewed: 2026-08-16.

The root [LICENSE](./LICENSE) covers only original contributions. It does not
grant rights to third-party code, market data, API accounts, or external
services. This inventory is not legal advice or investment advice.

## TradingAgents

- Optional dependency: tradingagents is declared as a direct Git dependency
  in pyproject.toml.
- Upstream: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents).
- License: Apache License 2.0. Preserve its license and any required notices
  when an artifact includes this dependency.

## Tushare data service

- Dependency: tushare.
- Terms: [Tushare data-service agreement](https://tushare.pro/document/1?doc_id=405).
- Boundary: the service agreement grants an individual, non-transferable,
  non-commercial, revocable, time-limited license for personal viewing and
  use. The project owner's commercial permission cannot grant Tushare data
  rights. Do not enable a commercial data workflow without separate rights
  from Tushare.

## AKShare data access

- Dependency: akshare.
- Upstream: [akfamily/akshare](https://github.com/akfamily/akshare).
- Boundary: review AKShare's current data-source notices and each upstream
  data provider's rights before commercial deployment or redistribution.

## Other dependencies

Generate a license inventory for the exact Python, frontend, container, or
installer artifact being distributed.
