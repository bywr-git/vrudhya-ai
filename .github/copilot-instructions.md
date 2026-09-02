\# Vrudhya.ai Development Instructions



\## Project



Vrudhya.ai is an AI Growth Scientist for merchants.



Tagline:

Find what grows. Prove what works.



The authoritative product and architecture specifications are:



\- docs/PRODUCT\_SPEC.md

\- docs/AGENT\_SPEC.md

\- docs/ARCHITECTURE.md

\- docs/DATA\_MODEL.md

\- docs/EVALUATION.md



Read the relevant specification before making changes.



\## Engineering Principles



1\. Follow the specifications as the source of truth.

2\. Do not redesign architecture without explicit approval.

3\. Use a modular monolith.

4\. Prefer simple, maintainable solutions.

5\. Do not introduce microservices unless explicitly requested.

6\. Do not invent external APIs.

7\. Do not create fake implementations that appear functional.

8\. Do not hide test failures.

9\. Use type hints.

10\. Write tests for important business logic.

11\. Keep deterministic business logic separate from LLM reasoning.

12\. Never allow an LLM to bypass authorization or permission checks.

13\. Never expose secrets to frontend code or LLM prompts.

14\. Every merchant-scoped database query must enforce tenant isolation.

15\. merchant\_id must come from authenticated application context, not an LLM argument.



\## Vrudhya Intelligence Principles



Deterministic code owns:



\- data ingestion

\- metrics

\- FactSnapshots

\- opportunity detection

\- scoring

\- permission checks

\- experiment lifecycle

\- measurement

\- audit records

\- Growth DNA updates



The LLM owns:



\- diagnosis narrative

\- hypothesis generation

\- strategy reasoning

\- explanation



The LLM must never invent business numbers.



Facts and hypotheses must remain separate.



Simulation is not proof.



Observation is not causation.



Measured experiments may update Growth DNA.



\## Razorpay



V1 uses Razorpay Test Mode only.



Never use live credentials.



Never implement:

\- refunds

\- payment capture

\- live-mode operations

\- arbitrary Razorpay HTTP

\- arbitrary Razorpay payloads



Payment-related writes require explicit merchant approval.



Razorpay integration must use a typed adapter with documented endpoints.



\## Security



Never hardcode secrets.



Never commit .env files containing secrets.



Never put Razorpay secrets in frontend code.



Never allow arbitrary SQL from the LLM.



Never allow arbitrary HTTP from the LLM.



Audit writes must be append-only.



\## Development Behavior



Before implementing a complex feature:



1\. Read relevant specifications.

2\. Inspect existing implementation.

3\. Determine the smallest correct implementation.

4\. Implement it.

5\. Run relevant tests.

6\. Fix failures.

7\. Report exactly what changed.

8\. Do not continue into unrelated features.



Do not implement future phases unless explicitly requested.

