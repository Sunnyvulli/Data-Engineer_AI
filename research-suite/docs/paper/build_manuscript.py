"""Render a manuscript from committed measured JSON; no hand-entered results."""
from pathlib import Path
import json
from html import escape
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for name, path in [("PaperSerif", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"), ("PaperSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), ("PaperBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
 pdfmetrics.registerFont(TTFont(name,path))

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results/validation/external-support.json').read_text())
lex=json.loads((ROOT/'results/followup/citation-transfer.json').read_text())
nli=json.loads((ROOT/'results/followup/nli-comparison.json').read_text())

def pct(x):return f'{100*x:.2f}%'
diag=json.loads((ROOT/'results/validation/review-diagnostics.json').read_text())
def rowtext(row,source):
 return f"| {source.upper()} | {row['policy']} | {row['average_precision']:.3f} | {row['roc_auc']:.3f} | {pct(row['recall'])} | {pct(row['false_positive_rate'])} | {pct(row['review_fraction'])} | {row['missed_unsupported']} |"
rows=[x for x in r['experiments'] if x['policy'] in ['learned_lexical','bounded_nli','coverage_nli']]
table='\n'.join(rowtext(x,x['source_policy']) for x in rows)
alce=[]
for source in ['asqa','eli5']:
 for name,data in [('learned_lexical',lex),('open_nli',nli)]:
  x=next(x for x in data['experiments'] if x['source']==source and x['policy']==name)
  alce.append(f"| {source.upper()} to {x['target'].upper()} | {'Lexical' if name=='learned_lexical' else 'Bounded NLI'} | {x['average_precision']:.3f} | {pct(x['recall'])} | {pct(x['review_fraction'])} | {x['missed_unsupported']} |")
intervals=[]
for x in rows:
 ci=x['uncertainty']['percentile_95']
 d=ci['paired_ap_difference']
 intervals.append(f"| {x['source_policy'].upper()} / {x['policy']} | [{ci['ap'][0]:.3f}, {ci['ap'][1]:.3f}] | {'reference' if d is None else f'[{d[0]:.3f}, {d[1]:.3f}]'} |")
body=f'''# Source Recall Does Not Guarantee Transfer: A Reproducible Audit of Evidence-Support Triage

Hanumantha Rao Vulli

Research manuscript draft for author review. Revised October 20, 2026 UTC. Not peer reviewed or accepted. No institutional affiliation is asserted.

## Abstract

Evidence-support triage can reduce manual review only if its recall and workload transfer beyond its calibration corpus. We audit six lexical features and an openly licensed small natural-language-inference (NLI) model under frozen source-only thresholds. Earlier ALCE sentence experiments are contrasted with a separately selected RAGTruth QA test set containing {r['selection']['retained_responses']} whole answers in {r['selection']['retained_source_groups']} question groups, with {r['positives']} positive annotations. At the original ASQA threshold, lexical triage catches every positive but flags 98.9% of answers. At the original ELI5 threshold, it catches 81.9% and flags 67.2%. The fixed bounded NLI representation has average precision 0.210. A precommitted coverage-window diagnostic raises this to 0.281, but at the ELI5-calibrated cutoff still misses 14 of 160 positives while flagging 70.9% of answers. The paired AP intervals versus ELI5 lexical [0.017, 0.117] and ASQA lexical [-0.053, 0.054] are exploratory, uncorrected contrasts from 300 cluster resamples. A post-hoc length-only ranking has AP 0.386, exceeding every tested detector; this exposes a major alternative explanation rather than demonstrating semantic detection. These are conditional benchmark findings, not a general ranking or deployment guarantee. We release original code, frozen protocols, derived predictions and failure audits, keeping restricted source text local.

## 1. Research question and bounded contribution

A high unsupported-claim recall on source validation does not specify the fraction of answers a user must inspect elsewhere. This audit asks: how do source-calibrated triage policies behave when the evidence task changes corpus and annotation unit? A second, diagnostic question asks whether covering all input tokens changes the behavior of the same NLI weights relative to a fixed truncation policy.

ALCE evaluates answers with citations and provides human sentence-support annotations (Gao et al., 2023). RAGTruth provides manually annotated hallucination spans in generated responses grounded in supplied material (Niu et al., 2024). Their annotations serve related purposes but are not identical constructs. This manuscript reports an empirical audit; it does not introduce a new learning algorithm, claim a first use of window aggregation, establish state-of-the-art performance, or establish a comprehensive novelty result. Previously exposed ALCE comparisons are historical context. The new RAGTruth protocol was committed before its model outcomes were computed.

## 2. Data, labels and independence

The ALCE annotation file contains 2,604 sentences from 200 supplied question groups across ASQA and ELI5. All available model responses to the same supplied question stay together. Source train and validation sets follow the existing seed42 split: ASQA has 639 training sentences from 81 questions and 172 validation sentences from 19 questions; ELI5 has 1,430 training sentences from 81 questions and 363 validation sentences from 19 questions. Unsupported is the positive class, defined as one minus the binary human sentence-support label. The other domain is an exposed historical target, never used to calibrate the new external experiment.

The independent external selection uses the published RAGTruth test split and task_type QA only. Every eligible response is retained, without filtering by generator, quality, label or score. A complete question group would be excluded if its lowercased whitespace-normalized question exactly matched any ALCE question. There were zero such exclusions, leaving 900 answers and 150 source_id groups. A positive answer has at least one supplied hallucination span; zero spans is negative under this released annotation rule, not a certificate of truth. All supplied quality flags, including imperfect outputs, remain available only as descriptive strata. Neither question text, model identity, quality flags, prompts nor human annotation spans enter model inputs. Only the response and its supplied evidence do.

The ALCE file SHA-256 is cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6. RAGTruth is pinned to commit c103204b9ce28d6bbad859304bf30de72b8ed8fe; the complete input hashes are stored in the protocol and measured result. The annotation repository has an MIT license, while its underlying MS MARCO web material has separate noncommercial research terms. Raw questions, passages, answers and hallucination spans are not redistributed. Exact question matching cannot establish semantic independence. Unknown model-pretraining overlap, corpus selection and annotation errors remain unresolved.

## 3. Frozen policies and evaluation

The lexical policy uses evidence-token overlap, number of citations, unique claim-token count, unique evidence-token count, unmatched-number fraction and a missing-citation indicator. A train-only standard scaler and balanced logistic regression fit each ALCE source separately. The highest validation threshold retaining at least 90% source unsupported recall is fixed before external scoring. The external complete answer is represented with one supplied evidence citation. This changes feature distributions; it is not a sentence-to-answer invariant. The implementation requires the previously measured lexical ALCE target AP and source threshold to reproduce before external inference.

The NLI comparator is cross-encoder/nli-deberta-v3-small at immutable revision fa2804872c3b4bd748f38c0185cc85775361e735, with hash-checked ONNX/tokenizer files and an Apache-2.0 model card. The model card identifies SNLI/MultiNLI training and label order contradiction, entailment, neutral. Unsupported risk is one minus the entailment softmax score. It is a model score, not a calibrated real-world probability. The bounded representation allows 512 total pair tokens and caps the answer at 120 tokens, truncating evidence first. Earlier ALCE-calibrated thresholds are reused without external adaptation.

The coverage diagnostic uses these identical weights. Evidence windows have 384 tokens and stride 320; answer windows have 120 tokens and stride 100. An end-aligned final window ensures that every original token appears in a window. Each answer window receives its maximum entailment score across all evidence windows. The whole-answer risk is the maximum unsupported score across answer windows. The policy uses 1,836 inference pairs for 900 external answers, with zero re-encoding truncations. Source validation separately calibrates this new representation, using the same 90% recall rule. Window dimensions and aggregation were frozen before target scoring. This method can split joint semantics and is intrinsically length-dependent; it is a diagnostic adaptation, not a claimed novel detector.

We report average precision (AP), ROC AUC, recall, supported-answer false-positive rate (FPR), review fraction and missed positives. AP is scikit-learn average precision, not trapezoidal PR area. Thresholds use source validation only. Review-all and review-none controls expose the workload extremes. Uncertainty uses 300 complete-source_id bootstrap resamples, seed 20261019, with paired AP differences on identical rows. These percentile intervals condition on fitted policies and the sampled corpus. They do not include model-fitting, annotation, source-selection or pretraining uncertainty. Multiple descriptive contrasts are not a family-wise corrected significance study.

## 4. Measured results

Table 1 gives the historical ALCE sentence-transfer results. These rows are not pooled with whole-answer RAGTruth metrics.

| Direction | Policy | AP | Recall | Review | Missed |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(alce)}

Table 2 gives the new whole-answer RAGTruth results. Source denotes the calibration policy, not a target subgroup. Bounded and coverage NLI risk rankings are the same across source rows; only their source-calibrated thresholds change. The target positive prevalence is 17.8%.

| Source | Policy | AP | ROC AUC | Recall | FPR | Review | Missed |
| --- | --- | --- | --- | --- | --- | --- | --- |
{table}

The bounded representation truncated evidence for 151 of 900 answers and truncated claims for 458. Consequently, a positive answer annotation can refer to text not observed by this policy. Covering all tokens improves AP from 0.210 to 0.281 for these fixed weights, but does not isolate token coverage as a causal explanation: aggregation and representation change together. With ELI5 calibration, coverage misses 14 positives rather than bounded NLI's 33, while increasing the review fraction from 66.8% to 70.9% and supported-answer FPR from 64.1% to 66.5%. With ASQA calibration, coverage misses 64 positives; its recall is 60.0%. There is no transferred 90% recall guarantee. The ELI5 coverage recall is exactly 146/160 = 91.25%; table percentages use two decimals to avoid inconsistent one-decimal rounding.

Table 3 gives the conditional 95% percentile intervals for AP and its paired difference from the corresponding lexical source policy. These are descriptive intervals from 150 question clusters, not 900 independent answer draws.

| Source / Policy | AP interval | AP difference from lexical |
| --- | --- | --- |
{chr(10).join(intervals)}

The coverage-versus-ELI5 lexical AP interval excludes zero under this conditional procedure. The coverage-versus-ASQA lexical difference includes zero. Review-all obtains recall 100%, FPR 100% and review 100%; review-none obtains recall 0%, FPR 0% and review 0%. Both constant-score controls have AP equal to prevalence, 0.178. Neither is a practical efficiency success. The ASQA lexical policy's perfect recall with 98.9% review approaches the review-all extreme, so recall alone obscures its operational weakness.

## 5. Interpretation and alternative explanations

The title is limited to the observed ALCE-sentence to RAGTruth-whole-answer setting. It is not a universal transfer theorem. The useful finding is a failure of easy transfer, not a universally superior policy.

Post-hoc diagnostics, specified in REVIEW_RESPONSE_PROTOCOL.md after the original outcomes and critique were exposed, use cached answer token counts aligned against identical coverage risk vectors. Longer-is-riskier length ranking has AP {diag['length_longer_risk']['ap']:.3f} and ROC AUC {diag['length_longer_risk']['roc_auc']:.3f}; shorter-is-riskier has AP {diag['length_shorter_risk']['ap']:.3f} and ROC AUC {diag['length_shorter_risk']['roc_auc']:.3f}. Both directions are reported without selecting one as a confirmatory result. Length alone ranks better than coverage NLI here. This finding materially weakens an interpretation of the detector scores as semantic support detection, but does not identify a causal mechanism.

All six generators contribute 150 answers. Positive counts are GPT-3.5: 5; GPT-4: 1; Llama-2-13B: 36; Llama-2-70B: 35; Llama-2-7B: 52; Mistral-7B: 31. Within-generator detector metrics and row-level diagnostics are retained in review-diagnostics.json; tiny positive counts prevent stable conclusions for some strata. A five-fold complete-question cross-fitted generator prior yields AP {diag['generator_prior_target_supervised']['ap']:.3f}, ROC AUC {diag['generator_prior_target_supervised']['roc_auc']:.3f}. It uses target labels from other question groups and is a target-supervised diagnostic, NOT a source-only comparator or an evidence-reading detector.

Coverage thresholds are 0.989811 for ASQA (172 sentences, 19 questions) and 0.451716 for ELI5 (363 sentences, 19 questions). They are empirical source recall cutoffs, not calibrated probabilities. Different source score distributions can produce different cutoffs, but the cached data do not establish why this gap occurs. Calibration sensitivity across independent question-group splits has not been measured; a 90% empirical source target is not a population recall guarantee. High historical sentence-level AP does not transfer unchanged to this answer-level benchmark. The target differs in generator mixture, response length, citation presentation, evidence and positive-label definition. These shifts occur together. Accordingly, the numerical AP drop cannot be attributed solely to domain shift, answer granularity or model architecture. A controlled unit-matched annotation study would be needed to separate those explanations.

AttrScore directly studies attribution errors and evaluates prompted and fine-tuned models (Yue et al., 2023). AttributionBench consolidates attribution evaluation and documents persistent failure modes (Li et al., 2024). These are close prior work, not systems reproduced here. Their task-specific F1 scores cannot be compared numerically with this audit's AP. REVIEW_RESPONSE_PROTOCOL.md records the required label mapping, checkpoint/license verification, context policy and source-only calibration for a matched AttrScore experiment, which remains unexecuted.

The small NLI model is an accessible open comparator, not a comprehensive current-model tournament. Target fine-tuning, prompt-based commercial judges, larger task-specific detectors and learned evidence retrieval are not tested. The source-only design answers a transfer question; it does not estimate the best achievable supervised RAGTruth performance. Comparison with the original RAGTruth paper's tuned systems would require their matched splits, units and procedures. No such numerical ranking is claimed.

Window aggregation has opposing failure modes. A maximum across evidence may find a spurious supporting fragment, while a maximum risk across answer windows may penalize long otherwise supported answers. Splitting text can destroy conjunctions or reference resolution. No calibrated probability, reliable factual verdict or educational learning benefit follows from these scores. Generator and quality strata are released descriptively, without outcome-selected exclusions or selecting a preferred policy after inspecting a favorable stratum.

## 6. Reproducibility, ethics and limitations

Protocols, source hashes, original code, integrity tests, individual derived risks and aggregate outputs accompany the manuscript in Sunnyvulli/Data-Engineer_AI/research-suite. The external protocol is fixed at commit cf1c7b96b7aee262fd64816377dbcf04168ba5e7. Run python -m research_suite.external_support with the pinned local data and model directory after installing documented dependencies. Hash-validated caches permit interrupted inference to resume. The recorded elapsed time is a resumed invocation, not a reconstructed end-to-end compute bill; no total from discarded process time is fabricated. CPU inference uses four intra-operation threads and batch 4; no paid API or GPU was used.

Integrity checks cover hidden-label exclusion, complete token-window coverage, grouped paired resampling and existing causal/split controls. Passing tests cannot prove statistical validity or absence of all defects. The four-perspective review is a self-audit generated within this project, not independent expert peer review. No participant study, production deployment, manually adjudicated new labels or acceptance by a journal is represented.

The named human author must inspect the artifacts, verify the claims and confirm substantive authorship and the final text before external submission. AI is not listed as an author. No institutional affiliation, funding award or external reviewer is invented.

## 7. Conclusion

Under the frozen conditions tested here, source recall and historical sentence-level ranking do not establish efficient whole-answer triage. A coverage diagnostic improves one fixed NLI representation but still trades missed positives against substantial review workload. The evidence supports a bounded, reproducible transfer audit. A post-hoc length-only ranking exceeds every tested detector, so a semantic detection advantage is not established. Representative deployment validity, causal explanations for the shift, stronger matched comparators and independent human review remain open.

## References

Yue, X., Wang, B., Chen, Z., Zhang, K., Su, Y., & Sun, H. (2023). Automatic Evaluation of Attribution by Large Language Models. Findings of EMNLP, 4615-4635. https://doi.org/10.18653/v1/2023.findings-emnlp.307

Li, Y., Yue, X., Liao, Z., & Sun, H. (2024). AttributionBench: How Hard is Automatic Attribution Evaluation? Findings of ACL, 14919-14935. https://doi.org/10.18653/v1/2024.findings-acl.886

Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling Large Language Models to Generate Text with Citations. Proceedings of EMNLP,6465-6488. https://doi.org/10.18653/v1/2023.emnlp-main.398

Niu, C., Wu, Y., Zhu, J., Xu, S., Shum, K., Zhong, R., Song, J., & Zhang, T. (2024). RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models. Proceedings of ACL, Volume1: Long Papers,10862-10878. https://doi.org/10.18653/v1/2024.acl-long.585

Sentence Transformers. cross-encoder/nli-deberta-v3-small model card and immutable revision fa2804872c3b4bd748f38c0185cc85775361e735. https://huggingface.co/cross-encoder/nli-deberta-v3-small/tree/fa2804872c3b4bd748f38c0185cc85775361e735

Particle Media. RAGTruth source and annotation release, commit c103204b9ce28d6bbad859304bf30de72b8ed8fe. https://github.com/ParticleMedia/RAGTruth/tree/c103204b9ce28d6bbad859304bf30de72b8ed8fe

Microsoft. MS MARCO data and research-use terms. https://microsoft.github.io/msmarco/

Vulli research suite. Frozen external-support protocol and original evaluation implementation. https://github.com/Sunnyvulli/Data-Engineer_AI/tree/main/research-suite
'''
(OUT/'MANUSCRIPT.md').write_text(body)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='PaperTitle',parent=styles['Title'],fontName='PaperBold',fontSize=17,leading=22,spaceAfter=14))
styles['BodyText'].fontName='PaperSerif';styles['BodyText'].fontSize=9.8;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=8
styles['Heading2'].fontName='PaperBold';styles['Heading2'].fontSize=11;styles['Heading2'].leading=16
styles.add(ParagraphStyle(name='Cell',fontName='PaperSans',fontSize=7.2,leading=9))
story=[];lines=body.splitlines();i=0
while i<len(lines):
 line=lines[i]
 if line.startswith('|'):
  cells=[]
  while i<len(lines) and lines[i].startswith('|'):
   parts=[x.strip() for x in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[-: ]+',x) for x in parts):cells.append([Paragraph(escape(x),styles['Cell']) for x in parts])
   i+=1
  cols=len(cells[0]);widths=([58,95,42,45,50,50,52,42] if cols==8 else [90,110,48,48,48,48,48] if cols==7 else [130,105,50,50,55,50] if cols==6 else [220,110,210])
  t=Table(cells,colWidths=[x*492/sum(widths) for x in widths],repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#586a7e')),('LINEBELOW',(0,1),(-1,-1),.2,colors.HexColor('#d4dbe4'))]))
  story.append(KeepTogether([t,Spacer(1,10)]));continue
 if line.startswith('# '):story.append(Paragraph(escape(line[2:]),styles['PaperTitle']))
 elif line.startswith('## '):story.append(Paragraph(escape(line[3:]),styles['Heading2']))
 elif line.strip():story.append(Paragraph(escape(line),styles['BodyText']))
 i+=1

def footer(canvas,doc):
 canvas.setFont('PaperSans',8);canvas.setFillColor(colors.HexColor('#586a7e'));canvas.drawString(54,30,'Research draft for author review | 20 October 2026');canvas.drawRightString(558,30,str(doc.page))
SimpleDocTemplate(str(OUT/'MANUSCRIPT.pdf'),pagesize=(612,792),rightMargin=60,leftMargin=60,topMargin=48,bottomMargin=48,title='Source Recall Does Not Guarantee Transfer',author='Hanumantha Rao Vulli').build(story,onFirstPage=footer,onLaterPages=footer)
print('Created manuscript Markdown and PDF')
