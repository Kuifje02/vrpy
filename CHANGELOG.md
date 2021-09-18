# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [v0.5.1] - 18/09/2021

### Added

- locked routes checks

### Fixed

- issues #102, #103, #105 - #110

## [v0.5.0] - 06/06/2021

### Added

- `heuristic_only` option
- `use_all_vehicles` option

### Fixed

- set covering constraints in last MIP with = sign

## [v0.4.0] - 13/05/2021

### Added

- `num_vehicles` option with `periodic` option

### Changed

- cspy 1.0.0
- node load when simultaneous distribution and collection (#79) is now accurate

### Fixed

- issues #79, #82, #84, #86

## [v0.3.0] - 10/11/2020

### Added

- JOSS paper
- Periodic CVRP scheduling option
- Initial solution for CVRP computed with Greedy Algorithm
- Diving heuristic (controlled with new parameter in `VehicleRoutingProblem.solve`)
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


[Unreleased]: https://github.com/Kuifje02/vrpy
[v0.2.0]: https://github.com/Kuifje02/vrpy/releases/tag/v0.2.0
[v0.3.0]: https://github.com/Kuifje02/vrpy/releases/tag/v0.3.0
[v0.4.0]: https://github.com/Kuifje02/vrpy/releases/tag/v0.4.0
[v0.5.0]: https://github.com/Kuifje02/vrpy/releases/tag/v0.5.0
[v0.5.1]: https://github.com/Kuifje02/vrpy/releases/tag/v0.5.1
