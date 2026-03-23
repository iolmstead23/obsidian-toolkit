# Mutable shared state for the vault_audit package.
# All modules import this module and access attributes via `state.ALIASES` etc.
# so that mutations are visible across modules.

ALIASES: dict = {}
_model        = None   # cached SentenceTransformer instance
_cached_pairs = None   # duplicate pairs from the last Option 2 run
