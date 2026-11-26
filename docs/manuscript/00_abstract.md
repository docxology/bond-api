# Abstract

{{BOND_IDENTITY}} (codename *{{BOND_CODENAME}}*) is the frozen mission
protocol contract for the BOND film suite — Layer 1 of the suite. It
defines {{BOND_NUM_DATACLASSES}} frozen dataclasses
({{BOND_PROTOCOL_DATACLASSES}}) and a {{BOND_NUM_PROVIDER_METHODS}}-method
provider contract ({{BOND_PROVIDER_METHODS}}) that every film package
implements.

The package ships the machinery every coordinator needs: deterministic JSON
round-trip serialization for all protocol objects, a gadget registry and a
mission/package registry for discovered providers, slug-based film discovery
on `sys.path`, and {{BOND_NUM_CAPABILITIES}} capability helpers
({{BOND_CAPABILITIES}}) layered on the frozen surface — soft brief
validation, plan-step schema checks, provenance hashing, and debrief
normalization. A reference film ({{BOND_REFERENCE_FILM}}) exercises the full
lifecycle, and the {{BOND_NUM_FILMS}} film packages of the suite implement the
same contract. Every artifact crosses process boundaries as tagged JSON
(reserved key `{{BOND_SERIALIZATION_TAG}}`), and the suite enforces a
{{BOND_COVERAGE_FLOOR}}% line-and-branch coverage floor on `src/`. This is
version {{BOND_VERSION}} of the contract.
