# ADR-002: Rule-Based Matching Over ML-Based Approaches

> Status: Accepted
> Date: 2026-02-25
> Deciders: Engineering Team
> Supersedes: None
> Superseded by: None

## Context

The matching module must identify the same or related products listed across Shopee Thailand and TikTok Shop Thailand. This is a critical component: incorrect matches directly mislead users about cross-platform pricing and competitive positioning.

We evaluated two broad approaches:

### Approach A: ML-Based Matching

Use machine learning models (e.g., fine-tuned sentence transformers, Siamese networks, or classification models) to learn product similarity from labeled examples.

**Typical ML matching pipeline**:
1. Generate candidate pairs (blocking).
2. Encode product features into embeddings.
3. Compute similarity using a trained model.
4. Classify match/no-match using a trained threshold or classifier.

### Approach B: Rule-Based Matching (Chosen)

Use deterministic, configurable rules with weighted scoring across multiple signals (brand, spec, title, price) to compute match scores.

**Rule-based matching pipeline**:
1. Generate candidate pairs (brand+category blocking + TF-IDF pre-filter).
2. Compute individual signal scores using deterministic functions.
3. Compute weighted composite score.
4. Classify by threshold bands: auto-accept, review, reject.

## Decision

We will use **rule-based matching** for the MVP and foreseeable future. ML-based matching remains a potential enhancement for later phases if the rule-based approach proves insufficient.

## Rationale

### 1. Explainability

**Rule-based**: Every match decision can be fully explained by the individual signal scores and the composite scoring formula. The `reasons` structure (see [matching-design.md](../design/matching-design.md)) provides a human-readable breakdown of exactly why two products matched or did not match.

Example explanation:
```
"This pair scored 0.82 because:
 - Brand: 1.0 (exact match: NIVEA = NIVEA)
 - Spec: 0.30 (volume mismatch: 500ml vs 200ml)
 - Title: 0.72 (high token overlap, minor differences)
 - Price: 0.70 (price ratio 0.87)
 Combined: 0.30*1.0 + 0.25*0.30 + 0.30*0.72 + 0.15*0.70 = 0.82"
```

**ML-based**: A neural network or ensemble model produces a score, but explaining why that specific score was assigned is difficult. Techniques like SHAP or LIME can approximate explanations, but they add complexity and are not always reliable for text-based features.

**Why this matters**: Reviewers in the review queue need to understand why the system made a particular suggestion. Clear, deterministic explanations dramatically reduce review time and improve reviewer accuracy.

### 2. Auditability

**Rule-based**: The complete matching logic is codified in configuration files (weights, thresholds, brand aliases). Every configuration version is tracked. Given the same input data and the same rule version, the output is 100% reproducible. This makes the system auditable:
- "Why did this match exist on February 15?" -> Look up the rule_version, apply it to the February 15 data, and reproduce the exact result.
- "What changed between this week and last week?" -> Diff the rule versions.

**ML-based**: Model weights are opaque. Reproducing a past decision requires the exact model checkpoint, the exact feature extraction pipeline, and potentially the exact random seed. Model retraining may produce different weights, meaning the same input could yield different outputs after retraining.

**Why this matters**: For a competitive intelligence platform, stakeholders need confidence that the data is correct and consistent. Auditable matching builds this trust.

### 3. No Training Data Needed (Cold Start)

**Rule-based**: Works from day one with zero labeled examples. The rules are designed based on domain knowledge of how e-commerce products are structured (brand, title, specifications, price). The initial weights and thresholds are set based on reasonable heuristics and can be tuned using the review queue feedback.

**ML-based**: Requires a labeled training set of product pairs annotated as match/no-match. For a new market (Thailand), new category (personal care), and new platform combination (Shopee + TikTok Shop), no such training set exists. Creating one requires:
- Manual labeling of hundreds to thousands of product pairs.
- Ensuring label quality and consistency.
- Handling class imbalance (most pairs are non-matches).
- Re-labeling when new product types or brands appear.

Estimated effort to create an initial training set: 2-4 weeks of manual labeling for ~2,000 pairs.

**Why this matters**: The MVP timeline does not accommodate a multi-week labeling effort. Rule-based matching lets us ship the matching module immediately and start collecting implicit training data (from review decisions) that could fuel a future ML model.

### 4. Iterability and Control

**Rule-based**: When a specific type of matching error is identified, it can be fixed surgically:
- "Products from brand X are not matching because of a brand alias issue" -> Add the alias to the dictionary. Instant fix.
- "Products with very different prices are being matched when they shouldn't be" -> Increase the price weight or tighten the price score thresholds. Predictable impact.
- "Variant products (same product, different size) should be a separate match type" -> Add a match type classification rule based on spec_score ranges.

**ML-based**: Fixing a specific error type in an ML model typically requires:
- Adding correctly labeled examples of the error case to the training set.
- Retraining the model.
- Evaluating the retrained model on the full test set to check for regressions.
- Deploying the new model.

This cycle takes days even for minor fixes, and there is always the risk of regressions (fixing one error type may break another).

### 5. Computational Simplicity

**Rule-based**: The scoring functions are simple arithmetic operations (string comparison, set intersection, ratio calculation). No GPU required. No model serving infrastructure. The entire matching module runs in a few minutes on a laptop for our data volume (~1,200 products).

**ML-based**: Embedding computation (especially for transformer models) requires significant compute. Serving a model adds infrastructure complexity (model registry, serving endpoint, version management). For 1,200 products, this is significant over-engineering.

### 6. Domain Fit

E-commerce product matching for a specific category (personal care) in a specific market (Thailand) has well-defined structure:
- Products always have brands (a critical discriminator).
- Products have standardized specifications (volume, weight, variant).
- Titles follow predictable patterns per platform.
- Prices are comparable within a reasonable range.

This structured domain is well-suited to rule-based approaches where domain knowledge can be directly encoded.

## When to Reconsider

ML-based matching should be reconsidered when:

1. **Scale exceeds rule manageability**: If we expand to 10+ categories and 5+ countries, maintaining per-category, per-market rules may become unwieldy.
2. **Training data becomes available**: The review queue generates labeled data over time. After accumulating ~5,000 reviewed pairs with high agreement rate (>90%), an ML model could be trained as a complement.
3. **Diminishing returns on rule tuning**: If rule-based precision/recall plateaus and the review queue remains large despite tuning, ML may break through the ceiling.
4. **New data modalities**: If we start using product images for matching, ML (specifically visual similarity models) would be the natural approach.

## Hybrid Path Forward

The architecture does not preclude a future hybrid approach:

```
[Rule-Based Scoring] --> composite_score, reasons
                              |
                         (future addition)
                              |
[ML-Based Scoring]  --> ml_score, ml_confidence
                              |
                              v
                    [Ensemble / Meta-Scorer]
                              |
                              v
                    [Final Score + Disposition]
```

A future ML model could:
- Run alongside the rule-based scorer.
- Provide an additional signal that the ensemble combines with the rule-based score.
- Be used only for the review band (0.65-0.85) to help auto-resolve borderline cases.

This hybrid approach preserves the explainability of the rule-based system while leveraging ML for the hardest cases.

## Consequences

### Positive

- Matching module ships with the MVP on day one, no labeling delay.
- Every match decision is fully explainable and auditable.
- Rules can be tuned quickly based on reviewer feedback.
- No ML infrastructure required (GPU, model serving, training pipeline).
- 100% reproducible: same input + same rules = same output, always.

### Negative

- Rules may struggle with unstructured or noisy data (e.g., titles with no recognizable brand or specs).
- Adding a new category requires designing new category-specific rules (though most rules are generic).
- The ceiling for precision/recall may be lower than a well-trained ML model.
- Maintaining rule complexity as the system grows may require more engineering effort than retraining a model.

### Risks

- **Rule brittleness**: A rule that works well for shampoo may not work for skincare serums. Mitigated by having sub-category-specific rule overrides.
- **Reviewer fatigue**: If the review band (0.65-0.85) is too wide, too many items land in the queue. Mitigated by threshold tuning (see [matching-design.md](../design/matching-design.md)).
- **Bias toward known brands**: Products from unknown brands get lower brand scores, which may systematically undervalue matches for new or niche brands. Mitigated by the unknown_brand block handling and reviewer attention.

## Related Documents

- [../design/matching-design.md](../design/matching-design.md) - Full matching algorithm specification
- [../design/system-design.md](../design/system-design.md) - Matching module in the system context
- [../runbooks/review-backlog.md](../runbooks/review-backlog.md) - Handling review queue backlog
