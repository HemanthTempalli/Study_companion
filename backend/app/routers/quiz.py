"""Quiz router — adaptive quiz generation, answer submission, and evaluation."""

import json
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import (
    User, QuizAttempt, Question, Answer, ProjectConcept, Concept,
    MasteryRecord, DocumentChunk, Material, EventType, QuestionType, Difficulty,
)
from app.schemas.schemas import (
    QuizGenerateRequest, QuizAttemptOut, QuestionOut, AnswerSubmit,
    AnswerFeedback, QuizResult,
)
from app.security.auth import get_student_user, verify_project_ownership
from app.ai.groq_provider import get_ai_provider, log_ai_usage, AIProviderError
from app.services.event_service import record_event
from app.services.mastery_service import update_mastery_from_answer

router = APIRouter(prefix="/api/projects/{project_id}/quiz", tags=["Quiz"])


QUIZ_GEN_PROMPT = """You are a quiz generator for a learning application.

Generate {num_questions} quiz questions based on the provided learning material.
Mix question types: approximately 70% MCQ and 30% open-ended.

For each question, consider:
- The student's weak concepts (prioritize these): {weak_concepts}
- The student's mastery levels: {mastery_info}
- Difficulty preference: {difficulty}

RULES:
1. Questions MUST be grounded in the provided material content.
2. For MCQ: provide exactly 4 options (A, B, C, D), one correct answer, and an explanation.
3. For open-ended: provide the expected answer/key points and an explanation.
4. Each question must be associated with a concept from the material.
5. Vary difficulty based on concept mastery — harder questions for well-known concepts.
6. Do NOT repeat questions the student has already seen: {previous_questions}

Respond as JSON:
{{
  "questions": [
    {{
      "question_type": "MCQ" or "OPEN_ENDED",
      "concept_name": "concept tested",
      "difficulty": "EASY" or "MEDIUM" or "HARD",
      "question_text": "The question...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."] or null,
      "correct_answer": "The correct answer or key points",
      "explanation": "Why this is the answer...",
      "source_page": "Material Name — Page N"
    }}
  ]
}}"""


@router.post("/generate", response_model=QuizAttemptOut)
async def generate_quiz(
    project_id: UUID,
    data: QuizGenerateRequest,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_project_ownership(project_id, user, db)

    # Get project concepts and mastery
    mastery_result = await db.execute(
        select(MasteryRecord).where(MasteryRecord.project_id == project_id)
    )
    mastery_records = mastery_result.scalars().all()
    weak_concepts = [m.concept_name for m in mastery_records if m.mastery_level < 60]
    mastery_info = {m.concept_name: f"{m.mastery_level:.0f}%" for m in mastery_records}

    # Get material content for grounding
    chunks_result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.project_id == project_id)
        .order_by(func.random())
        .limit(15)
    )
    chunks = chunks_result.scalars().all()
    if not chunks:
        raise HTTPException(status_code=400, detail="No processed materials found. Upload and process a PDF first.")

    material_content = "\n\n".join([
        f"[Page {c.page_number}]: {c.content[:500]}" for c in chunks
    ])

    # Get previous questions to avoid duplicates
    prev_q = await db.execute(
        select(Question.question_text)
        .where(Question.project_id == project_id)
        .order_by(Question.created_at.desc())
        .limit(20)
    )
    previous_questions = [q[0][:80] for q in prev_q.fetchall()]

    # Determine difficulty
    difficulty = data.difficulty or "ADAPTIVE"
    if difficulty == "ADAPTIVE" and mastery_records:
        avg_mastery = sum(m.mastery_level for m in mastery_records) / len(mastery_records)
        if avg_mastery < 40:
            difficulty = "EASY"
        elif avg_mastery < 70:
            difficulty = "MEDIUM"
        else:
            difficulty = "HARD"

    # Generate questions via Groq
    prompt = QUIZ_GEN_PROMPT.format(
        num_questions=data.num_questions,
        weak_concepts=", ".join(weak_concepts[:5]) or "None identified yet",
        mastery_info=json.dumps(mastery_info) if mastery_info else "No mastery data yet",
        difficulty=difficulty,
        previous_questions=json.dumps(previous_questions[:10]) if previous_questions else "None",
    )

    try:
        provider = get_ai_provider()
        result, stats = await provider.generate_structured(
            system_prompt=prompt,
            user_prompt=f"Material content:\n{material_content}",
            feature="quiz_generation",
        )
        await log_ai_usage(db, stats, user_id=user.id, project_id=project_id)
    except AIProviderError as e:
        raise HTTPException(status_code=503, detail=str(e.message))

    # Create quiz attempt
    quiz = QuizAttempt(
        project_id=project_id,
        user_id=user.id,
        total_questions=0,
        difficulty_level=Difficulty.MEDIUM if difficulty == "ADAPTIVE" else Difficulty(difficulty),
    )
    db.add(quiz)
    await db.flush()

    # Create questions from AI response
    questions_data = result.get("questions", [])
    if not questions_data:
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")

    question_count = 0
    for qd in questions_data[:data.num_questions]:
        q_type = QuestionType.MCQ if qd.get("question_type") == "MCQ" else QuestionType.OPEN_ENDED
        diff = Difficulty.MEDIUM
        try:
            diff = Difficulty(qd.get("difficulty", "MEDIUM"))
        except ValueError:
            pass

        question = Question(
            quiz_attempt_id=quiz.id,
            project_id=project_id,
            question_type=q_type,
            concept_name=qd.get("concept_name", "General"),
            difficulty=diff,
            question_text=qd.get("question_text", ""),
            options=qd.get("options"),
            correct_answer=qd.get("correct_answer", ""),
            explanation=qd.get("explanation", ""),
            source_page=qd.get("source_page"),
        )
        db.add(question)
        question_count += 1

    quiz.total_questions = question_count
    await db.flush()

    await record_event(db, user.id, project_id, EventType.QUIZ_STARTED, {
        "quiz_id": str(quiz.id), "num_questions": question_count, "difficulty": difficulty,
    })

    # Return quiz with questions
    q_result = await db.execute(
        select(Question).where(Question.quiz_attempt_id == quiz.id).order_by(Question.created_at)
    )
    questions_out = [QuestionOut.model_validate(q) for q in q_result.scalars().all()]

    return QuizAttemptOut(
        id=quiz.id,
        total_questions=quiz.total_questions,
        correct_answers=0,
        score=0.0,
        completed=False,
        difficulty_level=quiz.difficulty_level.value,
        created_at=quiz.created_at,
        questions=questions_out,
    )


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    project_id: UUID,
    quiz_id: UUID,
    answers: list[AnswerSubmit],
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)

    # Get quiz
    quiz_result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == quiz_id,
            QuizAttempt.project_id == project_id,
            QuizAttempt.user_id == user.id,
        )
    )
    quiz = quiz_result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.completed:
        raise HTTPException(status_code=400, detail="Quiz already completed")

    # Process each answer
    results = []
    correct_count = 0
    total_score = 0.0
    mastery_updates = []

    for ans in answers:
        q_result = await db.execute(
            select(Question).where(Question.id == ans.question_id, Question.quiz_attempt_id == quiz_id)
        )
        question = q_result.scalar_one_or_none()
        if not question:
            continue

        # Check if already answered
        existing = await db.execute(select(Answer).where(Answer.question_id == question.id))
        if existing.scalar_one_or_none():
            continue

        if question.question_type == QuestionType.MCQ:
            # MCQ: direct comparison
            is_correct = ans.user_answer.strip().upper()[:1] == question.correct_answer.strip().upper()[:1]
            # Also check if full answer text matches
            if not is_correct:
                is_correct = ans.user_answer.strip().lower() == question.correct_answer.strip().lower()
            score = 100.0 if is_correct else 0.0
            feedback = {}
        else:
            # Open-ended: evaluate via Groq
            is_correct, score, feedback = await evaluate_open_ended(
                db, question, ans.user_answer, user.id, project_id
            )

        answer = Answer(
            question_id=question.id,
            user_answer=ans.user_answer,
            is_correct=is_correct,
            score=score,
            feedback=feedback,
            evaluated=True,
        )
        db.add(answer)

        if is_correct:
            correct_count += 1
        total_score += score

        results.append(AnswerFeedback(
            question_id=question.id,
            is_correct=is_correct,
            score=score,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            feedback=feedback,
        ))

        # Update mastery
        if question.concept_name:
            mastery_update = await update_mastery_from_answer(
                db, project_id, user.id, question.concept_name, score, question.question_type.value
            )
            if mastery_update:
                mastery_updates.append(mastery_update)

        await record_event(db, user.id, project_id, EventType.QUESTION_ANSWERED, {
            "question_type": question.question_type.value,
            "concept": question.concept_name,
            "score": score,
            "is_correct": is_correct,
        })

    # Update quiz
    quiz.correct_answers = correct_count
    quiz.score = total_score / max(len(results), 1)
    quiz.completed = True
    quiz.completed_at = datetime.now(timezone.utc)
    await db.flush()

    # Record assessment completed
    await record_event(db, user.id, project_id, EventType.ASSESSMENT_COMPLETED, {
        "quiz_id": str(quiz.id),
        "score": quiz.score,
        "correct": correct_count,
        "total": len(results),
    })

    # Identify weak concepts
    weak_concepts = list(set(
        r.feedback.get("concept", "") for r in results
        if not r.is_correct and r.feedback.get("concept")
    ))

    return QuizResult(
        quiz_id=quiz.id,
        total_questions=len(results),
        correct_answers=correct_count,
        score=quiz.score,
        question_results=results,
        mastery_updates=mastery_updates,
        weak_concepts=weak_concepts,
    )


@router.get("/history", response_model=list[QuizAttemptOut])
async def get_quiz_history(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.project_id == project_id, QuizAttempt.user_id == user.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(20)
    )
    quizzes = result.scalars().all()
    return [QuizAttemptOut.model_validate(q) for q in quizzes]


async def evaluate_open_ended(
    db: AsyncSession, question: Question, user_answer: str, user_id: UUID, project_id: UUID
) -> tuple[bool, float, dict]:
    """Evaluate an open-ended answer using Groq."""
    eval_prompt = f"""Evaluate the student's answer to this question.

Question: {question.question_text}
Expected Answer / Key Points: {question.correct_answer}
Student's Answer: {user_answer}

Evaluate for:
1. Understanding of the concept
2. Accuracy of the answer
3. Key concepts covered
4. Missing concepts
5. Any mistakes

Respond as JSON:
{{
  "score": 0-100,
  "is_correct": true/false (true if score >= 60),
  "understood": ["concepts the student understood"],
  "missing": ["concepts the student missed"],
  "mistakes": ["specific mistakes made"],
  "explanation": "Detailed feedback for the student",
  "suggested_review": "What the student should review"
}}"""

    try:
        provider = get_ai_provider()
        result, stats = await provider.generate_structured(
            system_prompt="You are a fair and constructive academic evaluator. Evaluate student answers objectively.",
            user_prompt=eval_prompt,
            feature="assessment",
        )
        await log_ai_usage(db, stats, user_id=user_id, project_id=project_id)

        score = float(result.get("score", 50))
        is_correct = result.get("is_correct", score >= 60)
        feedback = {
            "understood": result.get("understood", []),
            "missing": result.get("missing", []),
            "mistakes": result.get("mistakes", []),
            "explanation": result.get("explanation", ""),
            "suggested_review": result.get("suggested_review", ""),
            "concept": question.concept_name,
        }
        return is_correct, score, feedback
    except AIProviderError:
        # Fallback: simple keyword matching
        expected_words = set(question.correct_answer.lower().split())
        answer_words = set(user_answer.lower().split())
        overlap = len(expected_words & answer_words) / max(len(expected_words), 1)
        score = min(overlap * 100, 100)
        return score >= 60, score, {"explanation": "Evaluation completed with basic matching.", "concept": question.concept_name}
