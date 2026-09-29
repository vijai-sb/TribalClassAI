---
language:
  - sat
license: apache-2.0
library_name: piper
pipeline_tag: text-to-speech
tags:
  - text-to-speech
  - tts
  - santali
  - ol-chiki
  - low-resource
  - piper
  - vits
  - onnx
  - multi-speaker
  - female
  - on-device
  - offline
datasets:
  - XKaab/ASR-santali_100hrs
---

# Santali Piper VITS

A multi-speaker **Santali (sat)** text-to-speech model trained with the Piper VITS training pipeline and exported to ONNX.

The model is designed for Santali written in the **Ol Chiki** script and uses a custom Santali grapheme-to-phoneme pipeline.

## Current release

This repository contains the **final 50-epoch training release**.

## Model details

| Property | Value |
|---|---|
| Language | Santali |
| Language code | `sat` |
| Script | Ol Chiki |
| Architecture | Piper VITS |
| Speakers | 80 female speakers |
| Training utterances | 10,348 |
| Training audio | 20.05 hours |
| Sample rate | 22.05 kHz |
| Phoneme symbols | 168 |
| Training epochs | 50 |
| Batch size | 8 per GPU |
| Training hardware | 2 × NVIDIA Tesla T4 |
| Precision | 16-bit mixed precision |

## Dataset

Training data comes from:

**XKaab/ASR-santali_100hrs**

The selected training corpus contains approximately **20.05 hours** of female Santali speech across **10,348 utterances** and **80 speakers**.

The raw training WAV corpus is not redistributed here.

## Phonemization

The model uses the custom Santali phonemizer:

`santhali_phonemizer.py`

Main function:

`santhali_to_ipa(text)`

The resulting symbols are converted using:

`phoneme_id_map.json`

The model uses **168 phoneme symbols**.

For compatible inference, use the same Santali phonemization and symbol mapping used during training.

## ONNX model

Primary inference model:

`model/santali_piper_vits.onnx`

Configuration:

`model/santali_piper_vits.onnx.json`

The model is multi-speaker. Speaker IDs are contained in the ONNX configuration under `speaker_id_map`.

## Android / edge deployment

The repository contains:

`santali_female_multispeaker_piper_onnx_android.tar.gz`

This package contains the deployment artifacts used for local Android integration.

The model is intended for offline and on-device inference.

## Repository files

- `model/santali_piper_vits.onnx`
- `model/santali_piper_vits.onnx.json`
- `model/santali_piper_vits_epoch50.ckpt`
- `training/last.ckpt`
- `phoneme_id_map.json`
- `phonemes.json`
- `santhali_phonemizer.py`
- `metadata.csv`
- `selected_metadata.parquet`
- `audio_phoneme_ids.csv`
- `phoneme_training_metadata.parquet`
- `training_config.json`
- `MODEL_MANIFEST.json`
- `config.json`
- `santali_female_multispeaker_piper_onnx_android.tar.gz`

## Limitations

This is a low-resource Santali TTS model.

Possible limitations include pronunciation errors on unseen words, variation between speakers, prosody differences, and occasional synthesis artifacts.

## License and dataset attribution

The model repository metadata uses Apache-2.0.

The training dataset is hosted separately on Hugging Face. Users should review and comply with the dataset's own license, attribution, and usage requirements.

Dataset:
https://huggingface.co/datasets/XKaab/ASR-santali_100hrs

Piper:
https://github.com/OHF-Voice/piper1-gpl
