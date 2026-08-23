# Access and Storage Boundary

Use this reference when adding an adapter, federated query, or source snapshot. GRDR's broad registry can describe access without copying data; the Plan → Execute → Storage factory has a stricter completion rule.

## Separate knowledge from retrieval

The registry records what a source is, who maintains it, what it contains, how authoritative it is, and how it can be accessed.

An adapter performs actual retrieval. Knowing a source exists and being authorized to retrieve its records are different capabilities.

The three-step factory is the production plane. The independent GRDR Agent Runtime is the use plane. Storage packages the source adapter/runtime and proves its interface is callable; Core Runtime performs unified search, snapshot materialization, variable resolution, and retrieval.

## Optional access modes

- `federated_access`: query the authoritative upstream API or bulk service.
- `local_snapshot`: keep a versioned copy only when licensing, privacy, cost, and scale permit.
- `controlled_access_pointer`: retain metadata and application instructions for restricted, commercial, sensitive, secure, or physical collections.

Do not equate “not copied locally” with “not registered in GRDR.” Also do not equate registration with completed Storage: a three-step database project requires a complete snapshot, GitHub Release, matching Elements copy, central card, and Storage receipt.

## Adapter requirements

Record the source and resource IDs, authentication, operations, formats, rate limits, last test, error state, and official documentation. Keep adapters source-specific and independently testable.

For the full architecture, resolve Core through the bundled launcher and read `docs/ACCESS_ARCHITECTURE.md` under that Core root.
