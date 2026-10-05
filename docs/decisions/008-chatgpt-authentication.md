# ADR 008: supported ChatGPT sign-in and explicit usage limits

## Context

The developer prefers an existing ChatGPT subscription, a smaller model, and
capped usage. No API key is configured. Official documentation now supports
public-client plan use with explicit browser authorization. The developer chose
this mode; API-key calls would have separate billing.

## Decision

Implement the documented dynamic registration/OAuth flow against public OpenAI
endpoints, with loopback callback, state, nonce, PKCE, issued client ID, RS256
identity checks, permission validation, protected local storage, and serialized
rotating refresh. Use PyJWT/cryptography for verification rather than custom
cryptography. Declare the SDK's existing httpx transport as a direct dependency
for bounded auth and Kubernetes reads.

Pass the OAuth bearer credential to the normal Responses SDK adapter. Use the
account catalog and default to `gpt-6-luna`; never automatically upgrade. Keep
credentials separate from model context/audit. Enforce call, byte, reported-token,
and time limits. Explain that this preview cannot enforce an exact credit cap or
server output-token limit. Explicit API mode has known-price reservations and a
server output limit, capped at $1 per run by default.

## Alternatives

A separately billed API key remains optional. Reusing Codex's credential cache
or private backend routes would bypass this app's explicit consent and supported
contract. Building a full identity/product login system would exceed this phase.
Treating API prices as subscription credits would misrepresent cost.

## Rationale

This honors the developer's choice using the official direct flow. Established
JWT/HTTP libraries reduce security-critical custom code. Credential scope checks
separate identity from permission to consume plan usage. Smaller models and
transparent bounds keep costly evaluations deliberate.

## Consequences

Live authorization and account/model eligibility require the user. One account
per credential directory is supported initially. Preview restrictions and token
rotation require dedicated tests; interrupted streams may have unknown usage.
No live login or model diagnosis is claimed by fixture tests.

## Reconsider when

The preview contract changes, reliable account-level cost controls are available,
multiple user accounts become part of the product, or the developer explicitly
chooses separately billed API access. Verify official docs before changes.
