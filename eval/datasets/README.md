Place benchmark JSONL files here. Each row should look like:

```json
{
  "language": "python",
  "code": "broken code snippet",
  "region": {"start_line": 1, "end_line": 10},
  "diagnostics": ["NameError: ..."],
  "instruction": "fix errors only",
  "expected": "optional target patch or clean code"
}
```
