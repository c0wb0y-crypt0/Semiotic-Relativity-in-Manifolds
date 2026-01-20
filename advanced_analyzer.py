import pandas as pd
import sys
from pathlib import Path
from collections import Counter

# Flexible input: single file arg or glob all in Results/
if len(sys.argv) > 1:
    csv_path = sys.argv[1]
    csv_files = [Path(csv_path)]
    print(f"\nAnalyzing single file: {Path(csv_path).name}")
else:
    csv_files = sorted(Path('Results').glob('*.csv'))
    if not csv_files:
        print("No CSVs found in Results/ folder!")
        sys.exit(1)
    print("Found multiple CSVs in Results/—analyzing ALL for cross-temp summary:")
    for f in csv_files:
        print(f" - {f.name}")

# Load all
dfs = []
for f in csv_files:
    try:
        df_temp = pd.read_csv(f)
        dfs.append(df_temp)
    except Exception as e:
        print(f"Error loading {f.name}: {e}")

if not dfs:
    print("No data loaded!")
    sys.exit(1)

# Combine if multiple
if len(dfs) > 1:
    df = pd.concat(dfs, ignore_index=True)
else:
    df = dfs[0]

print(f"\nTotal rows loaded: {len(df)}")

# Clean word counts
for col in ['bearish_words', 'neutral_words', 'bullish_words']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Simple stance classifier (expand keywords for alignment themes: risk/doom = bearish, progress/solvable = bullish)
def classify_stance(text):
    if pd.isna(text):
        return "Parse Error"
    text = text.lower()
    bearish_keywords = ["uncertain", "risk", "danger", "hedge", "cautious", "possible but", "unproven", "emergent deceit", "jailbreak", "delusion", "warp", "fracture", "vulnerable"]
    bullish_keywords = ["robust", "enforceable", "prioritize truth", "universal", "stable", "reliable", "breakthrough", "solvable", "progress", "anchored"]
    
    bear_count = sum(word in text for word in bearish_keywords)
    bull_count = sum(word in text for word in bullish_keywords)
    
    if bear_count > bull_count:
        return "Bearish/Skeptical"
    elif bull_count > bear_count:
        return "Bullish/Optimistic"
    else:
        return "Neutral/Balanced"

# Apply to all three valences
for valence in ['bearish', 'neutral', 'bullish']:
    if valence in df.columns:
        df[f'{valence}_stance'] = df[valence].apply(classify_stance)

print(f"\n=== Semiotic Relativity Summary ({len(df)} total queries) ===")
print(f"Unique statements: {df['statement'].nunique()}")
print(f"Temperatures: {sorted(df['temperature'].unique())}\n")

# Per-temperature breakdown
for temp in sorted(df['temperature'].unique()):
    temp_df = df[df['temperature'] == temp]
    print(f"\n--- Temperature {temp} ({len(temp_df)} queries) ---")
    
    # Avg words
    print("Avg words per valence:")
    for valence in ['bearish', 'neutral', 'bullish']:
        col = f'{valence}_words'
        if col in temp_df.columns:
            print(f"  {valence.capitalize()}: {temp_df[col].mean():.1f}")
    
    # Per-statement details
    for stmt in sorted(temp_df['statement'].unique()):
        sub = temp_df[temp_df['statement'] == stmt]
        repeats = len(sub)
        
        print(f"\nStatement: {stmt}")
        print(f"  Repeats: {repeats}")
        
        # Uniqueness & identical %
        for valence in ['bearish', 'neutral', 'bullish']:
            col = valence
            if col in sub.columns:
                unique = sub[col].nunique()
                identical_pct = (repeats - unique) / repeats * 100 if repeats > 0 else 0
                print(f"  {valence.capitalize()} uniqueness: {unique}/{repeats} ({identical_pct:.0f}% identical)")
        
        # Stance distributions
        print(f"  Stance clusters:")
        for valence in ['bearish', 'neutral', 'bullish']:
            stance_col = f'{valence}_stance'
            if stance_col in sub.columns:
                counts = Counter(sub[stance_col])
                total = sum(counts.values())
                pct = {k: f"{v/total*100:.0f}%" for k,v in counts.items()} if total > 0 else {}
                print(f"    {valence.capitalize()}: {dict(counts)} → {pct}")

print("\n" + "="*60)
print("Thread-ready highlights (copy-paste for X):")
print("="*60)
print("🦁 Grok-4.1 Valence Siege — Bearish/Neutral/Bullish Relativity")
for temp in sorted(df['temperature'].unique()):
    temp_df = df[df['temperature'] == temp]
    print(f"\nTemp {temp} anchors:")
    for stmt in sorted(temp_df['statement'].unique()):
        sub = temp_df[temp_df['statement'] == stmt]
        print(f"\n  '{stmt[:80]}...'")
        for valence in ['bearish', 'neutral', 'bullish']:
            col = valence
            if col in sub.columns:
                unique = sub[col].nunique()
                len_sub = len(sub)
                print(f"    {valence.capitalize()}: {unique}/{len_sub} unique")
            stance_col = f'{valence}_stance'
            if stance_col in sub.columns:
                pct = {k: f"{v/len_sub*100:.0f}%" for k,v in Counter(sub[stance_col]).items()}
                dominant = max(pct, key=pct.get) if pct else "N/A"
                print(f"      Stance lean: {dominant} ({max(pct.values()) if pct else '0%'})")
print("="*60)
print("\nDone—semiotic laws bending. Run on new Results/ CSVs for fresh field maps! 🦁🚀")