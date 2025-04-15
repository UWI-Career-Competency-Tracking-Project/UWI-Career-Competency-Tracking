This directory contains the tests for the UWI Career Competency Tracking System, including unit tests, integration tests, acceptance tests, and performance tests.

## Test Structure

The test suite is organized into the following files:

- `test_unit.py` - Unit tests for individual components
- `test_integration.py` - Integration tests for component interactions
- `test_acceptance.py` - Acceptance tests for user stories
- `test_performance.py` - Performance tests for system behavior under load

## Dependencies

To run the tests, you need to install the test dependencies:

```bash
pip install pytest pytest-cov flask-testing
```

## Running Tests

### Running All Tests

To run all tests:

```bash
pytest -v
```

### Running Specific Test Types

To run only unit tests:

```bash
pytest -v App/tests/test_unit.py
```

To run only integration tests:

```bash
pytest -v App/tests/test_integration.py
```

To run only acceptance tests:

```bash
pytest -v App/tests/test_acceptance.py
```

To run only performance tests:

```bash
pytest -v App/tests/test_performance.py
```


## Test Plans

Detailed test plans for each test type are available in separate documentation:

- Unit Test Plan - Covers individual component functionality
- Integration Test Plan - Covers component interactions
- Acceptance Test Plan - Covers user stories and workflows
- Performance Test Plan - Covers system performance metrics and thresholds 