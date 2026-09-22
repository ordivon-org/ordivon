#!/usr/bin/env python3
"""Compatibility facade for the Composition package.

Implementation authority moved to the public ordivon-composition package in Structure R2 S1A.
"""

from ordivon_composition.interface_contract_r2 import (
    currentness_standing,
    evaluate_interface,
    main,
)

__all__ = ["currentness_standing", "evaluate_interface"]

if __name__ == "__main__":
    raise SystemExit(main())
