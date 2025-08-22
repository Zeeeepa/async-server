from enum import Enum


class JobType(str, Enum):
    INDEX_PROJECT = "index_project"
    RESEARCH_TASK = "research_task"
    EXECUTE_TASK = "execute_task"
    REVISE_TASK = "revise_task"
