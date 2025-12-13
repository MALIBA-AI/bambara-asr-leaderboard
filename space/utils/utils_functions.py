import pandas as pd
from datasets import load_dataset
from jiwer import wer, cer
import os
from datetime import datetime
import re
import numpy as np
import sys
import subprocess
from settings.models import Settings


def load_references():
    config = Settings()
    try:
        token = None
        if config.hf_token and str(config.hf_token).strip() and str(config.hf_token).strip().lower() != 'none':
            token = config.hf_token
        
        dataset = load_dataset(
            config.dataset_url,
            name=config.dataset_config,
            token=token
        )["eval"]
        return {row["id"]: row["text"] for row in dataset}
    except Exception as e:
        raise ValueError(f"Failed to load the dataset: {e}")


def mask_sensitive_info(text):
    if text is None:
        return text
    return re.sub(r'github_[a-zA-Z0-9]+', '***', text)


def run_command(cmd, check=True, capture_output=False):
    masked_cmd = [mask_sensitive_info(c) if '://' in c or 'github_' in c else c for c in cmd]
    print(f"Running: {' '.join(masked_cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=capture_output, text=True)
    if result.stdout and not capture_output:
        print(mask_sensitive_info(result.stdout))
    if result.stderr and not capture_output:
        print(mask_sensitive_info(result.stderr), file=sys.stderr)
    return result


def git_pull():
    run_command(["git", "pull"], check=True)


def git_add_commit_push(message):
    config = Settings()
    run_command(["git", "add", config.leaderboard_file])
    commit_result = run_command(["git", "commit", "-m", message], check=False)
    if commit_result.returncode == 0:
        run_command(["git", "push"], check=True)
    else:
        print("No changes to commit.")


def normalize_text(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def calculate_metrics(predictions_df, references):
    results = []
    total_ref_words = 0
    total_ref_chars = 0
    
    for _, row in predictions_df.iterrows():
        id_val = row["id"]
        if id_val not in references:
            continue
        
        reference = normalize_text(references[id_val])
        hypothesis = normalize_text(row["text"])
        
        if not reference or not hypothesis:
            continue
        
        reference_words = reference.split()
        reference_chars = list(reference)
        
        try:
            sample_wer = wer(reference, hypothesis)
            sample_cer = cer(reference, hypothesis)
        
            sample_wer = min(sample_wer, 2.0)
            sample_cer = min(sample_cer, 2.0)
        
            total_ref_words += len(reference_words)
            total_ref_chars += len(reference_chars)
        
            results.append({
                "id": id_val,
                "reference": reference,
                "hypothesis": hypothesis,
                "ref_word_count": len(reference_words),
                "ref_char_count": len(reference_chars),
                "wer": sample_wer,
                "cer": sample_cer
            })
        except Exception as e:
            print(f"Error processing sample {id_val}: {str(e)}")
            pass
    
    if not results:
        raise ValueError("No valid samples for WER/CER calculation")
    
    avg_wer = sum(item["wer"] for item in results) / len(results)
    avg_cer = sum(item["cer"] for item in results) / len(results)
    
    return avg_wer, avg_cer, results


def format_as_percentage(value):
    return f"{value * 100:.2f}%"


def calculate_combined_score(wer_val, cer_val, wer_weight=0.7, cer_weight=0.3):
    total_weight = wer_weight + cer_weight
    if total_weight > 0:
        wer_weight = wer_weight / total_weight
        cer_weight = cer_weight / total_weight
    else:
        wer_weight = 0.5
        cer_weight = 0.5
    return wer_val * wer_weight + cer_val * cer_weight


def format_model_name_with_link(model_name, license_type, model_url):
    if license_type == "Open Source" and model_url and model_url.strip():
        return f'<a href="{model_url}" target="_blank" style="color: #2f3b7d; text-decoration: none; font-weight: 600;">{model_name}</a>'
    return model_name


def add_medals_to_models(df, score_col="Combined_Score"):
    score_float_col = "__score_float"
    df[score_float_col] = df[score_col].apply(
        lambda x: float(x.replace('%', '')) if isinstance(x, str) and '%' in x else float(x) if x != "---" else np.nan
    )
    df = df.sort_values(by=score_float_col, ascending=True, kind="mergesort").reset_index(drop=True)
    
    def get_rank_symbols(scores):
        unique_scores = sorted(set([s for s in scores if not pd.isna(s)]))
        symbols = ["🏆", "🥈", "🥉"]
        score_to_symbol = {s: symbols[i] for i, s in enumerate(unique_scores[:3])}
        return [score_to_symbol.get(s, "") for s in scores]
    
    df['rank_symbol'] = get_rank_symbols(df[score_float_col].tolist())
    df['Model_Name'] = df['rank_symbol'] + ' ' + df['Model_Name'].astype(str)
    df = df.drop(columns=['rank_symbol', score_float_col])
    return df


def get_current_leaderboard():
    git_pull()
    config = Settings()
    leaderboard_file = config.leaderboard_file
    
    try:
        if os.path.exists(leaderboard_file):
            current_leaderboard = pd.read_csv(leaderboard_file)
            
            required_columns = ["Model_Name", "WER", "CER", "Combined_Score", "timestamp", "License", "Model_URL"]
            
            for col in required_columns:
                if col not in current_leaderboard.columns:
                    if col == "Combined_Score":
                        current_leaderboard["Combined_Score"] = current_leaderboard["WER"] * 0.7 + current_leaderboard["CER"] * 0.3
                    elif col == "License":
                        current_leaderboard["License"] = "Unknown"
                    elif col == "Model_URL":
                        current_leaderboard["Model_URL"] = ""
            
            if set(current_leaderboard.columns) != set(pd.read_csv(leaderboard_file).columns):
                current_leaderboard.to_csv(leaderboard_file, index=False)
                git_add_commit_push("Added License and Model_URL columns to leaderboard")
            
            return current_leaderboard
        else:
            return pd.DataFrame(columns=["Model_Name", "WER", "CER", "Combined_Score", "timestamp", "License", "Model_URL"])
    except Exception as e:
        print(f"Error getting leaderboard: {str(e)}")
        return pd.DataFrame(columns=["Model_Name", "WER", "CER", "Combined_Score", "timestamp", "License", "Model_URL"])


def prepare_leaderboard_for_display(df, sort_by="Combined_Score"):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Rank", "Model Name", "WER (%)", "CER (%)", "Combined Score (%)", "License", "Timestamp"])
    
    display_df = df.copy()
    display_df = display_df.sort_values(sort_by, ascending=True)
    display_df.insert(0, "Rank", range(1, len(display_df) + 1))
    
    for col in ["WER", "CER", "Combined_Score"]:
        if col in display_df.columns:
            display_df[f"{col} (%)"] = display_df[col].apply(lambda x: f"{x * 100:.2f}")
    
    display_df = display_df.rename(columns={
        "Model_Name": "Model Name",
        "timestamp": "Timestamp",
        "Combined_Score (%)": "Combined Score (%)"
    })
    
    display_cols = ["Rank", "Model Name", "WER (%)", "CER (%)", "Combined Score (%)", "License", "Timestamp"]
    display_df = display_df[[col for col in display_cols if col in display_df.columns]]
    
    return display_df


def df_to_html(df):
    if df.empty:
        return "<p>No data available</p>"
    df.columns.name = None
    html = df.to_html(index=False, escape=False)
    return html


def get_model_performance_table(model_name):
    current_lb = get_current_leaderboard()
    model_data = current_lb[current_lb['Model_Name'].str.contains(model_name, regex=False, na=False)]
    
    if model_data.empty:
        model_data = current_lb[current_lb['Model_Name'] == model_name]
    
    if model_data.empty:
        return pd.DataFrame([{"Info": f"No data available for model: {model_name}"}])
    
    model_row = model_data.iloc[0]
    
    license_info = model_row.get('License', 'Unknown')
    model_url = model_row.get('Model_URL', '')
    
    metrics_data = [
        ["Bambara ASR", "Word Error Rate (WER)", f"{model_row['WER'] * 100:.2f}%"],
        ["Bambara ASR", "Character Error Rate (CER)", f"{model_row['CER'] * 100:.2f}%"],
        ["Bambara ASR", "Combined Score (Default)", f"{model_row['Combined_Score'] * 100:.2f}%"],
        ["Model Info", "License", license_info],
    ]
    
    if license_info == "Open Source" and model_url:
        metrics_data.append(["Model Info", "Repository", f'<a href="{model_url}" target="_blank">{model_url}</a>'])
    
    table = pd.DataFrame(metrics_data, columns=["Category", "Metric", "Value"])
    return table


def compare_models(model_1_name, model_2_name):
    if model_1_name == model_2_name:
        return pd.DataFrame([{"Info": "Please select two different models to compare."}])
    
    current_lb = get_current_leaderboard()
    model1_data = current_lb[current_lb['Model_Name'] == model_1_name]
    model2_data = current_lb[current_lb['Model_Name'] == model_2_name]
    
    if model1_data.empty or model2_data.empty:
        return pd.DataFrame([{"Info": "One or both selected models have no data to compare."}])
    
    m1 = model1_data.iloc[0]
    m2 = model2_data.iloc[0]
    
    def format_diff(val1, val2):
        diff = val1 - val2
        if abs(diff) < 0.001:
            return f'<span style="color: #212529 !important;">{diff:.3f}</span>'
        elif diff > 0:
            return f'<span style="color: #dc3545 !important; font-weight: bold !important;">+{diff:.3f}</span>'
        else:
            return f'<span style="color: #28a745 !important; font-weight: bold !important;">{diff:.3f}</span>'
    
    comparison_data = [
        ["ASR Performance", "Word Error Rate (WER)", f"{m1['WER']:.3f}", f"{m2['WER']:.3f}", format_diff(m1['WER'], m2['WER'])],
        ["ASR Performance", "Character Error Rate (CER)", f"{m1['CER']:.3f}", f"{m2['CER']:.3f}", format_diff(m1['CER'], m2['CER'])],
        ["ASR Performance", "Combined Score", f"{m1['Combined_Score']:.3f}", f"{m2['Combined_Score']:.3f}", format_diff(m1['Combined_Score'], m2['Combined_Score'])],
        ["Model Info", "License", m1.get('License', 'Unknown'), m2.get('License', 'Unknown'), "---"],
    ]
    
    comp_df = pd.DataFrame(comparison_data, columns=["Category", "Metric", model_1_name, model_2_name, "Difference"])
    return comp_df


def process_submission(model_name, csv_file, references, license_type="Unknown", model_url=""):
    config = Settings()
    leaderboard_file = config.leaderboard_file
    
    if not model_name or not model_name.strip():
        return "Error: Please provide a model name.", None
    
    if not csv_file:
        return "Error: Please upload a CSV file.", None
    
 
    if license_type == "Open Source" and (not model_url or not model_url.strip()):
        return "Error: Please provide a HuggingFace model URL for open source models.", None
    
    if model_url and model_url.strip():
        if not (model_url.startswith("https://huggingface.co/") or model_url.startswith("http://huggingface.co/")):
            return "Error: Model URL must be a valid HuggingFace URL (https://huggingface.co/...).", None
    
    try:
        df = pd.read_csv(csv_file)
        
        if len(df) == 0:
            return "Error: Uploaded CSV is empty.", None
        
        if set(df.columns) != {"id", "text"}:
            return f"Error: CSV must contain exactly 'id' and 'text' columns. Found: {', '.join(df.columns)}", None
        
        if df["id"].duplicated().any():
            dup_ids = df[df["id"].duplicated()]["id"].unique()
            return f"Error: Duplicate IDs found: {', '.join(map(str, dup_ids[:5]))}", None
        
        missing_ids = set(references.keys()) - set(df["id"])
        extra_ids = set(df["id"]) - set(references.keys())
        
        if missing_ids:
            return f"Error: Missing {len(missing_ids)} IDs in submission. First few missing: {', '.join(map(str, list(missing_ids)[:5]))}", None
        
        if extra_ids:
            return f"Error: Found {len(extra_ids)} extra IDs not in reference dataset. First few extra: {', '.join(map(str, list(extra_ids)[:5]))}", None
        
        try:
            avg_wer, avg_cer, detailed_results = calculate_metrics(df, references)
            
            if avg_wer < 0.001:
                return "Error: WER calculation yielded suspicious results (near-zero). Please check your submission CSV.", None
            
        except Exception as e:
            return f"Error calculating metrics: {str(e)}", None
        
        git_pull()
        leaderboard = get_current_leaderboard()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        combined_score = avg_wer * 0.7 + avg_cer * 0.3
        
        if model_name in leaderboard["Model_Name"].values:
            idx = leaderboard[leaderboard["Model_Name"] == model_name].index
            leaderboard.loc[idx, "WER"] = avg_wer
            leaderboard.loc[idx, "CER"] = avg_cer
            leaderboard.loc[idx, "Combined_Score"] = combined_score
            leaderboard.loc[idx, "timestamp"] = timestamp
            leaderboard.loc[idx, "License"] = license_type
            leaderboard.loc[idx, "Model_URL"] = model_url if model_url else ""
            updated_leaderboard = leaderboard
        else:
            new_entry = pd.DataFrame(
                [[model_name, avg_wer, avg_cer, combined_score, timestamp, license_type, model_url if model_url else ""]],
                columns=["Model_Name", "WER", "CER", "Combined_Score", "timestamp", "License", "Model_URL"]
            )
            updated_leaderboard = pd.concat([leaderboard, new_entry])
        
        updated_leaderboard = updated_leaderboard.sort_values("Combined_Score")
        updated_leaderboard.to_csv(leaderboard_file, index=False)
        git_add_commit_push(f"Update leaderboard for model: {model_name}")
        
        display_leaderboard = prepare_leaderboard_for_display(updated_leaderboard)
        
        return f"Submission processed successfully! WER: {format_as_percentage(avg_wer)}, CER: {format_as_percentage(avg_cer)}, Combined Score: {format_as_percentage(combined_score)}", df_to_html(display_leaderboard)
    
    except Exception as e:
        return f"Error processing submission: {str(e)}", None


def create_main_leaderboard(wer_weight=70, cer_weight=30):
    current_data = get_current_leaderboard()
    
    if len(current_data) == 0:
        return pd.DataFrame(columns=["Model Name", "WER (%)", "CER (%)", "Combined Score (%)", "License", "Timestamp"])
    
    display_df = current_data.copy()
    
    wer_w = wer_weight / 100.0
    cer_w = cer_weight / 100.0
    
    total = wer_w + cer_w
    if total > 0:
        wer_w = wer_w / total
        cer_w = cer_w / total
    else:
        wer_w = 0.5
        cer_w = 0.5
    
    display_df["Custom_Score"] = display_df["WER"] * wer_w + display_df["CER"] * cer_w
    
    display_df = display_df.sort_values("Custom_Score", ascending=True).reset_index(drop=True)
    
    display_df["Model_Name"] = display_df.apply(
        lambda row: format_model_name_with_link(
            row["Model_Name"],
            row.get("License", "Unknown"),
            row.get("Model_URL", "")
        ),
        axis=1
    )
    
    for col in ["WER", "CER"]:
        if col in display_df.columns:
            display_df[f"{col} (%)"] = display_df[col].apply(lambda x: f"{x * 100:.2f}")
    
    display_df["Combined Score (%)"] = display_df["Custom_Score"].apply(lambda x: f"{x * 100:.2f}")
    
    display_df = add_medals_to_models(display_df, score_col="Custom_Score")
    
    def format_license(license_type):
        if license_type == "Open Source":
            return '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">Open Source</span>'
        elif license_type == "Proprietary":
            return '<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">Proprietary</span>'
        else:
            return '<span style="background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">Unknown</span>'
    
    display_df["License"] = display_df["License"].apply(format_license)
    
    display_df = display_df.rename(columns={
        "Model_Name": "Model Name",
        "timestamp": "Timestamp"
    })
    
    final_cols = ["Model Name", "WER (%)", "CER (%)", "Combined Score (%)", "License", "Timestamp"]
    display_df = display_df[[col for col in final_cols if col in display_df.columns]]
    
    return display_df


def get_weight_description(wer_weight, cer_weight):
    total = wer_weight + cer_weight
    if total > 0:
        wer_pct = (wer_weight / total) * 100
        cer_pct = (cer_weight / total) * 100
    else:
        wer_pct = 50
        cer_pct = 50
    
    return f"Current ranking: {wer_pct:.0f}% WER + {cer_pct:.0f}% CER"