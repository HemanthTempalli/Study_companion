# AI Evaluation Framework

## Overview

The AI Evaluation framework ensures LLM outputs meet quality requirements across all AI-powered features. Results are stored in the `ai_evaluations` table for tracking over time.

## Evaluation Dimensions

### 1. Quiz Question Quality
- **Relevance**: Questions should relate to uploaded material content
- **Difficulty Match**: Generated difficulty should match requested level
- **Option Quality (MCQ)**: Distractors should be plausible but clearly wrong
- **Answer Validity**: Correct answer should be unambiguously correct

### 2. Tutor Response Quality
- **Groundedness**: Answers should be supported by retrieved document chunks
- **Citation Accuracy**: Citations should reference real pages and content
- **Insufficient Evidence Detection**: System should flag when evidence is limited
- **Hallucination Prevention**: Answers should not contain fabricated information

### 3. Quiz Evaluation Accuracy
- **MCQ Grading**: Binary correct/incorrect should be deterministic
- **Open-Ended Scoring**: Scores should be consistent across similar answers
- **Feedback Quality**: Explanations should be educational and specific

### 4. Recommendation Quality
- **Actionability**: Recommendations should be specific and actionable
- **Novelty**: Should not repeat previous recommendations
- **Relevance**: Should target actual weak concepts

## Evaluation Schema

```python
class AIEvaluation:
    feature: str          # "quiz_generation", "tutor_response", etc.
    test_case_name: str   # "basic_science_question", etc.
    input_data: dict      # The input sent to the AI
    expected_output: dict  # What we expected
    actual_output: dict   # What the AI returned
    score: float          # 0-100
    passed: bool          # Whether it met the threshold
    details: dict         # Specific failure reasons
```

## Quality Thresholds

| Feature | Metric | Threshold |
|---------|--------|-----------|
| Quiz Generation | Valid JSON output | 100% |
| Quiz Generation | Relevant questions | > 80% |
| Tutor Response | Grounded answers | > 90% |
| Tutor Response | Citation accuracy | > 85% |
| Quiz Evaluation | MCQ accuracy | 100% |
| Quiz Evaluation | Open-ended consistency | > 75% |
| Recommendations | Actionable output | > 90% |

## Running Evaluations

Evaluations can be triggered via the admin dashboard or programmatically:

```python
from app.ai.evaluation import run_evaluation_suite

results = await run_evaluation_suite(db, feature="quiz_generation")
```

## Structured Output Robustness

All AI calls use structured JSON schemas with retry logic:

1. First attempt: Standard prompt with JSON format instructions
2. If JSON parsing fails: Retry with stricter "RESPOND ONLY WITH JSON" prompt
3. If second attempt fails: Return safe default (`{}`)

This ensures the system never crashes due to malformed AI output.
