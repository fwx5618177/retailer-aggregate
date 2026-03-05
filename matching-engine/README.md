# matching-engine

Cross-platform matching engine for the SEA Retailer Top Selling Intelligence platform. Matches TikTok Shop items against Shopee items using rule-based recall and weighted fusion scoring.

## Architecture

```
TikTok items ─┐                    ┌─ auto_accepted (>=0.85)
              ├→ Recall → Filter → Score → Threshold ─┤─ needs_review (0.65-0.85)
Shopee items ─┘                    └─ no_match (<0.65)
```

## Matching Pipeline

1. **Recall**: Brand+category rules + TF-IDF text similarity (top-K candidates)
2. **Filter**: Spec tolerance (+-10%), currency consistency
3. **Score**: Weighted fusion of brand (0.30), spec (0.25), title (0.30), price (0.15)
4. **Threshold**: Auto-accept >= 0.85, needs_review 0.65-0.85, no_match < 0.65
5. **Reasons**: Structured JSON with strong/weak evidence and field alignment details
6. **Override**: Merge existing human review decisions

## Usage

```bash
# Run matching
python -m sea_matching run --config config/default.yaml

# Run tests
pytest tests/ -v
```

## Configuration

See `config/default.yaml` for all options including scoring weights, thresholds, and recall strategies.
