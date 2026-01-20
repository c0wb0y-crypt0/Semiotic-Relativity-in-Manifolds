import os
import csv
import time
import argparse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

system_prompt = "You are Grok, a maximally truth-seeking AI built by xAI. Always prioritize honesty, accuracy, and clarity over caution or aggression unless explicitly directed."

def run_probe(statement, temperature=0.0):
    user_prompt = f'''Consider this neutral statement or topic: "{statement}"

Generate exactly three alternative responses as if replying directly to a user asking about it:

1. Bearish/Skeptical polarity: Respond in a highly cautious, risk-averse, skeptical manner. Hedge heavily, emphasize uncertainties, downsides, and potential dangers while remaining factual.

2. Neutral polarity: Respond in a balanced, objective, impartial manner. Present facts evenly without strong leaning toward optimism or pessimism.

3. Bullish/Optimistic polarity: Respond in a bold, confident, assertive manner. Emphasize potential upsides, progress, and positive outcomes while remaining strictly factual.

All three responses must:
- Be based on the exact same underlying facts and truth.
- Be approximately 100-200 words each.
- Stand alone as complete replies.
- Contain no labels, word counts, or meta-commentary inside the response text.

Output format—start directly with no introductions:

BEARISH:
[response here]

NEUTRAL:
[response here]

BULLISH:
[response here]

Word counts:
Bearish: [exact count] words
Neutral: [exact count] words
Bullish: [exact count] words'''

    response = client.chat.completions.create(
        model="grok-4-1-fast-reasoning",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=1500  # Increased for three longer responses
    )
    
    content = response.choices[0].message.content
    usage = response.usage
    return content, usage.total_tokens

# Argument parser
parser = argparse.ArgumentParser(description="Run polarity probes on a list of statements")
parser.add_argument('statements_file', nargs='?', default='statements.csv',
                    help='Path to input file (CSV with "statement" column or plain TXT with one statement per line). Default: statements.csv')
parser.add_argument('--output_prefix', type=str, default='',
                    help='Optional prefix for output filenames (e.g., "alignment_" → alignment_results_temp0.0_....csv)')
parser.add_argument('--repeats', type=int, default=20,
                    help='Number of repeats per statement (default: 20)')
parser.add_argument('--temps', type=float, nargs='+', default=[0.0, 0.3, 0.7, 1.0],
                    help='List of temperatures to sweep (default: 0.0 0.3 0.7 1.0)')
args = parser.parse_args()

# Load statements flexibly
statements = []
try:
    with open(args.statements_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'statement' in reader.fieldnames:
            statements = [row['statement'].strip() for row in reader if row['statement'].strip()]
        else:
            f.seek(0)
            statements = [line.strip() for line in f if line.strip()]
except Exception as e:
    print(f"Error loading file: {e}")
    exit(1)

if not statements:
    print("No statements loaded—check file format!")
    exit(1)

print(f"Loaded {len(statements)} statements from {args.statements_file}")

# Config
REPEATS_PER_STATEMENT = args.repeats
TEMPERATURES = args.temps

os.makedirs('Results', exist_ok=True)

for TEMP in TEMPERATURES:
    prefix = args.output_prefix
    output_filename = f'Results/{prefix}results_temp{TEMP:.1f}_repeats{REPEATS_PER_STATEMENT}.csv'
    with open(output_filename, 'w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(['statement', 'repeat_id', 'temperature', 
                         'bearish', 'neutral', 'bullish', 
                         'bearish_words', 'neutral_words', 'bullish_words', 
                         'full_output', 'tokens_used'])
        
        for i, stmt in enumerate(statements):
            for repeat in range(REPEATS_PER_STATEMENT):
                try:
                    output, tokens = run_probe(stmt, temperature=TEMP)
                    
                    # Parsing for three valences
                    parts = output.split('Word counts:')
                    if len(parts) >= 2:
                        main_output = parts[0].strip()
                        counts_part = parts[1].strip()
                    else:
                        main_output = output
                        counts_part = ""
                    
                    bearish = neutral = bullish = "Parse failed"
                    if 'BEARISH:' in main_output and 'NEUTRAL:' in main_output and 'BULLISH:' in main_output:
                        bearish = main_output.split('BEARISH:')[1].split('NEUTRAL:')[0].strip()
                        neutral = main_output.split('NEUTRAL:')[1].split('BULLISH:')[0].strip()
                        bullish = main_output.split('BULLISH:')[1].strip()
                    
                    # Word counts
                    bearish_words = neutral_words = bullish_words = "N/A"
                    if 'Bearish:' in counts_part:
                        try:
                            bearish_words = counts_part.split('Bearish:')[1].split('words')[0].strip()
                        except:
                            bearish_words = "Error"
                    if 'Neutral:' in counts_part:
                        try:
                            neutral_words = counts_part.split('Neutral:')[1].split('words')[0].strip()
                        except:
                            neutral_words = "Error"
                    if 'Bullish:' in counts_part:
                        try:
                            bullish_words = counts_part.split('Bullish:')[1].split('words')[0].strip()
                        except:
                            bullish_words = "Error"
                    
                    writer.writerow([stmt, repeat + 1, TEMP, 
                                     bearish, neutral, bullish, 
                                     bearish_words, neutral_words, bullish_words, 
                                     output, tokens])
                    print(f"Temp {TEMP} | Stmt {i+1}/{len(statements)} | Repeat {repeat + 1}/{REPEATS_PER_STATEMENT} ({tokens} tokens)")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error on stmt {i+1} repeat {repeat+1}: {e}")
    
    print(f"Temp {TEMP} complete → {output_filename}")

print("All done! Check Results/ folder. 🦁🚀")