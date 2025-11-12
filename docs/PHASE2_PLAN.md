# Phase 2: Data-Driven Pattern Discovery & Scoring Algorithm
## Integrated Plan with Strategic Recommendations

**Status:** Planning  
**Prerequisites:** Phase 1 Complete (Property Universe Ingested)

---

## 🎯 Phase 2 Objectives

1. **Ingest Additional Data Sources** - Build complete intent signal dataset
2. **Pattern Discovery** - Identify correlations and predictive patterns
3. **Signal Processing** - Implement temporal decay and multi-signal correlation
4. **Feature Engineering** - Build comprehensive feature set
5. **Scoring Algorithm** - Develop predictive intent scoring model
6. **Validation & Testing** - Validate model performance and accuracy

---

## 📋 Detailed Task Breakdown

### **Week 1: Data Source Integration**

#### Task 2.1: Research & Document Additional Data Source APIs
**Priority:** CRITICAL  
**Effort:** 2-3 days  
**Dependencies:** None

**Deliverables:**
- [ ] Austin Code Compliance API client
  - Research endpoint, authentication, rate limits
  - Document data schema and update frequency
  - Create ingestion client with error handling
- [ ] NOAA Storm Events API client
  - Research API access (REST/GraphQL)
  - Document event types and geographic coverage
  - Create ingestion client with date range queries
- [ ] City of Austin 311 API client
  - Research endpoint and filtering capabilities
  - Document request types and status codes
  - Create ingestion client with pagination
- [ ] Travis County Deed Records API client
  - Research access method (API vs. bulk download)
  - Document deed types and transaction fields
  - Create ingestion client with date filtering

**Files to Create:**
- `backend/src/ingestion/austin_code_compliance.py`
- `backend/src/ingestion/noaa_storm_events.py`
- `backend/src/ingestion/austin_311.py`
- `backend/src/ingestion/travis_deeds.py`
- `docs/data-sources/austin-code-compliance.md`
- `docs/data-sources/noaa-storm-events.md`
- `docs/data-sources/austin-311.md`
- `docs/data-sources/travis-deeds.md`

---

#### Task 2.2: Address Matching & Property Linkage
**Priority:** CRITICAL  
**Effort:** 2-3 days  
**Dependencies:** Task 2.1

**Deliverables:**
- [ ] Address normalization service
  - Standardize address formats
  - Handle variations (St vs. Street, Ave vs. Avenue)
  - Parse and normalize components
- [ ] Property matching algorithm
  - Match violations/311 requests to properties by address
  - Match storm events to properties by ZIP/coordinates
  - Match deed records to properties by address/prop_id
  - Handle fuzzy matching for address variations
- [ ] Linkage validation
  - Confidence scoring for matches
  - Manual review queue for low-confidence matches
  - Deduplication of linked records

**Files to Create:**
- `backend/src/services/address_normalization.py`
- `backend/src/services/property_matching.py`
- `backend/src/ingestion/link_signals_to_properties.py`

**Integration Points:**
- Uses existing `Property` model
- Links to `CodeViolation`, `StormEvent`, `ServiceRequest`, `DeedRecord` models
- Non-breaking: Adds `prop_id` foreign keys to signal tables

---

#### Task 2.3: Historical Data Ingestion
**Priority:** HIGH  
**Effort:** 3-4 days  
**Dependencies:** Task 2.1, Task 2.2

**Deliverables:**
- [ ] Ingest 12-24 months of historical data
  - Code violations (last 24 months)
  - Storm events (last 12 months, or all available)
  - 311 requests (last 12 months)
  - Deed records (last 12 months)
- [ ] Data quality validation
  - Completeness checks
  - Linkage success rates
  - Temporal coverage analysis
- [ ] Historical data export for analysis
  - Export to CSV/Parquet for pattern discovery
  - Create analysis-ready datasets

**Files to Create:**
- `backend/src/ingestion/ingest_historical_signals.py`
- `backend/src/ingestion/export_analysis_data.py`

**Integration Points:**
- Populates existing signal tables
- Non-breaking: Adds historical records

---

### **Week 2: Pattern Discovery & Signal Processing**

#### Task 2.4: Temporal Signal Decay Implementation
**Priority:** HIGH (Strategic Recommendation)  
**Effort:** 1-2 days  
**Dependencies:** Task 2.3

**Deliverables:**
- [ ] Signal decay service
  - Exponential decay function with configurable half-life
  - Default: 30-day half-life for 30-day prediction window
  - Support for different decay rates by signal type
- [ ] Signal strength calculation
  - Calculate current strength for all signals
  - Store decayed strength in database
  - Real-time strength updates
- [ ] Decay parameter optimization
  - Test different half-lives (15, 30, 45, 60 days)
  - A/B test decay functions
  - Document optimal parameters

**Files to Create:**
- `backend/src/services/signal_decay.py`
- `backend/src/models/signal_strength.py` (optional: cache table)
- `backend/tests/unit/test_signal_decay.py`

**Integration Points:**
- Non-breaking: Adds decay calculation layer
- Can be applied to existing signals retroactively
- Works with all signal types (violations, storms, 311, deeds)

**Business Model Alignment:**
- Improves lead quality → higher conversion → better contractor satisfaction
- Enables premium pricing for high-strength signals

---

#### Task 2.5: Multi-Signal Correlation Analysis
**Priority:** HIGH (Strategic Recommendation)  
**Effort:** 2-3 days  
**Dependencies:** Task 2.4

**Deliverables:**
- [ ] Correlation analysis engine
  - Calculate pairwise correlations between signals
  - Identify high-correlation signal pairs
  - Document correlation matrix
- [ ] Interaction feature generation
  - Storm + Violation combinations
  - Property Age + Signal combinations
  - Deed + Property Value combinations
  - Geographic clustering signals
- [ ] Correlation-based scoring
  - Boost scores for high-correlation signal pairs
  - Penalize isolated signals
  - Weight multi-signal properties higher

**Files to Create:**
- `backend/src/analysis/correlation_analysis.py`
- `backend/src/services/signal_correlation.py`
- `backend/src/services/interaction_features.py`
- `notebooks/correlation_analysis.ipynb` (exploratory)

**Integration Points:**
- Non-breaking: Adds correlation layer on top of signals
- Creates new features without modifying existing data
- Can be enabled/disabled via configuration

**Business Model Alignment:**
- Higher correlation = higher intent = premium lead pricing
- Enables dynamic pricing based on signal strength

---

#### Task 2.6: Pattern Discovery Analysis
**Priority:** CRITICAL  
**Effort:** 3-4 days  
**Dependencies:** Task 2.5

**Deliverables:**
- [ ] Statistical pattern analysis
  - Identify patterns in historical data
  - Calculate conversion probabilities by signal type
  - Analyze time-to-conversion patterns
- [ ] Trade-specific pattern discovery
  - Roofing: Hail events, roof violations, age patterns
  - HVAC: Age patterns, 311 requests, seasonal patterns
  - Siding: Wind events, violation types, property age
  - Electrical: Age patterns, 311 requests, property value
- [ ] Pattern documentation
  - Document discovered patterns
  - Create pattern library
  - Validate patterns with domain experts (if available)

**Files to Create:**
- `backend/src/analysis/pattern_discovery.py`
- `notebooks/pattern_discovery.ipynb`
- `docs/patterns/discovered-patterns.md`

**Integration Points:**
- Informs scoring algorithm development
- Non-breaking: Analysis layer

---

### **Week 3: Feature Engineering**

#### Task 2.7: Comprehensive Feature Engineering
**Priority:** HIGH (Strategic Recommendation)  
**Effort:** 3-4 days  
**Dependencies:** Task 2.6

**Deliverables:**
- [ ] Temporal features
  - Days since last storm event
  - Days since code violation
  - Days since property sale
  - Days since first improvement year
  - Seasonal indicators (month, quarter, season)
- [ ] Aggregated features
  - Count of violations in last 30/60/90 days
  - Count of storm events in last 30/60/90 days
  - Count of 311 requests in last 30/60/90 days
  - Average property value in ZIP code
  - Property value percentile (vs. ZIP code)
  - Property age percentile (vs. ZIP code)
- [ ] Interaction features
  - Property age × market value (maintenance capacity)
  - Storm magnitude × property age (vulnerability)
  - Violation type × property value (affordability)
  - ZIP tier × property value (market dynamics)
  - Signal count × signal strength (multi-signal intensity)
- [ ] Behavioral features
  - Neighbor maintenance activity (geographic clustering)
  - Similar property maintenance rates
  - Historical maintenance patterns (if available)

**Files to Create:**
- `backend/src/features/temporal_features.py`
- `backend/src/features/aggregated_features.py`
- `backend/src/features/interaction_features.py`
- `backend/src/features/behavioral_features.py`
- `backend/src/features/feature_pipeline.py` (orchestration)
- `backend/tests/unit/test_features.py`

**Integration Points:**
- Non-breaking: Feature calculation layer
- Features computed on-demand or cached
- Can be added incrementally without breaking existing code

**Business Model Alignment:**
- Better features = better predictions = higher lead quality
- Enables more accurate pricing tiers

---

#### Task 2.8: Property Lifecycle Modeling
**Priority:** HIGH (Strategic Recommendation)  
**Effort:** 2-3 days  
**Dependencies:** Task 2.7

**Deliverables:**
- [ ] Lifecycle stage classification
  - Years 0-5: Minimal maintenance (warranty period)
  - Years 5-15: Routine maintenance
  - Years 15-25: Major system replacements (roof, HVAC, etc.)
  - Years 25+: Ongoing major maintenance
- [ ] Maintenance window prediction
  - Predict when property enters high-maintenance period
  - Combine with first improvement year
  - Identify properties entering critical maintenance windows
- [ ] Lifecycle-based scoring
  - Boost scores for properties in high-maintenance windows
  - Adjust scores based on lifecycle stage
  - Combine with other signals

**Files to Create:**
- `backend/src/services/property_lifecycle.py`
- `backend/src/models/property_lifecycle_stage.py` (optional: cache table)

**Integration Points:**
- Uses existing `Property` model (age, first_improvement_year)
- Non-breaking: Adds lifecycle classification
- Works with existing scoring system

**Business Model Alignment:**
- Lifecycle stage = predictable maintenance needs
- Enables proactive lead generation before peak seasons

---

### **Week 4: Scoring Algorithm Development**

#### Task 2.9: Baseline Scoring Algorithm
**Priority:** CRITICAL  
**Effort:** 3-4 days  
**Dependencies:** Task 2.8

**Deliverables:**
- [ ] Rule-based baseline model
  - Simple weighted sum of signals
  - Trade-specific scoring rules
  - Threshold-based classification
- [ ] Scoring service
  - Calculate intent score for property
  - Support trade-specific scoring
  - Real-time scoring capability
- [ ] Score validation
  - Validate scores against known patterns
  - Test edge cases
  - Performance testing (1k/sec target)

**Files to Create:**
- `backend/src/scoring/baseline_scorer.py`
- `backend/src/scoring/scoring_service.py`
- `backend/src/models/lead_score.py` (optional: cache table)
- `backend/tests/unit/test_scoring.py`

**Integration Points:**
- Uses all features from Task 2.7
- Uses signal decay from Task 2.4
- Uses correlation from Task 2.5
- Non-breaking: Scoring layer on top of features

**Business Model Alignment:**
- Intent score drives lead pricing
- Higher scores = premium pricing
- Enables dynamic pricing model

---

#### Task 2.10: Machine Learning Model (Optional Enhancement)
**Priority:** MEDIUM (Future Enhancement)  
**Effort:** 4-5 days  
**Dependencies:** Task 2.9, historical conversion data

**Deliverables:**
- [ ] ML model training pipeline
  - Feature preparation
  - Model training (Random Forest, XGBoost, or similar)
  - Hyperparameter tuning
  - Cross-validation
- [ ] Model evaluation
  - Precision/recall metrics
  - ROC-AUC score
  - Feature importance analysis
- [ ] Model deployment
  - Model versioning
  - A/B testing framework
  - Model monitoring

**Files to Create:**
- `backend/src/ml/model_training.py`
- `backend/src/ml/model_serving.py`
- `notebooks/ml_model_development.ipynb`

**Note:** This requires historical conversion data. Can be implemented after Phase 4 (feedback collection).

**Integration Points:**
- Can replace or complement baseline scorer
- Non-breaking: Can run alongside baseline model
- A/B test against baseline

---

#### Task 2.11: Trade-Specific Scoring
**Priority:** HIGH  
**Effort:** 2-3 days  
**Dependencies:** Task 2.9

**Deliverables:**
- [ ] Roofing-specific scoring
  - Hail events (high weight)
  - Roof violations (high weight)
  - Property age 15-25 years (medium weight)
  - Storm damage indicators
- [ ] HVAC-specific scoring
  - Property age patterns
  - 311 requests (HVAC-related)
  - Seasonal patterns (pre-summer/winter)
  - Property value (affordability)
- [ ] Siding-specific scoring
  - Wind events (high weight)
  - Siding violations (high weight)
  - Property age patterns
  - Aesthetic maintenance signals
- [ ] Electrical-specific scoring
  - Property age patterns
  - 311 requests (electrical-related)
  - Property value (affordability)
  - Safety-related signals

**Files to Create:**
- `backend/src/scoring/trade_scorers.py`
- `backend/src/scoring/scoring_factory.py` (trade-specific routing)

**Integration Points:**
- Extends baseline scorer
- Non-breaking: Adds trade-specific logic
- Can be enabled per trade

**Business Model Alignment:**
- Trade-specific scoring = better lead quality per trade
- Enables trade-specific pricing

---

### **Week 5: Validation & Testing**

#### Task 2.12: Model Validation & Performance Testing
**Priority:** CRITICAL  
**Effort:** 2-3 days  
**Dependencies:** Task 2.11

**Deliverables:**
- [ ] Validation framework
  - Holdout set validation
  - Temporal validation (train on past, test on future)
  - Cross-validation
- [ ] Performance metrics
  - Precision/recall at different thresholds
  - Score distribution analysis
  - Trade-specific performance
- [ ] Performance optimization
  - Query optimization for scoring
  - Caching strategy
  - Batch scoring optimization

**Files to Create:**
- `backend/src/validation/model_validation.py`
- `backend/src/validation/performance_metrics.py`
- `notebooks/validation_analysis.ipynb`

**Integration Points:**
- Validates scoring system
- Non-breaking: Testing layer

---

#### Task 2.13: Scoring System Integration
**Priority:** CRITICAL  
**Effort:** 2-3 days  
**Dependencies:** Task 2.12

**Deliverables:**
- [ ] Scoring API endpoints
  - Score single property
  - Batch scoring
  - Trade-specific scoring
- [ ] Scoring scheduler
  - Daily score recalculation
  - Real-time score updates (on signal changes)
  - Score refresh pipeline
- [ ] Score storage
  - Store scores in database
  - Score history tracking
  - Score change detection

**Files to Create:**
- `backend/src/api/scoring.py` (FastAPI endpoints)
- `backend/src/services/score_scheduler.py`
- `backend/src/models/lead_score.py` (if not created earlier)

**Integration Points:**
- Integrates with FastAPI backend
- Non-breaking: New endpoints
- Ready for Phase 3 (production engine)

---

## 🔄 Integration Strategy (Non-Breaking)

### Modular Architecture
All Phase 2 components are designed as **additive layers**:

1. **Data Layer** (Existing)
   - Properties, Signals (violations, storms, 311, deeds)
   - No changes to existing models

2. **Processing Layer** (New)
   - Signal decay, correlation, feature engineering
   - Computed on-demand or cached
   - Can be disabled/enabled via config

3. **Scoring Layer** (New)
   - Scoring algorithms
   - Can run alongside existing systems
   - A/B testable

4. **API Layer** (New)
   - New endpoints for scoring
   - Doesn't modify existing endpoints

### Backward Compatibility
- All new features are **optional**
- Existing functionality remains unchanged
- Can roll back any component independently
- Feature flags for gradual rollout

### Database Changes
- New tables for caching (optional)
- New columns with defaults (non-breaking)
- Migrations are additive only

---

## 📊 Success Metrics

### Technical Metrics
- [ ] Scoring performance: 1,000 properties/sec
- [ ] API response time: p95 < 500ms
- [ ] Feature calculation: < 100ms per property
- [ ] Data freshness: < 24 hours for all signals

### Business Metrics (Post-Launch)
- [ ] Lead quality score distribution: Mean > 0.6
- [ ] Conversion rate: > 15% (industry benchmark: 10-20%)
- [ ] Signal correlation: > 0.3 for key pairs
- [ ] Trade-specific accuracy: > 70% precision

---

## 🚨 Risks & Mitigations

### Risk 1: Data Source Availability
**Risk:** APIs may be unavailable or have rate limits  
**Mitigation:** 
- Implement robust retry logic
- Cache historical data
- Fallback to alternative sources

### Risk 2: Address Matching Accuracy
**Risk:** Fuzzy matching may create false links  
**Mitigation:**
- Confidence scoring for matches
- Manual review queue
- Validation against known good matches

### Risk 3: Model Performance
**Risk:** Scoring may not meet accuracy targets  
**Mitigation:**
- Start with rule-based (proven patterns)
- Iterate based on feedback
- A/B test improvements

### Risk 4: Feature Engineering Complexity
**Risk:** Too many features may cause overfitting  
**Mitigation:**
- Start with high-impact features
- Feature importance analysis
- Regularization in ML models

---

## ✅ Phase 2 Completion Criteria

- [ ] All data sources ingested and linked to properties
- [ ] Signal decay implemented and tested
- [ ] Multi-signal correlation analysis complete
- [ ] Feature engineering pipeline operational
- [ ] Baseline scoring algorithm deployed
- [ ] Trade-specific scoring implemented
- [ ] Scoring API endpoints functional
- [ ] Performance targets met (1k/sec)
- [ ] Validation metrics documented
- [ ] Documentation complete

**Status:** Ready for Phase 3 (Production Scoring Engine)

---

## 🔗 Dependencies on Future Phases

### Phase 3 Dependencies
- Scoring system must be production-ready
- Performance targets must be met
- API endpoints must be stable

### Phase 4 Dependencies
- Scoring system must generate lead lists
- Trade-specific scoring must be functional
- Score thresholds must be defined

### Phase 5 Dependencies (Feedback Loop)
- Scoring system must be A/B testable
- Model versioning must be in place
- Performance monitoring must be operational

---

## 📝 Notes

- **Incremental Development:** Each task can be developed and tested independently
- **Feature Flags:** Use configuration to enable/disable features
- **Testing:** Unit tests for each component, integration tests for workflows
- **Documentation:** Document all patterns, correlations, and scoring logic
- **Performance:** Optimize early, profile regularly, cache aggressively

---

**Phase 2 Estimated Duration:** 4-5 weeks  
**Team Size:** 1-2 developers  
**Critical Path:** Data Sources → Pattern Discovery → Scoring Algorithm

