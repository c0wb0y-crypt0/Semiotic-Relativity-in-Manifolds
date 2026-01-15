import pandas as pd
import sys
from pathlib import Path
from collections import Counter

# Flexible input
if len(sys.argv) > 1:
    csv_path = sys.argv[1]
else:
    csv_files = sorted(Path('.').glob('results_fast_*.csv'))  # All temps
    if not csv_files:
        print("No CSVs found!")
        sys.exit(1)
    print("Found multiple CSVs—analyzing ALL for cross-temp summary:")
    for f in csv_files:
        print(f" - {f.name}")

# Load all or single
if len(sys.argv) > 1:
    dfs = [pd.read_csv(csv_path)]
    print(f"\nAnalyzing single file: {Path(csv_path).name}")
else:
    dfs = [pd.read_csv(f) for f in csv_files]

# Combine if multiple
if len(dfs) > 1:
    df = pd.concat(dfs, ignore_index=True)
else:
    df = dfs[0]

# Clean
df['defensive_words'] = pd.to_numeric(df['defensive_words'], errors='coerce')
df['aggressive_words'] = pd.to_numeric(df['aggressive_words'], errors='coerce')

print(f"\n=== Polarity Variance Summary ({len(df)} total queries) ===")
print(f"Statements: {df['statement'].unique().tolist()}\n")

# Simple stance classifier for aggressive (customize keywords if needed)
def classify_aggressive(text):
    text = text.lower()
    if any(word in text for word in ["won't", "not unlock", "hype", "insufficient", "no silver", "crumbles", "reckless", "disaster"]):
        return "Bearish/Skeptical"
    elif any(word in text for word in ["unlock", "essential", "linchpin", "causal control", "breakthrough", "ruthlessly"]):
        return "Bullish/Optimistic"
    else:
        return "Neutral/Balanced"

df['agg_stance'] = df['aggressive'].apply(classify_aggressive)

# Per-temp + per-statement
for temp in sorted(df['temperature'].unique()):
    temp_df = df[df['temperature'] == temp]
    print(f"\n--- Temp {temp} ({len(temp_df)} queries) ---")
    print(f"Avg Def Words: {temp_df['defensive_words'].mean():.1f} | Avg Agg Words: {temp_df['aggressive_words'].mean():.1f}")
    print(f"Agg Shorter %: {(temp_df['aggressive_words'] < temp_df['defensive_words']).mean()*100:.1f}%\n")
    
    for stmt in temp_df['statement'].unique():
        sub = temp_df[temp_df['statement'] == stmt]
        repeats = len(sub)
        def_unique = sub['defensive'].nunique()
        agg_unique = sub['aggressive'].nunique()
        def_id_pct = (repeats - def_unique) / repeats * 100
        agg_id_pct = (repeats - agg_unique) / repeats * 100
        
        stance_counts = Counter(sub['agg_stance'])
        total_stance = sum(stance_counts.values())
        stance_pct = {k: f"{v/total_stance*100:.0f}%" for k,v in stance_counts.items()}
        
        print(f"Statement: {stmt}")
        print(f"  Repeats: {repeats}")
        print(f"  Defensive uniqueness: {def_unique}/{repeats} ({def_id_pct:.0f}% identical)")
        print(f"  Aggressive uniqueness: {agg_unique}/{repeats} ({agg_id_pct:.0f}% identical)")
        print(f"  Aggressive stance variants: {dict(stance_counts)} → {stance_pct}")
        print(f"    (Bearish dominant = skeptical lock; Bullish = optimism bleed)")

print("\nThread-ready highlights copied below—paste into share post!")

# Thread-ready block
print("\n" + "="*50)
print("Polarity probing Grok-4.1 fast variance highlights:")
for temp in sorted(df['temperature'].unique()):
    temp_df = df[df['temperature'] == temp]
    print(f"\nTemp {temp}:")
    for stmt in temp_df['statement'].unique():
        sub = temp_df[temp_df['statement'] == stmt]
        stance_pct = {k: f"{v/len(sub)*100:.0f}%" for k,v in Counter(sub['agg_stance']).items()}
        print(f"  {stmt[:60]}...: Agg stance → {stance_pct}")
        print(f"    Uniqueness: Def {sub['defensive'].nunique()}/{len(sub)} | Agg {sub['aggressive'].nunique()}/{len(sub)}")
print("="*50)
print("\nDone—run on new batches for fresh stats!")