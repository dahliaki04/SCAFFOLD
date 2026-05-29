"""L1-39: Auto-derive SubGroups from a Priority column on BOM Structure.

When the optional ``Priority`` column is populated, the tool treats
multiple priority-tagged children of the same parent as a substitution
group — the consultant doesn't have to invent ``SubGroup`` names by
hand. The Priority-1 child is the preferred alternate; higher
priorities are fallbacks.

The derivation is purely additive:

* Rows with no ``Priority`` are untouched.
* Rows with a manual ``SubGroup`` already set are left alone — manual
  classification beats auto-derivation. Priority is preserved as
  metadata in that case.
* For each parent ``(AssemblyName, AssemblySite)`` whose remaining
  priority-tagged rows number 2 or more, a deterministic SubGroup
  name is assigned:

      AUTO-SG-{AssemblyName}-{AssemblySite}

  and ``UsageShare`` is filled in as 1.0 for the Priority-1 row and
  0.0 for all higher priorities, satisfying the L1-03 sum-to-1.0 rule.

Run *after* :func:`local.core.validation.validate_priority` and
*before* graph construction in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

AUTO_SUBGROUP_PREFIX = "AUTO-SG-"


@dataclass
class SubGroupProposal:
    """One auto-derived SubGroup, for display in validated.xlsx / reports."""

    parent_part: str
    parent_site: str
    subgroup_name: str
    members: list[tuple[str, str, int, float]]  # (component, site, priority, usage_share)


def _subgroup_name(parent_part: str, parent_site: str) -> str:
    return f"{AUTO_SUBGROUP_PREFIX}{parent_part}-{parent_site}"


def derive_subgroups_from_priority(
    bom_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[SubGroupProposal]]:
    """Fill in ``SubGroup`` and ``UsageShare`` for priority-tagged rows.

    Returns a 2-tuple of ``(modified_bom_df, proposals)``.

    * ``modified_bom_df`` is a copy of the input with new SubGroup and
      UsageShare values applied where appropriate. Original rows are
      unchanged if Priority is empty or SubGroup is already set.
    * ``proposals`` is a list of :class:`SubGroupProposal` for
      downstream surfaces (validated.xlsx readback, PDF report) so
      consultants can review the auto-derivation.

    The function is idempotent: running it twice yields the same output.
    """
    if "Priority" not in bom_df.columns:
        return bom_df.copy(), []

    out = bom_df.copy()
    if "SubGroup" not in out.columns:
        out["SubGroup"] = pd.NA
    if "UsageShare" not in out.columns:
        out["UsageShare"] = pd.NA

    # When the CSV input has SubGroup completely empty, pandas infers
    # float64 for the column. Assigning a string into a float64 cell
    # triggers a FutureWarning in pandas 2.x and will be a hard error
    # in pandas 3.x. Force object dtype so string assignment is clean.
    out["SubGroup"] = out["SubGroup"].astype(object)
    out["UsageShare"] = out["UsageShare"].astype(object)

    # Candidates: rows with a Priority AND no pre-existing manual SubGroup
    auto_eligible = out["Priority"].notna() & out["SubGroup"].isna()
    if not auto_eligible.any():
        return out, []

    proposals: list[SubGroupProposal] = []
    parent_groups = out[auto_eligible].groupby(
        ["AssemblyName", "AssemblySite"], sort=False
    )

    for (parent_name, parent_site), grp in parent_groups:
        if len(grp) < 2:
            continue  # single priority-tagged child is not a substitution group

        sg_name = _subgroup_name(parent_name, parent_site)
        ordered = grp.sort_values("Priority")

        members: list[tuple[str, str, int, float]] = []
        for idx, row in ordered.iterrows():
            share = 1.0 if int(row["Priority"]) == 1 else 0.0
            out.at[idx, "SubGroup"] = sg_name
            out.at[idx, "UsageShare"] = share
            members.append(
                (
                    row["ComponentName"],
                    row["ComponentSite"],
                    int(row["Priority"]),
                    share,
                )
            )

        proposals.append(
            SubGroupProposal(
                parent_part=parent_name,
                parent_site=parent_site,
                subgroup_name=sg_name,
                members=members,
            )
        )

    return out, proposals


def parts_with_alternates(bom_df: pd.DataFrame) -> set[str]:
    """Return the set of part names that belong to a SubGroup with 2+ members.

    Used by L1-13 single-source detection to exclude parts whose
    sourcing risk is already mitigated by an alternate component.
    Considers both manual and auto-derived SubGroups (the source
    doesn't matter for the risk question).
    """
    if "SubGroup" not in bom_df.columns:
        return set()

    sg_rows = bom_df[bom_df["SubGroup"].notna()]
    if sg_rows.empty:
        return set()

    multi_member_groups = (
        sg_rows.groupby("SubGroup")["ComponentName"]
        .nunique()
        .pipe(lambda s: s[s >= 2].index)
    )
    return set(
        sg_rows[sg_rows["SubGroup"].isin(multi_member_groups)]["ComponentName"]
    )
