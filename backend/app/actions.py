from enum import Enum

class LogAction(str, Enum):
    """
    Enum for all loggable actions in the system.
    Used by ActivityLog to track user interactions and system events.
    """

    # ============ Conversation Flow ============
    START_CONVERSATION = "start_conversation"
    REPLY_USER = "reply_user"
    REPLY_LLM = "reply_llm"
    RESET_CONVERSATION = "reset_conversation"
    CONVERSATION_ARCHIVED = "conversation_archived"

    # ============ Context Management ============
    CONTEXT_SET = "context_set"
    CONTEXT_COMPLETED = "context_completed"
    CONTEXT_CHANGE = "context_change"

    # ============ Strategy Detection & Evaluation ============
    STRATEGY_DETECTED = "strategy_detected"
    STRATEGY_NOT_DETECTED = "strategy_not_detected"
    STRATEGY_STORED = "strategy_stored"
    STRATEGY_VALIDATED = "strategy_validated"
    FREQUENCY_ASKED = "frequency_asked"
    FREQUENCY_RATED = "frequency_rated"
    FREQUENCY_UPDATED = "frequency_updated"

    # ============ Interview Lifecycle ============
    INTRO_STEP = "intro_step"
    INTRO_STEP_COMPLETED = "intro_step_completed"
    STRATEGY_STEP = "strategy_step"
    STRATEGY_STEP_COMPLETED = "strategy_step_completed"
    FREQUENCY_STEP = "frequency_step"
    FREQUENCY_STEP_COMPLETED = "frequency_step_completed"
    INTERVIEW_COMPLETE = "interview_complete"
    STEP_UPDATED = "step_updated"
    TURN_UPDATED = "turn_updated"

    # ============ Evaluation & Summary ============
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_GENERATED = "evaluation_generated"
    STRATEGY_EVALUATED = "strategy_evaluated"
    SUMMARY_GENERATED = "summary_generated"

    # ============ User Management ============
    NEW_USER = "new_user"
    USER_CREATED = "user_created"
    USER_RETRIEVED = "user_retrieved"
    STUDY_SUBJECT_STORED = "study_subject_stored"
    USER_LANGUAGE_REQUESTED = "user_language_requested"

    # ============ Data Storage ============
    ANSWER_STORED = "answer_stored"
    LLM_ANSWER_STORED = "llm_answer_stored"

    # ============ Errors & Debugging ============
    ERROR_OCCURRED = "error_occurred"
    DB_ROLLBACK = "db_rollback"
    USER_NOT_FOUND = "user_not_found"
    LANGUAGE_NOT_SUPPORTED = "language_not_supported"

    # ============ API Calls ============
    API_CALL_START = "api_call_start"
    API_CALL_SUCCESS = "api_call_success"
    API_CALL_ERROR = "api_call_error"

    # ============ Translation & Config ============
    TRANSLATION_REQUESTED = "translation_requested"
    TRANSLATION_ERROR = "translation_error"

    # ============ Tab Visibility ============
    TAB_HIDDEN = "tab_hidden"
    TAB_VISIBLE = "tab_visible"

    # ============ Navigation ============
    PAGE_VIEW = "page_view"

    # ============ Mouse Tracking ============
    MOUSE_TRACE = "mouse_trace"