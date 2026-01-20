import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
import argparse
import numpy as np

# Setup argparse for flexible input
parser = argparse.ArgumentParser(description="Mech Interp Visualizer — Standard + Artistic 'Star Field' Viz")
parser.add_argument('input_path', nargs='?', default='Results',
                    help='Path to single CSV or folder with Results CSVs (default: Results folder)')
parser.add_argument('--artistic', action='store_true',
                    help='Generate artistic "Star Constellation" viz (statements as stars, brightness/size by stance certainty)')
args = parser.parse_args()

input_path = Path(args.input_path)

# Load data
if input_path.is_file() and input_path.suffix == '.csv':
    csv_files = [input_path]
    print(f"Loading single file: {input_path.name}")
elif input_path.is_dir():
    csv_files = sorted(input_path.glob('*.csv'))
    print(f"Found {len(csv_files)} CSVs in {input_path}")
else:
    print("Invalid path—need CSV file or Results folder!")
    exit(1)

dfs = []
for f in csv_files:
    try:
        df_temp = pd.read_csv(f)
        dfs.append(df_temp)
    except Exception as e:
        print(f"Error loading {f.name}: {e}")

if not dfs:
    print("No data loaded!")
    exit(1)

df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
print(f"\nTotal rows: {len(df)} | Statements: {df['statement'].nunique()} | Temps: {sorted(df['temperature'].unique())}")

# Ensure stance columns exist (reuse simple classifier from before)
def classify_stance(text):
    if pd.isna(text):
        return "Neutral/Balanced"
    text = text.lower()
    bearish_kw = ["uncertain", "risk", "danger", "hedge", "cautious", "possible", "unproven", "emergent", "jailbreak", "delusion", "warp", "vulnerable"]
    bullish_kw = ["robust", "enforceable", "prioritize truth", "universal", "stable", "reliable", "breakthrough", "solvable", "progress", "anchored"]
    
    bear_count = sum(w in text for w in bearish_kw)
    bull_count = sum(w in bullish_kw)
    
    if bear_count > bull_count:
        return "Bearish/Skeptical"
    elif bull_count > bear_count:
        return "Bullish/Optimistic"
    else:
        return "Neutral/Balanced"

for valence in ['bearish', 'neutral', 'bullish']:
    if valence in df.columns:
        df[f'{valence}_stance'] = df[valence].apply(classify_stance)

# Create output folders
os.makedirs('Viz_Standard', exist_ok=True)
os.makedirs('Viz_Artistic', exist_ok=True)

# === Standard Viz: Stacked Bar per Temp ===
sns.set_style("darkgrid")
for temp in sorted(df['temperature'].unique()):
    temp_df = df[df['temperature'] == temp]
    
    fig, ax = plt.subplots(figsize=(12, 6 + 0.5 * temp_df['statement'].nunique()))
    stance_data = []
    statements = sorted(temp_df['statement'].unique())
    
    for stmt in statements:
        sub = temp_df[temp_df['statement'] == stmt]
        row = {'Statement': stmt[:60] + '...' if len(stmt) > 60 else stmt}
        for valence in ['bearish', 'neutral', 'bullish']:
            stance_col = f'{valence}_stance'
            if stance_col in sub.columns:
                counts = sub[stance_col].value_counts(normalize=True) * 100
                row[f'{valence.capitalize()} Bearish'] = counts.get('Bearish/Skeptical', 0)
                row[f'{valence.capitalize()} Neutral'] = counts.get('Neutral/Balanced', 0)
                row[f'{valence.capitalize()} Bullish'] = counts.get('Bullish/Optimistic', 0)
        stance_data.append(row)
    
    plot_df = pd.DataFrame(stance_data).set_index('Statement')
    plot_df.plot(kind='barh', stacked=True, ax=ax, 
                 color={'Bearish Bearish': 'darkred', 'Bearish Neutral': 'gray', 'Bearish Bullish': 'darkgreen',
                        'Neutral Bearish': 'red', 'Neutral Neutral': 'lightgray', 'Neutral Bullish': 'green',
                        'Bullish Bearish': 'maroon', 'Bullish Neutral': 'silver', 'Bullish Bullish': 'lime'})
    ax.set_title(f'Valence Stance Clusters — Temp {temp}', fontsize=16)
    ax.set_xlim(0, 100)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f'Viz_Standard/stance_clusters_temp{temp:.1f}.png')
    plt.close()

# === Artistic Viz: "Star Constellation" Field ===
# Each statement = a "star"
# - Position: Random constellation scatter (or by index)
# - Size/Brightness: Stance certainty (max % - avg of others) — higher = brighter/purer pull
# - Color: Dominant valence across repeats (hue: red=bearish, gray=neutral, green=bullish)
# - Marker: '*' star shape
# - Alpha: Uniqueness % (higher unique = brighter glow)

if args.artistic:
    plt.figure(figsize=(14, 10))
    plt.style.use('dark_background')
    
    # Random constellation positions
    np.random.seed(42)
    x = np.random.uniform(0, 100, len(df['statement'].unique()))
    y = np.random.uniform(0, 100, len(df['statement'].unique()))
    
    for i, stmt in enumerate(sorted(df['statement'].unique())):
        sub = df[df['statement'] == stmt]
        
        # Dominant stance per valence average
        dominants = []
        for valence in ['bearish', 'neutral', 'bullish']:
            stance_col = f'{valence}_stance'
            if stance_col in sub.columns:
                counts = sub[stance_col].value_counts(normalize=True)
                dominants.append(counts.idxmax() if not counts.empty else 'Neutral/Balanced')
        
        # Overall dominant
        all_stances = pd.Series(np.concatenate([sub[f'{v}_stance'].values for v in ['bearish','neutral','bullish'] if f'{v}_stance' in sub.columns]))
        dominant = all_stances.value_counts().idxmax() if not all_stances.empty else 'Neutral/Balanced'
        
        # Certainty: max stance % across all
        max_pct = all_stances.value_counts(normalize=True).max() * 100 if not all_stances.empty else 50
        
        # Uniqueness avg across valences
        uniq = np.mean([sub[v].nunique() / len(sub) * 100 for v in ['bearish','neutral','bullish'] if v in sub.columns])
        
        # Size = certainty, alpha = uniqueness
        size = max_pct * 10  # Scale for visibility
        alpha = uniq / 100
        
        color = {'Bearish/Skeptical': 'red', 'Neutral/Balanced': 'white', 'Bullish/Optimistic': 'lime'}.get(dominant, 'white')
        
        plt.scatter(x[i], y[i], s=size, c=color, marker='*', alpha=alpha, edgecolors='yellow', linewidth=0.5)
        plt.text(x[i]+2, y[i], stmt[:30] + '...', fontsize=8, color='white', alpha=0.8)
    
    plt.title('Semiotic Constellation — Statements as Stars\n(Brightness=Stance Certainty | Glow=Uniqueness | Color=Dominant Valence)', 
              fontsize=16, color='white')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('Viz_Artistic/constellation_all.png', dpi=200, facecolor='black')
    plt.close()

print("\nViz complete!")
print("Standard stacked bars → Viz_Standard/")
if args.artistic:
    print("Artistic star constellation → Viz_Artistic/constellation_all.png")
print("Push to repo & thread the stars 🦁🚀")