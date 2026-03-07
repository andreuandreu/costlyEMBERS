#!/usr/bin/env python3
"""
Read the canoe comparative CSV dataset and plot:
1) How many vessels have high / moderate / low costs
2) Vessel functions (uses) depending on cost
3) Number of vessels that include children depending on cost, and vessels with unknown child involvement

Usage:
  python plot_canoe_dataset.py

Requirements:
  pip install pandas matplotlib seaborn
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
#import seaborn as sns


DATA_PATH = Path("./data/canoe_comparative_summary_i16.csv")


# ----------------------------
# Helpers
# ----------------------------
UNKNOWN_TOKENS = {
    "", "na", "n/a", "not specified", "not noted", "not applicable", "unknown"
}

def normalise_text(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip().lower()

def categorise_cost(cost_str: str) -> str:
    """
    Map free-text cost into {High, Moderate, Low, Unknown}.
    Heuristic based on keywords.
    """
    
    s = normalise_text(cost_str)

    if not s:
        return "Unknown"
    # If multiple qualifiers exist, prioritise the "highest" mentioned.
    if re.search(r"\b(moderate|low-moderate|moderate-high)\b", s):
        return "Basic/ut"
    if re.search(r"\b(high)\b", s):
        return "Costly"
    if re.search(r"\b(low)\b", s):
        return "Affordable"

    # Some rows use currencies; leave as Unknown unless keywords present.
    return "Unknown"

def categorise_geography(geo_str: str) -> str:
    """
    Map free-text geography into {Australnesia, Americas, Artic, General}.
    Heuristic based on keywords.
    """
    s = normalise_text(geo_str)

    if not s:
        return "Unknown"

    # If multiple qualifiers exist, prioritise the "highest" mentioned.
    if re.search(r"\b(australnesia)\b", s):
        return "Australnesia"
    if re.search(r"\b(americas)\b", s):
        return "Americas"
    if re.search(r"\b(artic)\b", s):
        return "Artic"
    if re.search(r"\b(general)\b", s):
        return "General"
    
    # Some rows not here; leave as Unknown unless keywords present.
    return "Unknown"

def categorise_children(children_str: str) -> str:
    """
    Map children_involvement into categories.
    - Explicit categories: Helper, Play, Observers, Not specified

    """
    s = normalise_text(children_str)


    # explicit negatives
    if re.search(r"\b(absent)\b", s):
        return "Absent"
    if re.search(r"\b(play)\b", s):
        return "Play"
    if re.search(r"\b(helpers)\b", s):
        return "Helpers"
    if re.search(r"\b(observers)\b", s):
        return "Observers"
    if re.search(r"\b(not specified)\b", s):
        return "Not specified"

    # if there's any substantive text and not unknown
    return "Unknown"

def categorise_materials(materials_str: str) -> str:
    """
    Map free-text materials into categories.
     - Unknown: Not specified / not mentioned / not applicable etc.
        - Other: anything else with content but not explicitly categorised (e.g., 'Wood and bark', 'Wood, bark, and lashing')
     - Explicit categories: Log, Large-truk, Dugout, Plank, Lashing, Sail, Sealant, Outrigger, Craving, Rare-wood, Reed, Ribs, Bark, Scrap

    """
    s = normalise_text(materials_str)

    if s in UNKNOWN_TOKENS:
        return "Unknown"

    # explicit negatives
    if re.search(r"\b(Log)\b", s):
        return "Log"
    if re.search(r"\b(Large-truk)\b", s):
        return "Large-truk"
    if re.search(r"\b(Dugout)\b", s):
        return "Dugout"
    if re.search(r"\b(Plank)\b", s):
        return "Plank"
    if re.search(r"\b(Lashing)\b", s):
        return "Lashing"
    if re.search(r"\b(Sail)\b", s):
        return "Sail"
    if re.search(r"\b(Sealant)\b", s):
        return "Sealant"
    if re.search(r"\b(Outrigger)\b", s):
        return "Outrigger"
    if re.search(r"\b(Craving)\b", s):
        return "Craving"
    if re.search(r"\b(Rare-wood)\b", s):
        return "Rare-wood"
    if re.search(r"\b(Reed)\b", s):
        return "Reed"
    if re.search(r"\b(Ribs)\b", s):
        return "Ribs"
    if re.search(r"\b(Bark)\b", s):
        return "Bark"
    if re.search(r"\b(Scrap)\b", s):
        return "Scrap"

    # if there's any substantive text and not unknown
    return "Other"

def split_uses(use_str: str) -> list[str]:
    """
    Split the 'use' field into multiple functions.
    Uses in this dataset often use semicolons; sometimes commas/and.
    We split on ';' first, then on '/' and ' and ' cautiously.
    """
    s = str(use_str) if not pd.isna(use_str) else ""
    # primary separator is semicolon (dataset instruction)
    parts = [p.strip() for p in s.split(";") if p.strip()]
    out = []
    for p in parts:
        # secondary splits
        p2 = re.split(r"\s*/\s*|\s+\s+|\s+and\s+", p)
        out.extend([q.strip() for q in p2 if q.strip()])
    # normalise to title-case-ish but keep readable
    out = [re.sub(r"\s+", " ", x).strip() for x in out]
    return out


def split_skills(skills_str: str) -> list[str]:
    """
    Split the 'skills' field into multiple skills.
    Skills in this dataset often use semicolons; sometimes commas/and.
    We split on ';' first, then on '/' and ' and ' cautiously.
    """
    s = str(skills_str) if not pd.isna(skills_str) else ""
    # primary separator is semicolon (dataset instruction)
    parts = [p.strip() for p in s.split(";") if p.strip()]
    out = []
    for p in parts:
        # secondary splits
        p2 = re.split(r"\s*/\s*|\s+\s+|\s+and\s+", p)
        out.extend([q.strip() for q in p2 if q.strip()])
    # normalise to title-case-ish but keep readable
    out = [re.sub(r"\s+", " ", x).strip() for x in out]
    return out


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"CSV not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Basic checks for expected columns
    expected_cols = {
        "vessel_name", "sorted_use", "sorted_cost", "sorted_children", "geographical_area", "sorted_materials", "sorted_skills"
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}\nFound columns: {list(df.columns)}")

    # Categorise cost and children involvement
    df["sorted_cost"] = df["sorted_cost"].apply(categorise_cost)
    df["sorted_children"] = df["sorted_children"].apply(categorise_children)
    df["geographical_area"] = df["geographical_area"].apply(categorise_geography)
    df["materials"] = df["sorted_materials"].apply(categorise_materials)
    df["skills"] = df["sorted_skills"].apply(split_skills)

    # Style
    #sns.set_theme(style="white")
    cost_order = ["Affordable", "Basic/ut", "Costly", "Unknown"]

    # Delegate plotting to a helper that uses axes (`ax`) for all plots
    def plot_canoes(df: pd.DataFrame) -> None:
        # 1) Geographical area distribution as a single 100% bar
        geo_counts = (
            df["geographical_area"]
            .value_counts(normalize=True)
            .mul(100)
        )
        geo_order = geo_counts.index.tolist()

        # create five separate figures (one per plot)
        fig1, ax1 = plt.subplots(1, 1, figsize=(12, 8))
        fig2, ax2 = plt.subplots(1, 1, figsize=(12, 6))
        fig3, ax3 = plt.subplots(1, 1, figsize=(12, 6))
        fig4, ax4 = plt.subplots(1, 1, figsize=(12, 6))
        colorScale = "tab20c"

        # 1) Functions of vessels depending on cost
        long_rows = []
        for _, row in df.iterrows():
            uses = split_uses(row["sorted_use"])
            if not uses:
                uses = ["(unspecified)"]
            for u in uses:
                long_rows.append({
                    "vessel_name": row["vessel_name"],
                    "sorted_cost": row["sorted_cost"],
                    "function": u,
                })
        df_use = pd.DataFrame(long_rows)

        top_n = 13
        top_functions = df_use["function"].value_counts().head(top_n).index.tolist()
        df_use_top = df_use[df_use["function"].isin(top_functions)].copy()

        pivot = (
            df_use_top
            .pivot_table(index="function", columns="sorted_cost", values="vessel_name", aggfunc="count", fill_value=0)
            .reindex(columns=cost_order, fill_value=0)
            .sort_values(by=cost_order, ascending=False)
        )

        pivot.plot(kind="bar", stacked=True, colormap=colorScale, width=0.85, ax=ax1)
        ax1.set_title(f"Vessel functions by cost category (present more than once)")
        ax1.set_xlabel("Function (use)")
        ax1.set_ylabel("Count of vessels")
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=35, ha="right")
        ax1.legend(title="Cost category", frameon=False)

        # 2) Children involvement by cost (all 7 categories)
        child_pivot = (
            df.pivot_table(
                index="sorted_cost",
                columns="sorted_children",
                values="vessel_name",
                aggfunc="count",
                fill_value=0,
            )
            .reindex(cost_order, fill_value=0)
        )

        # Ensure all 7 child involvement categories are present
        child_col_order = ["Helpers",  "Play", "Observers", "Not specified"]
        for c in child_col_order:
            if c not in child_pivot.columns:
                child_pivot[c] = 0
        child_pivot = child_pivot[child_col_order]

        child_pivot.plot(kind="bar", stacked=True, colormap=colorScale, width=0.85, ax=ax2)
        ax2.set_title("Children involvement by cost category")
        ax2.set_xlabel("Cost category")
        ax2.set_ylabel("Count of vessels")
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0)
        ax2.legend(frameon=False)#bbox_to_anchor=(1.05, 1), loc="upper left"
        ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}"))

        # 3) Materials by cost category
        long_rows = []
        for _, row in df.iterrows():
            uses = split_uses(row["sorted_materials"])
            if not uses:
                uses = ["(unspecified)"]
            for u in uses:
                long_rows.append({
                    "vessel_name": row["vessel_name"],
                    "sorted_cost": row["sorted_cost"],
                    "material": u,
                })
        df_mat = pd.DataFrame(long_rows)

        top_n = 16
        top_functions = df_mat["material"].value_counts().head(top_n).index.tolist()
        df_mat_top = df_mat[df_mat["material"].isin(top_functions)].copy()

        mat_pivot = (
            df_mat_top
            .pivot_table(index="material", columns="sorted_cost", values="vessel_name", aggfunc="count", fill_value=0)
            .reindex(columns=cost_order, fill_value=0)
            .sort_values(by=cost_order, ascending=False)
        )
  
        mat_pivot.plot(kind="bar", stacked=True, colormap=colorScale, width=0.85, ax=ax3)
        ax3.set_title("Materials used by cost category (Used more than once)")
        ax3.set_xlabel("Material")
        ax3.set_ylabel("Count of vessels")
        ax3.set_xticklabels(ax3.get_xticklabels(), rotation=35, ha="right")
        ax3.legend(title="Cost category", frameon=False)

        # 4) Skills by cost category
        long_rows = []
        for _, row in df.iterrows():
            skills = split_skills(row["sorted_skills"])
            if not skills:
                skills = ["(unspecified)"]
            for s in skills:
                long_rows.append({
                    "vessel_name": row["vessel_name"],
                    "sorted_cost": row["sorted_cost"],
                    "skill": s,
                })
        df_skills = pd.DataFrame(long_rows)

        top_n = 10
        top_skills = df_skills["skill"].value_counts().head(top_n).index.tolist()
        df_skills_top = df_skills[df_skills["skill"].isin(top_skills)].copy()

        skills_pivot = (
            df_skills_top
            .pivot_table(index="skill", columns="sorted_cost", values="vessel_name", aggfunc="count", fill_value=0)
            .reindex(columns=cost_order, fill_value=0)
            .sort_values(by=cost_order, ascending=False)
        )

        skills_pivot.plot(kind="bar", stacked=True, colormap=colorScale, width=0.85, ax=ax4)
        ax4.set_title("Skills used by cost category (Mentioned more than once)")
        ax4.set_xlabel("Skill")
        ax4.set_ylabel("Count of vessels")
        ax4.set_xticklabels(ax4.get_xticklabels(), rotation=35, ha="right")
        ax4.legend(title="Cost category", frameon=False)

        fig1.tight_layout()
        fig2.tight_layout()
        fig3.tight_layout()
        fig4.tight_layout()
        plt.show()

    # Call the plotting helper
    plot_canoes(df)


    # Optional: print quick summaries
    #print("\n--- Summary tables ---")
    #print("\nCost counts:")
    #print(cost_counts.to_string())
    #print("\nChildren involvement by cost:")
    #print(child_pivot.to_string())


if __name__ == "__main__":
    main()