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
        gr.Button("Dataset Repository", link="https://huggingface.co/datasets/sudoping01/bambara-speech-recognition-benchmark", elem_classes=['flat-navy-button'])
        gr.Button("GitHub Repo", link="https://github.com/MALIBA-AI/bambara-asr-leaderboard", elem_classes=['flat-navy-button'])
        gr.Button("Paper", link="#", elem_classes=['flat-navy-button'])
        gr.Button("Tasks", link="#", elem_classes=['flat-navy-button'])
    
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
                        value=70,
                        step=5,
                        label="WER Weight (%)",
                        info="Weight for Word Error Rate"
                    )
                    cer_weight_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=30,
                        step=5,
                        label="CER Weight (%)",
                        info="Weight for Character Error Rate"
                    )
                
                weight_description = gr.Markdown(
                    value=get_weight_description(70, 30),
                    elem_classes="weight-description"
                )
                
                update_ranking_btn = gr.Button("🔄 Update Ranking", variant="primary")
                
                main_leaderboard_html = gr.HTML(df_to_html(create_main_leaderboard(70, 30)))
                
                def update_leaderboard_with_weights(wer_w, cer_w):
                    description = get_weight_description(wer_w, cer_w)
                    leaderboard = create_main_leaderboard(wer_w, cer_w)
                    return description, df_to_html(leaderboard)
                
                update_ranking_btn.click(
                    fn=update_leaderboard_with_weights,
                    inputs=[wer_weight_slider, cer_weight_slider],
                    outputs=[weight_description, main_leaderboard_html]
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
                
                gr.Markdown("""
                <div style="margin-top: 20px; padding: 10px; background: #e9ecef; border-radius: 8px;">
                    <strong>Legend:</strong><br>
                    🏆 = 1st Place | 🥈 = 2nd Place | 🥉 = 3rd Place<br>
                    <span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Open Source</span> = Model available on HuggingFace (click name to visit) | 
                    <span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Proprietary</span> = Closed source model
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
        
            with gr.Tab("📊 Submit New Results", id="submit"):
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
            
                with gr.Row():
                    model_name_input = gr.Textbox(
                        label="Model Name",
                        placeholder="e.g., MALIBA-AI/bambara-whisper-large",
                        info="Use a descriptive name to identify your model"
                    )
                
                gr.Markdown("### 📜 Model License Information")
                gr.Markdown(
                    """
                    <div style="background: #fff3cd; padding: 10px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #ffc107;">
                        <strong>⚠️ Important:</strong> If your model is <strong>Open Source</strong>, you must provide a valid HuggingFace URL. 
                        The model name will be displayed as a clickable link to your model repository.
                    </div>
                    """
                )
                
                with gr.Row():
                    license_type_input = gr.Radio(
                        choices=["Open Source", "Proprietary"],
                        label="License Type",
                        value="Open Source",
                        info="Select the license type for your model"
                    )
                
                with gr.Row():
                    model_url_input = gr.Textbox(
                        label="HuggingFace Model URL",
                        placeholder="https://huggingface.co/your-org/your-model",
                        info="Required for Open Source models. Must be a valid HuggingFace URL.",
                        visible=True
                    )
                
                def toggle_url_visibility(license_type):
                    if license_type == "Open Source":
                        return gr.update(visible=True, info="Required for Open Source models. Must be a valid HuggingFace URL.")
                    else:
                        return gr.update(visible=True, info="Optional for Proprietary models.")
                
                license_type_input.change(
                    fn=toggle_url_visibility,
                    inputs=[license_type_input],
                    outputs=[model_url_input]
                )
                
                gr.Markdown("### 📁 Prediction File")
                with gr.Row():
                    csv_upload = gr.File(
                        label="Upload CSV File",
                        file_types=[".csv"]
                    )
                    gr.Markdown("*CSV with columns: id, text*")
                    
                submit_btn = gr.Button("🚀 Submit", variant="primary")
                output_msg = gr.Textbox(label="Status", interactive=False)
            
                submission_leaderboard_display = gr.HTML(
                    df_to_html(create_main_leaderboard()),
                    label="Updated Leaderboard"
                )
            
                def process_submission_wrapper(model_name, csv_file, license_type, model_url):
                    return process_submission(model_name, csv_file, references, license_type, model_url)
                
                submit_btn.click(
                    fn=process_submission_wrapper,
                    inputs=[model_name_input, csv_upload, license_type_input, model_url_input],
                    outputs=[output_msg, submission_leaderboard_display]
                )
        
            with gr.Tab("📝 Benchmark Dataset", id="dataset"):
                gr.HTML("<br><br><center><h2>About the Benchmark Dataset</h2></center><br>")
                gr.Markdown(
                    """
                    ## Bambara ASR Benchmark Dataset
                
                    This leaderboard uses the **[MALIBA-AI/bambara-speech-recognition-leaderboard](https://huggingface.co/datasets/MALIBA-AI/bambara-speech-recognition-leaderboard)** dataset for evaluation.
                
                    ### Dataset Characteristics
                
                    * **Language**: Bambara (native to Mali and surrounding regions)
                    * **Task**: Automatic Speech Recognition (ASR)
                    * **Domain**: Diverse speech samples covering various topics and speaking styles
                    * **Speakers**: Multiple native Bambara speakers with different accents and dialects
                    * **Audio Quality**: Various recording conditions to test model robustness
                
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
                    * Default weighted combination: 70% WER + 30% CER
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

    with gr.Group(elem_classes="content-card citation-section"):
        gr.HTML("<h2>Citation</h2>")
        gr.Markdown(
            """
            If you use the Bambara ASR benchmark for your scientific publication, or if you find the resources in this leaderboard useful, please cite our work:
            
            ```bibtex
            @article{bambara_asr_benchmark_2025,
                title={Bambara ASR Benchmark: Evaluating Speech Recognition for a Low-Resource African Language},
                author={MALIBA-AI Team and RobotsMali AI4D-LAB and Djelia},
                journal={arXiv preprint},
                year={2025},
                url={https://huggingface.co/datasets/MALIBA-AI/bambara-speech-recognition-leaderboard}
            }
            ```
            
            ### About the Collaboration
            
            This benchmark is a collaborative effort between:
            
            * **MALIBA-AI** - Mission: "No Malian Language Left Behind" - Empowering Mali's linguistic diversity through AI innovation
            * **RobotsMali AI4D-LAB** - Advancing AI research and development in Mali
            * **Djelia** - Preserving and promoting African languages through technology
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
    demo.launch(share=True)