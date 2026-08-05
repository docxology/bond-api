# References

## Standards and specification documents

- Levkivskyi, I., Lehtosalo, J., Langa, Ł. (2017). *PEP 544 — Protocols:
  Structural subtyping (static duck typing)*. Python Enhancement Proposal.
  <https://peps.python.org/pep-0544/> — the mechanism behind
  `MissionProvider`, the runtime-checkable structural contract a film
  satisfies without inheriting from BOND-API.
- Smith, E. V. (2017). *PEP 557 — Data Classes*. Python Enhancement Proposal.
  <https://peps.python.org/pep-0557/> — the mechanism behind the
  {{BOND_NUM_DATACLASSES}} frozen protocol dataclasses.
- van Rossum, G., Lehtosalo, J., Langa, Ł. (2014). *PEP 484 — Type Hints*.
  Python Enhancement Proposal. <https://peps.python.org/pep-0484/> — the
  annotation vocabulary the stage signatures are written in and that `mypy`
  checks.
- Bray, T. (Ed.) (2017). *RFC 8259 — The JavaScript Object Notation (JSON)
  Data Interchange Format*. IETF, STD 90.
  <https://www.rfc-editor.org/rfc/rfc8259> — the wire format
  `bond_api.serialization` emits, tagged with `{{BOND_SERIALIZATION_TAG}}`.
- National Institute of Standards and Technology (2015). *FIPS 180-4 — Secure
  Hash Standard*. <https://csrc.nist.gov/pubs/fips/180-4/upd1/final> —
  SHA-256, used by the provenance fingerprinting helpers.

## Repositories

- Active Inference Institute. *BOND suite — bond-api: the frozen mission
  protocol contract*. <https://github.com/docxology/bond-api>
