# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.3.0] - 10/11/2020

### Added

- JOSS paper
- Periodic CVRP scheduling option
- Initial solution for CVRP computed with Greedy Algorithm
- Diving heuristic (controlled with new paramater in `VehicleRoutingProblem.solve`)
- Hyper-heuristic pricing strategy option `pricing_strategy="Hyper"`.
- Jupyter notebooks with hyper-heuristics experiments (one to be updated soon).
- Paragraph to the paper with the hyper-heuristic explanation and citations.

### Changed

- Master problem formulation to column-based
- Benchmark tests

## [v0.2.0] - 07/06/2020

### Added

- Mixed fleet option
- Greedy randomized pricing option
- Stabilization with Interior Points
- Diving heuristic WIP

### Changed

- Pricing strategy names


[Unreleased]: https://github.com/Kuifje02/vrpy/compare/0.2.0...master
[v0.2.0]: https://github.com/Kuifje02/vrpy/compare/0.1.0...0.2.0
