- [1. Research \& Setup](#1-research--setup)
- [2. Prototype Matching Engine](#2-prototype-matching-engine)
- [3. Backend Service](#3-backend-service)
- [4. Basic Mobile App](#4-basic-mobile-app)
- [5. Continuous Listening + Sync](#5-continuous-listening--sync)
- [6. UX Improvements](#6-ux-improvements)

## 1. Research & Setup

- ✅ **Audio to text transcriber** &rarr; openai-whisper turbo model does the work. Tried [Conformer-CTC-BPE-Large.nemo](https://github.com/Open-Speech-EkStep/vakyansh-models#:~:text=punjabi_large_ssl_500) as well but it didn't work as expected. Still, need to get the `wer`, for that I need SGGS local DB. With `turbo` model, it takes about 40seconds

## 2. Prototype Matching Engine

- Added cleaning, removal of diacritics.
- Matching engine approaches &rarr;

| |

| Approach                                                                                                                          | Cons                                                     |
| --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| RDBMS, store verses line by line and do a `rapidfuzz` search                                                                    | poor performance on query_text which spans multiple rows |
| **Edit distance based matching** &rarr;<br />- Levenshtein distance &rarr;<br />- Jaro-Winkler distance &Rarr;             |                                                          |
| **Token/word base matching** &rarr;<br />- Jaccard similarity &rarr;<br />- Cosime similarity with TF/IDF &rarr;           |                                                          |
| **N-gram based matching**&Rarr;<br />- Character ngram &rarr;(This seems to be the most promising)<br />- Word ngram &rarr; |                                                          |
| **ML matching** &rarr;<br />- Sentence embeddings (BERT, SentenceTransformer) &rarr;                                       |                                                          |
| **Elasticasearch's fuzzy capabilties** &Rarr;                                                                               |                                                          |
| **Phonetic matching** &rarr;<br />- Soundex &rarr;<br />- Metaphone &rarr;                                                 |                                                          |

## 3. Backend Service

- ✅ **DB is setup** &rarr;Created FastAPI backed, SQLite DB to store verses. Tried `rapidfuzz` for directly querying but it is not working

## 4. Basic Mobile App

## 5. Continuous Listening + Sync

## 6. UX Improvements
