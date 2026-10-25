# Research decisions and data card

## Data is a prerequisite, not an afterthought

This project trains on authentic public research email corpora. It does not train on its synthetic demonstration messages. Training automatically downloads three files from the original publisher, validates the published MD5 values, and records SHA-256 hashes in `data/manifest.json`. Network access is needed for downloads; investigation is local thereafter. No Kaggle account, API key, or manually labelled dataset is required.

Source: **Phishing Email Curated Datasets**, Zenodo record 8339691, DOI https://doi.org/10.5281/zenodo.8339691. The record's API declares **CC BY 4.0**. Credit: Arifa Islam Champa and collaborators. See the citation entries below. This licence is separate from the project's MIT source licence. Raw emails are not distributed in the ZIP or committed to GitHub.

| File | Role | Published MD5 |
| --- | --- | --- |
| CEAS_08.csv | Historical spam/ham proxy baseline and mixed training | 1f0d59191eec892a709995d48cd8decb |
| Nazario.csv | Genuine phishing-source examples in mixed training; positive-only transfer test for the CEAS-only experiment | 4022d055bb7cf8602f30f768f652e91e |
| Nigerian_5.csv | External fraud/legitimate benchmark after overlap removal | edfbbb89c40e7447f47867bcc82e72f9 |

Total download is approximately 94 MB. The model only uses subject and body; it deliberately excludes sender, receiver, date, and the upstream URL indicator from the ML feature set. Interactive rules inspect metadata independently.

**Label honesty:** upstream label 1 is a heterogeneous unwanted/malicious class. Inspection of CEAS finds ordinary advertising spam. Do not rename its benchmark score “verified phishing accuracy.” Nazario contributes phishing content, and the Nigerian corpus tests fraud/scam transfer. Neither makes a production-quality ground truth for today's corporate inbox.

## Experimental protocol

1. Decode CSV, combine subject/body, normalize case/whitespace, cap text at 100,000 characters, drop empty/short messages and folder-internal notices.
2. Remove exact normalized duplicate texts; drop groups with contradictory labels. Split the combined sources 80/20, stratified by label, seed 42.
3. Fit TF-IDF on training rows only: word unigrams/bigrams, sublinear TF, minimum document frequency 2, at most 30,000 features.
4. Fit balanced logistic regression; fixed evaluation threshold 0.5. No test-set threshold search or parameter tuning.
5. Report per-class precision, recall, F1, confusion matrix, ROC AUC and average precision on held-out rows.
6. Exclude exact text overlaps between the complete development corpus and external corpus before evaluating. Record the remaining class counts. External results must be interpreted by class availability.
7. Run a separate 12-message AI-authored challenge set. These examples were authored by ChatGPT for this project, use reserved domains/documentation IPs, contain no working payloads, and were not used to fit the model. They are illustrative, not representative of AI-generated attacks generally.

The included first experiment used CEAS alone and detected only 20% of 1,550 held-out-source Nazario positives at threshold 0.5, despite a high CEAS random-split result. This diagnostic motivated adding Nazario examples to mixed training. It is not an apples-to-apples estimate of improvement on that same external source: Nazario is now part of development. The final external source is Nigerian_5, not Nazario.

During source auditing, Nazario_5 was rejected as an independent phishing holdout: its phishing messages overlap Nazario.csv, leaving only negative examples after overlap filtering. It is not used by the released training code. This is why filenames alone are insufficient for assigning evaluation roles.

The development split is not chronological or campaign-grouped. Near duplicates and source artifacts can inflate metrics. Logistic regression scores are not calibrated real-world probabilities. Label noise, English-language bias, changing attack styles, sparse headers, HTML content differences, and class prevalence shift remain limitations. The ML benchmark covers text classification, not end-to-end MIME/header rule performance. Rules are verified through dedicated tests and illustrative scenarios.

## LLM design

Optional Ollama model: `qwen2.5:1.5b`. No hosted API or paid credits. The model receives only fixed detector categories, weights, and evidence IDs. Raw email body, subject, URLs, names, and attachment filenames are excluded. A constrained JSON schema permits evidence IDs only; the application validates IDs and copies the corresponding deterministic explanations. The LLM cannot alter classification scores or call tools. This deliberately limits narrative freedom and the prompt-injection surface; it is evidence prioritization, not an autonomous investigator or a proven injection-proof system.

## Sources and implementation references

- Dataset record and original checksums: https://zenodo.org/records/8339691
- Machine-readable licence and file metadata: https://zenodo.org/api/records/8339691
- Champa, A. I., Rabbi, M. F., and Zibran, M. F. (2024). *Why phishing emails escape detection: A closer look at the failure points.* ISDFS, pp. 1–6.
- Champa, A. I., Rabbi, M. F., and Zibran, M. F. (2024). *Curated datasets and feature analysis for phishing email detection with machine learning.* ICMI, pp. 1–7.
- Leakage prevention: https://scikit-learn.org/stable/common_pitfalls.html
- Model persistence security: https://scikit-learn.org/stable/model_persistence.html
- Ollama local API: https://docs.ollama.com/api/introduction
- Structured outputs: https://ollama.com/blog/structured-outputs
- Local model: https://ollama.com/library/qwen2.5:1.5b
- Python email parser: https://docs.python.org/3/library/email.parser.html

No live reputation service is enabled. URLs and domains are lexical evidence only. Authentication-Results headers are untrusted message text; the app does not verify sender identity, SPF, DKIM, or DMARC. It neither resolves links nor downloads external content. Attachments are listed as metadata, not extracted or scanned.
