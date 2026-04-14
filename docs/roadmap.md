# Roadmap

## Guiding direction

PyDAVE should grow in two complementary directions:
- stronger core wrapper quality
- cleaner integration surfaces for real applications

## Near term

1. Stabilize documentation.
2. Clarify public versus internal APIs.
3. Add more examples for common flows.
4. Reduce rough edges in error handling and tracing.

## Medium term

1. Add richer high-level helpers for session orchestration.
2. Improve test coverage and fixture structure.
3. Add CI-friendly build and smoke paths where possible.
4. Separate Discord-specific integration into a clearly labeled module or companion package.

## Long term

1. Support broader platform guidance.
2. Improve packaging and publishing story.
3. Decide whether a future compiled extension or `cffi` path adds enough value to justify complexity.
4. Build robust integration examples for real client applications.

## Non-goals for now

- pretending the API is fully stable
- over-abstracting the low-level DAVE model before enough real integrations exist
- locking the project too early into a single Discord library or framework
