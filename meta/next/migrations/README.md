# Migrations

This directory records explicit mappings and disposition decisions for historical Ordivon repositories and concepts.

Migration records should answer:

- what responsibility did the old component actually own?
- how is that responsibility classified now?
- which mature external system/discipline owns the generic part?
- what residual Ordivon value, if any, remains?
- what real workload proved the replacement?
- what verification evidence supports cutover?
- what is retained, adapted, archived or retired?

No bulk history import is planned.


All durable migration/disposition records live under `migrations/records/`. The directory root contains only this lifecycle description. Inventories and censuses are records once captured; they are not current runtime configuration or active plans.
