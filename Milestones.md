- [1. Research \& Setup](#1-research--setup)
- [2. Prototype Matching Engine](#2-prototype-matching-engine)
- [3. Backend Service](#3-backend-service)
- [4. Basic Mobile App](#4-basic-mobile-app)
- [5. Continuous Listening + Sync](#5-continuous-listening--sync)
- [6. UX Improvements](#6-ux-improvements)

## 1. Research & Setup

- ✅ **Audio to text transcriber** &rarr; openai-whisper turbo model does the work. Tried [Conformer-CTC-BPE-Large.nemo](https://github.com/Open-Speech-EkStep/vakyansh-models#:~:text=punjabi_large_ssl_500) as well but it didn't work as expected. Still, need to get the `wer`, for that I need SGGS local DB. With `turbo` model, it takes about 40seconds

## 2. Prototype Matching Engine

- Matching engine is needed
  - Maybe after audiio to text transcribe, I need to do some cleaning ... removal of stopwords, searching only genuine words that have been transformed.
  - Later I also need to factor in noise.
  - We need the accuracy to be as high as possible, will focus on speed later.

## 3. Backend Service

- ✅ **DB is setup** &rarr;Created FastAPI backed, SQLite DB to store verses. Tried `rapidfuzz` for directly querying but it is not working

## 4. Basic Mobile App

## 5. Continuous Listening + Sync

## 6. UX Improvements
