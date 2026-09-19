"""Initial schema — all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from pgvector.sqlalchemy import Vector

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Users
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='USER'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Spaces
    op.create_table('spaces',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, server_default=''),
        sa.Column('color', sa.String(7), server_default='#6366f1'),
        sa.Column('icon', sa.String(50), server_default='book'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_spaces_user_id', 'spaces', ['user_id'])

    # Projects
    op.create_table('projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('space_id', UUID(as_uuid=True), sa.ForeignKey('spaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, server_default=''),
        sa.Column('learning_goal', sa.Text, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_index('ix_projects_space_id', 'projects', ['space_id'])

    # Materials
    op.create_table('materials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger, server_default='0'),
        sa.Column('page_count', sa.Integer, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='QUEUED'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_materials_project_id', 'materials', ['project_id'])

    # Document Chunks
    op.create_table('document_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('material_id', UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', Vector(384)),
        sa.Column('metadata', JSON, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_chunks_material_id', 'document_chunks', ['material_id'])
    op.create_index('ix_chunks_project_id', 'document_chunks', ['project_id'])

    # Concepts
    op.create_table('concepts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_concepts_name', 'concepts', ['name'])

    # Project Concepts
    op.create_table('project_concepts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_id', UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='SET NULL'), nullable=True),
        sa.Column('relevance_score', sa.Float, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_project_concepts_project_id', 'project_concepts', ['project_id'])

    # Conversations
    op.create_table('conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), server_default='New conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_conversations_project_id', 'conversations', ['project_id'])

    # Messages
    op.create_table('messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('citations', JSON, server_default='[]'),
        sa.Column('has_sufficient_evidence', sa.Boolean, server_default='true'),
        sa.Column('metadata', JSON, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # Learning Context
    op.create_table('learning_context',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('learning_goals', JSON, server_default='[]'),
        sa.Column('strengths', JSON, server_default='[]'),
        sa.Column('weaknesses', JSON, server_default='[]'),
        sa.Column('important_history', JSON, server_default='[]'),
        sa.Column('repeated_mistakes', JSON, server_default='[]'),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Quiz Attempts
    op.create_table('quiz_attempts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_questions', sa.Integer, server_default='0'),
        sa.Column('correct_answers', sa.Integer, server_default='0'),
        sa.Column('score', sa.Float, server_default='0'),
        sa.Column('completed', sa.Boolean, server_default='false'),
        sa.Column('difficulty_level', sa.String(20), server_default='MEDIUM'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_quiz_attempts_project_id', 'quiz_attempts', ['project_id'])

    # Questions
    op.create_table('questions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_attempt_id', UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),
        sa.Column('concept_name', sa.String(500)),
        sa.Column('difficulty', sa.String(20), server_default='MEDIUM'),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('options', JSON),
        sa.Column('correct_answer', sa.Text, nullable=False),
        sa.Column('explanation', sa.Text, server_default=''),
        sa.Column('source_page', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_questions_quiz_id', 'questions', ['quiz_attempt_id'])

    # Answers
    op.create_table('answers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('user_answer', sa.Text, nullable=False),
        sa.Column('is_correct', sa.Boolean),
        sa.Column('score', sa.Float, server_default='0'),
        sa.Column('feedback', JSON, server_default='{}'),
        sa.Column('evaluated', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Mastery Records
    op.create_table('mastery_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_name', sa.String(500), nullable=False),
        sa.Column('mastery_level', sa.Float, server_default='0'),
        sa.Column('evidence_count', sa.Integer, server_default='0'),
        sa.Column('last_assessed', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('history', JSON, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_mastery_project_concept', 'mastery_records', ['project_id', 'concept_name'], unique=True)

    # Learning Events
    op.create_table('learning_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('metadata', JSON, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_events_project', 'learning_events', ['project_id'])
    op.create_index('ix_events_type_created', 'learning_events', ['event_type', 'created_at'])

    # Recommendations
    op.create_table('recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommendation_text', sa.Text, nullable=False),
        sa.Column('reasoning', sa.Text, server_default=''),
        sa.Column('action_type', sa.String(100), server_default='review'),
        sa.Column('target_concepts', JSON, server_default='[]'),
        sa.Column('target_pages', JSON, server_default='[]'),
        sa.Column('is_dismissed', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_recommendations_project', 'recommendations', ['project_id'])

    # Background Jobs
    op.create_table('background_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='QUEUED'),
        sa.Column('payload', JSON, server_default='{}'),
        sa.Column('result', JSON),
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('idempotency_key', sa.String(500), unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_jobs_status_created', 'background_jobs', ['status', 'created_at'])

    # AI Usage Logs
    op.create_table('ai_usage_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL')),
        sa.Column('feature', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('latency_ms', sa.Integer, server_default='0'),
        sa.Column('input_tokens', sa.Integer, server_default='0'),
        sa.Column('output_tokens', sa.Integer, server_default='0'),
        sa.Column('estimated_cost', sa.Float, server_default='0'),
        sa.Column('status', sa.String(20), server_default='success'),
        sa.Column('error_message', sa.Text),
        sa.Column('request_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ai_logs_feature', 'ai_usage_logs', ['feature', 'created_at'])

    # AI Evaluations
    op.create_table('ai_evaluations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('feature', sa.String(100), nullable=False),
        sa.Column('test_case_name', sa.String(255), nullable=False),
        sa.Column('input_data', JSON, nullable=False),
        sa.Column('expected_output', JSON),
        sa.Column('actual_output', JSON),
        sa.Column('score', sa.Float),
        sa.Column('passed', sa.Boolean),
        sa.Column('details', JSON, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    tables = [
        'ai_evaluations', 'ai_usage_logs', 'background_jobs', 'recommendations',
        'learning_events', 'mastery_records', 'answers', 'questions', 'quiz_attempts',
        'learning_context', 'messages', 'conversations', 'project_concepts', 'concepts',
        'document_chunks', 'materials', 'projects', 'spaces', 'users',
    ]
    for t in tables:
        op.drop_table(t)
    op.execute('DROP EXTENSION IF EXISTS vector')
