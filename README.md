# Bambara ASR Leaderboard

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard) [![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/MALIBA-AI/bambara-asr-leaderboard) [![Dataset](https://img.shields.io/badge/Dataset-Benchmark-orange?logo=huggingface)](https://huggingface.co/datasets/MALIBA-AI/bambara-asr-benchmark) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A public benchmark and leaderboard for evaluating Automatic Speech Recognition on Bambara (Bamanankan), a language spoken by over 14 million people in Mali and across West Africa.

This repository contains the source code for the leaderboard application, deployed on [Hugging Face Spaces](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard) with results persisted via GitHub.

## Benchmark

All evaluations run against the [**Bambara ASR Benchmark**](https://huggingface.co/datasets/MALIBA-AI/bambara-asr-benchmark): 1 hour of studio-recorded Malian constitutional text, transcribed and validated by linguists from Mali's DNENF-LN.

| | |
|:--|:--|
| Language | Bambara (bm) |
| Domain | Malian Constitution legal/formal register |
| Duration | 1.075 hours, 518 segments |
| Speaker | 1 adult male (main), 1 female (national anthem) |
| Vocabulary | 1,198 unique words, ~75% absent from existing training corpora |
| Acoustic conditions | Studio, single-channel, 99% of segments ≥ 15 dB SNR |
| Code-switching | None |

The benchmark is intentionally narrow: formal vocabulary, clean audio, no code-switching. It tests domain robustness and OOV handling under near-optimal conditions. Details in the [paper](https://huggingface.co/datasets/MALIBA-AI/bambara-asr-benchmark).

## Scoring

Transcriptions are normalized before scoring: lowercase, punctuation removed, whitespace collapsed.

**Default ranking metric:** Combined Score = 0.5 × WER + 0.5 × CER

The leaderboard UI lets you adjust WER/CER weights to match your use case.

## Submitting Results

1. Download the test audio from the [benchmark dataset](https://huggingface.co/datasets/MALIBA-AI/bambara-asr-benchmark).
2. Run your model and generate transcriptions.
3. Format output as CSV with columns `id,text`, where `id` matches the dataset segment IDs.
4. Go to the [leaderboard](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard) and upload via the **Submit New Results** tab.

Scores are computed automatically on submission.

## Running Locally

```bash
git clone https://github.com/MALIBA-AI/bambara-asr-leaderboard.git
cd bambara-asr-leaderboard
pip install -r requirements.txt
python app.py
```

## Current Top Results
 Check the leaderboard [leaderboard](https://huggingface.co/spaces/MALIBA-AI/bambara-asr-leaderboard).

## Contributing

Contributions welcome new metrics, UI improvements, bug fixes.

1. Fork the repo and create a branch.
2. Implement your changes and test locally.
3. Open a PR with a clear description of what changed and why.

Report bugs or suggest features via [GitHub Issues](https://github.com/MALIBA-AI/bambara-asr-leaderboard/issues).

## Citation

```bibtex
@misc{BambaraASRBenchmark2025,
  title        = {Where Are We at with Automatic Speech Recognition for the Bambara Language?},
  author       = {Seydou Diallo and Yacouba Diarra and Mamadou K. Keita and Panga Azazia Kamat{\'e} and Adam Bouno Kampo and Aboubacar Ouattara},
  year         = {2025},
  howpublished = {Hugging Face Datasets},
  url          = {https://huggingface.co/datasets/MALIBA-AI/bambara-asr-benchmark}
}
```

## License

MIT. See [LICENSE](LICENSE).
