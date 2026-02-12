import gradio as gr
from utils.utils_functions import (
    load_references,
    mask_sensitive_info,
    run_command,
    git_pull,
    git_add_commit_push,
    normalize_text,
    calculate_metrics,
    format_as_percentage,
    add_medals_to_models,
    get_current_leaderboard,
    prepare_leaderboard_for_display,
    df_to_html,
    get_model_performance_table,
    compare_models,
    process_submission,
    create_main_leaderboard,
    get_weight_description
)
import os
from settings.models import Settings
from assets.styles.themes import (
    get_logo_html,
    header_html,
    style_css
)
import pandas as pd

config = Settings()

run_command(["git", "config", "--global", "user.email", config.github_email])
run_command(["git", "config", "--global", "user.name", "HF Space"])

remote_url = f"https://{config.github_user}:{config.github_token}@github.com/{config.github_repo}.git"
run_command(["git", "remote", "set-url", "--push", "origin", remote_url], check=True, capture_output=True)

git_pull()

references = load_references()
leaderboard_file = config.leaderboard_file
logo_path = config.logo_path

if not os.path.exists(leaderboard_file):
    raise ValueError("No file found the for the leaderboard")

current_data = get_current_leaderboard()
MODEL_NAME_LIST = sorted(current_data['Model_Name'].unique()) if len(current_data) > 0 else []

favicon_head = '<link rel="icon" type="image/x-icon" href="/file=favicon.ico">'

with gr.Blocks(theme=gr.themes.Default(), title="Bambara ASR Benchmark Leaderboard", css=style_css, head=favicon_head) as demo:
    gr.HTML(header_html)
    
    with gr.Row():
        gr.Button("MALIBA-AI", link="https://huggingface.co/MALIBA-AI", elem_classes=['flat-navy-button'])
        gr.Button("Dataset Repository", link="https://huggingface.co/datasets/MALIBA-AI/bambara-speech-recognition-leaderboard", elem_classes=['flat-navy-button'])
        gr.Button("GitHub Repo", link="https://github.com/MALIBA-AI/bambara-asr-leaderboard", elem_classes=['flat-navy-button'])
        gr.Button("Paper", link="https://arxiv.org/pdf/2602.09785", elem_classes=['flat-navy-button'])
        # gr.Button("Tasks", link="#", elem_classes=['flat-navy-button'])
    
    with gr.Group(elem_classes="content-card"):
        gr.Markdown("<br>")
        
        if len(current_data) > 0:
            best_model = current_data.sort_values("Combined_Score").iloc[0]
            license_info = best_model.get('License', 'Unknown')
            gr.Markdown(f"""
            <div class="best-model-card">
            
            ### 🏆 Current Best Model: **{best_model['Model_Name']}**
            * WER: **{best_model['WER']*100:.2f}%**
            * CER: **{best_model['CER']*100:.2f}%**
            * Combined Score: **{best_model['Combined_Score']*100:.2f}%**
            * License: **{license_info}**
            </div>
            """)
    
        with gr.Tabs() as tabs:
            with gr.Tab("Main Leaderboard", id="main"):
                gr.HTML("<br><br><center><h2 style='color: #000000;'>Main Leaderboard</h2></center><br>")
                

                gr.Markdown("""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #7d3561;">
                    <strong>📊 Custom Ranking Weights</strong><br>
                    <span style="color: #666;">Adjust the sliders below to rank models based on your preference. 
                    For example, set WER to 100% and CER to 0% if you only care about Word Error Rate.</span>
                </div>
                """)
                
                with gr.Row():
                    wer_weight_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=50,
                        step=5,
                        label="WER Weight (%)",
                        info="Weight for Word Error Rate"
                    )
                    cer_weight_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=50,
                        step=5,
                        label="CER Weight (%)",
                        info="Weight for Character Error Rate"
                    )
                
                weight_description = gr.Markdown(
                    value=get_weight_description(50, 50),
                    elem_classes="weight-description"
                )
                
                with gr.Row():
                    update_ranking_btn = gr.Button("🔄 Update Ranking", variant="primary")
                    refresh_btn = gr.Button("🔃 Refresh Leaderboard", variant="secondary")
                
                main_leaderboard_html = gr.HTML(df_to_html(create_main_leaderboard(50, 50))) # WER=50% and CER=50%
                
                def update_leaderboard_with_weights(wer_w, cer_w):
                    description = get_weight_description(wer_w, cer_w)
                    leaderboard = create_main_leaderboard(wer_w, cer_w)
                    return description, df_to_html(leaderboard)
                
                def refresh_leaderboard():
                    """Refresh leaderboard by pulling latest data."""
                    git_pull()
                    leaderboard = create_main_leaderboard(50, 50)
                    return df_to_html(leaderboard)
                
                update_ranking_btn.click(
                    fn=update_leaderboard_with_weights,
                    inputs=[wer_weight_slider, cer_weight_slider],
                    outputs=[weight_description, main_leaderboard_html]
                )
                
                refresh_btn.click(
                    fn=refresh_leaderboard,
                    inputs=[],
                    outputs=[main_leaderboard_html]
                )
                
                wer_weight_slider.change(
                    fn=lambda w, c: get_weight_description(w, c),
                    inputs=[wer_weight_slider, cer_weight_slider],
                    outputs=[weight_description]
                )
                cer_weight_slider.change(
                    fn=lambda w, c: get_weight_description(w, c),
                    inputs=[wer_weight_slider, cer_weight_slider],
                    outputs=[weight_description]
                )
                
                gr.HTML("""
                <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 8px; color: #212529 !important;">
                    <strong style="color: #212529;">Legend:</strong><br>
                    <span style="color: #212529;">🏆 = 1st Place | 🥈 = 2nd Place | 🥉 = 3rd Place</span><br><br>
                    <span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">Open Source</span>
                    <span style="color: #212529;"> = Model available on HuggingFace (click name to visit)</span><br>
                    <span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-top: 5px; display: inline-block;">Proprietary</span>
                    <span style="color: #212529;"> = Closed source model</span>
                </div>
                """)
        
            with gr.Tab("Model-Specific Performance", id="models", elem_id="model_specific_table"):
                gr.HTML("<br><br><center><h2>Model-Specific Performance</h2></center><br>")
            
                if MODEL_NAME_LIST:
                    initial_model = MODEL_NAME_LIST[0]
                    initial_title_html = f"<h3 style='color: #2f3b7d;'><span style='color: #7d3561; font-weight: 700;'>Model name:</span> {initial_model}</h3>"
                    model_title_component = gr.HTML(initial_title_html)
                
                    model_dropdown = gr.Dropdown(
                        choices=MODEL_NAME_LIST,
                        label="Select Model",
                        interactive=True,
                        value=initial_model
                    )
                
                    model_table_component = gr.HTML(df_to_html(get_model_performance_table(initial_model)))
                
                    def update_model_display(model_name):
                        table = get_model_performance_table(model_name)
                        title = f"<h3 style='color: #2f3b7d;'><span style='color: #7d3561; font-weight: 700;'>Model name:</span> {model_name}</h3>"
                        return title, df_to_html(table)
                
                    model_dropdown.change(
                        fn=update_model_display,
                        inputs=model_dropdown,
                        outputs=[model_title_component, model_table_component]
                    )
                else:
                    gr.HTML("<p>No models available for comparison.</p>")
        
            with gr.Tab("Compare Models", id="compare"):
                gr.HTML("<br><br><center><h2>Compare Two Models</h2></center><br>")
            
                if len(MODEL_NAME_LIST) >= 2:
                    with gr.Row():
                        model_1_dd = gr.Dropdown(MODEL_NAME_LIST, label="Select Model 1", interactive=True)
                        model_2_dd = gr.Dropdown(MODEL_NAME_LIST, label="Select Model 2", interactive=True)
                    compare_btn = gr.Button("Compare")
                
                    explanation_note = """
                    **Note on the 'Difference' Column:**
                    * This value is calculated as: `(Score of Model 1) - (Score of Model 2)`.
                    * For ASR tasks (where lower is better): A negative value in <span style='color:green; font-weight:bold;'>green</span> indicates that **Model 1** performed better.
                    * A positive value in <span style='color:red; font-weight:bold;'>red</span> indicates that **Model 2** performed better.
                    """
                    explanation_note_md = gr.Markdown(explanation_note, visible=False)
                
                    with gr.Column(elem_id="models_comparison_table"):
                        comparison_output = gr.HTML("<p style='text-align:center; color: #212529;'>Select two models and click Compare to see the results.</p>")
                
                    def update_comparison_display(m1, m2):
                        if not m1 or not m2:
                            return gr.update(visible=False), "<p style='text-align:center; color: #212529;'>Please select two models to compare.</p>"
                    
                        comp_df = compare_models(m1, m2)
                        return gr.update(visible=True), df_to_html(comp_df)
                
                    compare_btn.click(
                        fn=update_comparison_display,
                        inputs=[model_1_dd, model_2_dd],
                        outputs=[explanation_note_md, comparison_output]
                    )
                else:
                    gr.HTML("<p style='color: #212529;'>At least 2 models are required for comparison.</p>")
        
            with gr.Tab(" Submit New Results", id="submit"):
                gr.HTML("<br><br><center><h2>Submit New Model Results</h2></center><br>")
                gr.Markdown(
                    """
                    ### Submit a new model for evaluation
                
                    Upload a CSV file with your model's predictions on the Bambara ASR benchmark dataset.
                
                    **Required CSV format:**
                    * Must contain exactly two columns: `id` and `text`
                    * The `id` column should match the reference dataset IDs
                    * The `text` column should contain your model's transcriptions
                    * Ensure all reference IDs are included in your submission
                    """
                )
            
                gr.HTML('<label style="color: #212529; font-weight: 600; font-size: 14px; display: block; margin-bottom: 8px;">Model Name</label>')
                model_name_input = gr.Textbox(
                    label="",
                    placeholder="e.g., MALIBA-AI/bambara-whisper-large",
                    show_label=False,
                    elem_classes=["light-input"]
                )
                gr.HTML('<span style="color: #666666; font-size: 12px;">Use a descriptive name to identify your model</span>')
                

                gr.HTML('<h3 style="color: #2f3b7d; margin-top: 24px;"> Model License Information</h3>')
                gr.HTML(
                    """
                    <div style="background: #fff3cd; padding: 12px 16px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #ffc107;">
                        <strong style="color: #856404;">⚠️ Important:</strong> 
                        <span style="color: #856404;">If your model is <strong>Open Source</strong>, you must provide a valid HuggingFace URL. 
                        The model name will be displayed as a clickable link to your model repository.</span>
                    </div>
                    """
                )
                
                gr.HTML('<label style="color: #212529; font-weight: 600; font-size: 14px; display: block; margin-bottom: 8px;">License Type</label>')
                license_type_input = gr.Radio(
                    choices=["Open Source", "Proprietary"],
                    label="",
                    value="Open Source",
                    show_label=False,
                    elem_classes=["light-radio"]
                )
                
                gr.HTML('<label style="color: #212529; font-weight: 600; font-size: 14px; display: block; margin-top: 16px; margin-bottom: 8px;">HuggingFace Model URL</label>')
                model_url_input = gr.Textbox(
                    label="",
                    placeholder="https://huggingface.co/your-org/your-model",
                    show_label=False,
                    elem_classes=["light-input"]
                )
                gr.HTML('<span style="color: #666666; font-size: 12px;">Required for Open Source models. Must be a valid HuggingFace URL.</span>')
                
                gr.HTML('<h3 style="color: #2f3b7d; margin-top: 24px;">Prediction File</h3>')
                with gr.Row():
                    csv_upload = gr.File(
                        label="Upload CSV File",
                        file_types=[".csv"],
                        elem_classes=["light-file"]
                    )
                    gr.HTML('<span style="color: #666666; font-size: 14px; padding: 20px;">CSV with columns: id, text</span>')
                    
                submit_btn = gr.Button("Submit", variant="primary")
                output_msg = gr.Textbox(label="Status", interactive=False)
            
                submission_leaderboard_display = gr.HTML(
                    df_to_html(create_main_leaderboard()),
                    label="Updated Leaderboard"
                )
            
                def process_submission_wrapper(model_name, csv_file, license_type, model_url):
                    result_msg, result_html = process_submission(model_name, csv_file, references, license_type, model_url)
                    main_lb_html = df_to_html(create_main_leaderboard(50, 50))
                    return result_msg, result_html, main_lb_html
                
                submit_btn.click(
                    fn=process_submission_wrapper,
                    inputs=[model_name_input, csv_upload, license_type_input, model_url_input],
                    outputs=[output_msg, submission_leaderboard_display, main_leaderboard_html]
                )
        
            with gr.Tab("Benchmark Dataset", id="dataset"):
                gr.HTML("<br><br><center><h2>About the Benchmark Dataset</h2></center><br>")
                gr.Markdown(
                    """
                    ## Bambara ASR Benchmark Dataset
                
                    This leaderboard uses the **[MALIBA-AI/bambara-speech-recognition-leaderboard](https://huggingface.co/datasets/MALIBA-AI/bambara-speech-recognition-leaderboard)** dataset for evaluation.
                
                    ### Dataset Characteristics
                
                    * **Language**: Bambara (pure bambara)
                    * **Task**: Automatic Speech Recognition (ASR)
                    * **Domain**: Mainly about the Mali constitution
                    * **Speakers**: Single speaker (male)
                    * **Audio Quality**: high-quality recordings (studio recordings)
                
                    ### Evaluation Metrics
                
                    **Word Error Rate (WER)**
                    * Primary metric for ASR evaluation
                    * Measures accuracy at the word level
                    * Calculated as: (Substitutions + Insertions + Deletions) / Total Words
                    * Lower values indicate better performance
                
                    **Character Error Rate (CER)**
                    * Complementary metric for character-level accuracy
                    * More fine-grained than WER
                    * Better captures partial word matches
                    * Particularly useful for morphologically rich languages like Bambara
                
                    **Combined Score**
                    * Default weighted combination: 50% WER + 50% CER
                    * **NEW:** You can now customize the weights in the Main Leaderboard tab!
                    * Set your own preference (e.g., 100% WER + 0% CER if you only care about WER)
                    * Provides flexible evaluation based on your specific needs
                
                    ### How to Submit Results
                
                    1. **Download the dataset** from the Hugging Face repository
                    2. **Process the audio files** with your ASR model
                    3. **Generate predictions** in the required CSV format:
                    
                    ```csv
                    id,text
                    sample_001,"your model's transcription here"
                    sample_002,"another transcription"
                    ...
                    ```
                    
                    4. **Specify your model's license:**
                       - **Open Source:** Provide a HuggingFace URL (model name becomes a link)
                       - **Proprietary:** No URL required
                    5. **Submit your results** using the "Submit New Results" tab
                
                    ### Evaluation Guidelines
                
                    * All text is normalized (lowercase, punctuation removed) before evaluation
                    * Submissions must include predictions for all reference samples
                    * Duplicate IDs or missing samples will result in submission rejection
                    * Results are automatically validated for format and completeness
                
                    ### Technical Details
                
                    * **Text Normalization**: Removes punctuation, converts to lowercase, normalizes whitespace
                    * **Error Calculation**: Uses the jiwer library for standard WER/CER computation
                    * **Quality Assurance**: Extreme outliers are capped to prevent result manipulation
                    * **Reproducibility**: All evaluation code is open-source and transparent
                    """
                )
                
            with gr.Tab("Task", id="task"):
                gr.HTML("<br><br><center><h2>Task: Automatic Speech Recognition</h2></center><br>")
                gr.Markdown(
                    """
                    ### What is ASR?

                    Automatic Speech Recognition (ASR) is the task of converting spoken audio into written text. 
                    Given an audio input, a model produces a transcription — a sequence of words representing what was said.

                    ### Why Bambara?

                    Bambara (Bamanankan) is the most widely spoken language in Mali with over 14 million speakers across West Africa. 
                    Despite this, it remains severely underrepresented in speech technology. Most commercial ASR systems either do not 
                    support Bambara at all or produce unusable output — as this benchmark demonstrates, with several major multilingual 
                    models exceeding 100% Word Error Rate.

                    ### What This Benchmark Measures

                    Models are evaluated on a **formal, read-speech domain**: a studio recording of the Malian Constitution in 
                    standard Bambara orthography, with no code-switching and near-perfect acoustic conditions.

                    This is deliberately a **best-case scenario**. Real-world Bambara speech involves background noise, varying 
                    accents, dialectal differences, and frequent French code-switching — all of which would increase error rates 
                    beyond what is reported here.

                    The benchmark tests two specific challenges:

                    **1. Out-of-vocabulary handling** — ~75% of the vocabulary in this dataset does not appear in existing 
                    Bambara ASR training corpora. Words like *yuruguyuruguli* (disorder/embezzlement) and *yamaruyasariya* 
                    (ordinance/regulation) are central to legal text but absent from conversational data.

                    **2. Morphological segmentation** — Bambara is agglutinative. Compound words like *kiritigɛfanga* 
                    (judicial power) are frequently split by models into *kiritigɛ fanga*, producing correct characters but 
                    wrong word boundaries. This explains the consistent gap between CER and WER across all evaluated models.

                    ### Metrics

                    | Metric | What it measures | How it's computed |
                    |:---|:---|:---|
                    | **WER** (Word Error Rate) | Word-level accuracy | (Substitutions + Insertions + Deletions) / Total reference words |
                    | **CER** (Character Error Rate) | Character-level accuracy | Same formula applied at the character level |
                    | **Combined Score** | Balanced ranking | Adjustable: default is 0.5 × WER + 0.5 × CER |

                    Lower is better for all metrics. WER can exceed 100% when models hallucinate — generating more 
                    tokens than exist in the reference.

                    ### Production Readiness Context

                    | Application | Typical WER needed | Current best on this benchmark |
                    |:---|:---|:---|
                    | Transcription services | < 10% | 47.50% |
                    | Voice assistants | < 15% | 47.50% |
                    | Captioning / accessibility | < 10% | 47.50% |
                    | Voice-to-text input | < 5% | 47.50% |

                    Current Bambara ASR is **30–40 percentage points** above production thresholds, even under ideal conditions.

                    ### Key Findings from the Evaluation

                    **37 models** were evaluated. The main takeaways:

                    * **Bambara-specific fine-tunes dominate.** Small focused models (114M–600M parameters) consistently 
                    outperform massive multilingual systems, confirming that targeted development beats scale for low-resource languages.
                    * **Multilingual pre-training does not transfer.** All OpenAI Whisper variants and NVIDIA models (not trained 
                    on Bambara) exceed 100% WER — performing worse than producing no output at all.
                    * **Scale does not compensate for data scarcity.** Meta's 7B CTC model (74.65% WER) underperforms their 
                    300M LLM variant (63.32% WER), which itself trails a 114M monolingual model (48.32% WER).
                    * **Phonetics are easier than words.** Best CER is 13.00% vs. best WER of 46.76%, reflecting the 
                    morphological complexity of Bambara.
                    """
                )

    with gr.Group(elem_classes="content-card citation-section"):
        gr.HTML("<h2>Citation</h2>")
        gr.Markdown(
            """
            If you use the Bambara ASR benchmark for your scientific publication, or if you find the resources in this leaderboard useful, please cite our work:
            
            ```bibtex
                @misc{BambaraASRBenchmark2025,
                  title        = {Where Are We at with Automatic Speech Recognition for the Bambara Language?},
                  author       = {Seydou Diallo and Yacouba Diarra and Mamadou K. Keita and Panga Azazia Kamat{\'e} and Adam Bouno Kampo and Aboubacar Ouattara},
                  year         = {2025},
                  howpublished = {Hugging Face Datasets},
                  url          = {https://huggingface.co/datasets/MALIBA-AI/bambara-asr-benchmark}
                }
            ```

            """
        )

    gr.HTML(
        """
        <center>
            <br><br>
            <p style="color: #7d3561; font-size: 18px; font-weight: bold;">
                A collaboration between MALIBA-AI, RobotsMali AI4D-LAB, and Djelia
            </p>
            <p style="color: #2f3b7d; font-size: 14px;">
                Advancing Speech Recognition Technology for African Languages
            </p>
            <br>
        </center>
        """
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1)
    demo.launch(share=True)


