# Abstract

BOND-API ({{BOND_IDENTITY}}, codename *{{BOND_CODENAME}}*) is the frozen
mission protocol contract for the BOND film suite — Layer 1 of the suite. It
defines {{BOND_NUM_DATACLASSES}} frozen dataclasses
({{BOND_PROTOCOL_DATACLASSES}}) and a five-method provider contract
({{BOND_PROVIDER_METHODS}}) that every film package implements.

The package ships the machinery every coordinator needs: deterministic JSON
round-trip serialization for all protocol objects, a gadget registry and a
mission/package registry for discovered providers, and slug-based film
discovery on `sys.path`. A reference film (SABLE) exercises the full lifecycle.
This is version {{BOND_VERSION}} of the contract.
