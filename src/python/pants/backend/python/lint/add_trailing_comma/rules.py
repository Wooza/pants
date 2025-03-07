# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from dataclasses import dataclass

from pants.backend.python.lint.add_trailing_comma.skip_field import SkipAddTrailingCommaField
from pants.backend.python.lint.add_trailing_comma.subsystem import AddTrailingComma
from pants.backend.python.target_types import PythonSourceField
from pants.backend.python.util_rules import pex
from pants.backend.python.util_rules.pex import PexRequest, VenvPex, VenvPexProcess
from pants.core.goals.fmt import FmtResult, FmtTargetsRequest
from pants.engine.fs import Digest
from pants.engine.internals.native_engine import Snapshot
from pants.engine.process import ProcessResult
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import FieldSet, Target
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel
from pants.util.strutil import pluralize


@dataclass(frozen=True)
class AddTrailingCommaFieldSet(FieldSet):
    required_fields = (PythonSourceField,)

    source: PythonSourceField

    @classmethod
    def opt_out(cls, tgt: Target) -> bool:
        return tgt.get(SkipAddTrailingCommaField).value


class AddTrailingCommaRequest(FmtTargetsRequest):
    field_set_type = AddTrailingCommaFieldSet
    name = AddTrailingComma.options_scope


@rule(desc="Format with add-trailing-comma", level=LogLevel.DEBUG)
async def add_trailing_comma_fmt(
    request: AddTrailingCommaRequest, add_trailing_comma: AddTrailingComma
) -> FmtResult:
    if add_trailing_comma.skip:
        return FmtResult.skip(formatter_name=request.name)
    add_trailing_comma_pex = await Get(VenvPex, PexRequest, add_trailing_comma.to_pex_request())

    result = await Get(
        ProcessResult,
        VenvPexProcess(
            add_trailing_comma_pex,
            argv=(
                "--exit-zero-even-if-changed",
                *add_trailing_comma.args,
                *request.snapshot.files,
            ),
            input_digest=request.snapshot.digest,
            output_files=request.snapshot.files,
            description=f"Run add-trailing-comma on {pluralize(len(request.field_sets), 'file')}.",
            level=LogLevel.DEBUG,
        ),
    )
    output_snapshot = await Get(Snapshot, Digest, result.output_digest)
    return FmtResult.create(request, result, output_snapshot, strip_chroot_path=True)


def rules():
    return [
        *collect_rules(),
        UnionRule(FmtTargetsRequest, AddTrailingCommaRequest),
        *pex.rules(),
    ]
