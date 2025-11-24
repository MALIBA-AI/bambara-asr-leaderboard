# Bambara ASR Leaderboard

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard)     [![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/MALIBA-AI/bambara-asr-leaderboard)  [![Dataset](https://img.shields.io/badge/Dataset-Benchmark-orange?logo=huggingface)](https://huggingface.co/datasets/MALIBA-AI/bambara-speech-recognition-leaderboard)   [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  

The **Bambara ASR Leaderboard** is a collaborative benchmark for evaluating Automatic Speech Recognition (ASR) models on Bambara, a low-resource African language spoken primarily in Mali. It promotes innovation in ASR for underrepresented languages, supporting the mission: *"No Malian Language Left Behind"*.

This repository hosts the source code for the leaderboard application, deployed on Hugging Face Spaces with results persisted via GitHub for reliability.



## Dataset

Evaluations use the  **[Bambara ASR Benchmark](https://huggingface.co/datasets/MALIBA-AI/bambara-speech-recognition-leaderboard)** dataset:
- **Language**: Bambara
- **Task**: ASR
- **Characteristics**: Diverse samples from multiple, accents, domains, and audio qualities.
- **Normalization**: Lowercase, remove punctuation, normalize whitespace.

**Submission Process**:
1. Access the test audio from the dataset.
2. Generate transcriptions.
3. Format as CSV (`id,text` matching dataset IDs).
4. Visit the [HF Space](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard).
4. Submit via the app's "Submit New Results" tab.

## Usage

- Visit the [HF Space](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard).
- Explore tabs: Leaderboard, Model Performance, Comparisons, Submissions, Dataset Info.
- Submit: Upload model name and CSV; scores computed automatically.

## Contributing
1
Welcome contributions! 
- Fork, branch, implement (e.g., new metrics, UI improvements).
- Test locally.
- PR with clear description.
- Report issues via GitHub.

## Citation
```
@article{bambara_asr_benchmark_2025,
    title={Bambara ASR Benchmark: Evaluating Speech Recognition for a Low-Resource African Language},
    author={MALIBA-AI Team and RobotsMali AI4D-LAB and Djelia},
    journal={Unpublished},
    year={2025},
    url={https://huggingface.co/datasets/sudoping01/bam-asr-benchmark}
}
```

## License

MIT License. See [LICENSE](LICENSE).

*Last updated: November 24, 2025*