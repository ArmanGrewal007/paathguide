<div align="center"><h1>ਪਾਠ guide</h1></div>Got the gurbani file from here - https://www.gurbanifiles.net/other/index.htm

```bash
# This must be executed to not interfere with zsh-autosuggestions plugin
export PYTHONIOENCODING=utf-8
```


```bash
poetry run python -m paathguide.cli clear-data
poetry run python -m paathguide.cli init-db
poetry run python -m paathguide.cli stats
poetry run python -m paathguide.cli load-data --file-path="SGGS-Gurm-SBS-Uni with page line numbers.docx"
# Test the FTS5 search
poetry run python -m paathguide.cli search -q "ਸਦਣਹਾਰਾ ਸਿਮਰੀਐ ਨਾਨਕ ਸੇ ਦਿਹ ਆਵੰਨਿ" -l 2
# Test the fuzzy search
poetry run python -m paathguide.cli fuzzy-search -q "ਸਦਣਹਾਰਾ ਸਿਮਰੀਐ ਨਾਨਕ ਸੇ ਦਿਹ ਆਵੰਨਿ" -l 2
poetry run python -m paathguide.cli fuzzy-search -q " ਕਾਚੇ ਕਾਰ ਛੇ ਗੁਰ ਛੇ ਅਪ ਦੇਸ ਗੁਰ ਗੁਰ ਇਕ ਵੇ ਸਨੇ ਕ" -l 2
# Run whisper
poetry run python -m paathguide.transcribe.whisper_turbo_pa

' ਕਾਚੇ ਕਾਰ ਛੇ ਗੁਰ ਛੇ ਅਪ ਦੇਸ ਗੁਰ ਗੁਰ ਇਕ ਵੇ ਸਨੇ ਕ'



```
