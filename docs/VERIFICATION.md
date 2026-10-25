# Verification record — release 1.0

Package creation: 25 October 2026, Europe/Helsinki. Automated timestamps in JSON are UTC. Verified in a Linux execution environment using Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5, and SciPy 1.17.0. Windows PowerShell commands are supplied for the user; they were not executed on Windows during package creation.

## Completed

- Downloaded CEAS_08.csv, Nazario.csv, and Nigerian_5.csv from the original Zenodo source and matched their published MD5 checksums. Stored SHA-256 digests and source metadata in the manifest.
- Fitted the mixed-source text model and wrote numeric JSON parameters; completed held-out evaluation, external overlap filtering, and held-out error indexing.
- Reproduced the CEAS-only diagnostic experiment separately.
- Ran 17 automated unittest checks: all passed. Tests cover MIME attachment separation, HTML-alternative links, pressure/credential/IP indicators, untrusted authentication headers, size limits, contradictory duplicate removal, injection-pattern evidence, benign rules, model loading, disjoint train/test hashes, LLM input minimization, invalid evidence-ID rejection, HTTP analysis, session-token rejection, empty input rejection, byte-preserving upload hashes, host validation, and inaccessible raw-data paths.
- Ran all 12 synthetic challenge cases against the final model and wrote `reports/challenge.json`.
- Checked dashboard JavaScript syntax with Node.js. Confirmed local HTTP/API routes through automated requests.

## Still to verify on the user's laptop

- Python 3.12 installation and pinned package installation on Windows 11.
- Browser rendering, sample loading, file upload and both download buttons through the manual acceptance checks in START_HERE.md. A browser binary download was unavailable in the build environment, so visual browser QA was not completed here.
- Live Ollama qwen2.5:1.5b inference and response time. LLM tests use mocked responses to check boundaries; they do not establish live model quality or availability.
- GitHub push and screenshots after the user's local run. No repository was created or pushed during package creation.

## Interpreting tests

Passing software tests verifies specific expected behaviour, not universal phishing detection accuracy. The external benchmark exposes substantial misses. The rule score is a manually weighted heuristic from 0 to 100; the ML score is an uncalibrated 0-to-1 output. Neither is a probability that the message is safe or malicious in a real inbox.

Evaluation threshold is 0.5. Dashboard wording uses 0.7 for “Elevated signals” and 0.3 for “Review recommended”, alongside rule thresholds of 30 and 10. These review bands are deliberately distinct from the benchmark binary threshold and are not validated policy recommendations.
