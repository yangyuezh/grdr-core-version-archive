# Later-Phase Access Architecture

Use this reference only when adding a representative adapter, federated query, or lawful local snapshot. GRDR's current foundation is the Data Source Registry, Dataset Knowledge Graph, and Agent Research Data Infrastructure.

## Separate knowledge from retrieval

The registry records what a source is, who maintains it, what it contains, how authoritative it is, and how it can be accessed.

An adapter performs actual retrieval. Knowing a source exists and being authorized to retrieve its records are different capabilities.

## Optional access modes

- `federated_access`: query the authoritative upstream API or bulk service.
- `local_snapshot`: keep a versioned copy only when licensing, privacy, cost, and scale permit.
- `controlled_access_pointer`: retain metadata and application instructions for restricted, commercial, sensitive, secure, or physical collections.

Do not equate “not copied locally” with “not included in GRDR.”

## Adapter requirements

Record the source and resource IDs, authentication, operations, formats, rate limits, last test, error state, and official documentation. Keep adapters source-specific and independently testable.

For the full optional architecture, read `/Users/jasper/Documents/codex/grdr/docs/ACCESS_ARCHITECTURE.md`.
