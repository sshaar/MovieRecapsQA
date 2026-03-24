"""
Data loader for MovieRecapsQA dataset from HuggingFace Hub.

This module handles loading the dataset and providing utilities for
accessing questions, facts, segments, and recaps.
"""

import json
from typing import Dict, List, Optional
from datasets import load_dataset
from config import DATASET_NAME


class MovieRecapsDataLoader:
    """Loader for MovieRecapsQA dataset from HuggingFace Hub."""

    def __init__(self, dataset_name: str = DATASET_NAME, cache_dir: Optional[str] = None):
        """
        Initialize the data loader.

        Args:
            dataset_name: Name of the dataset on HuggingFace Hub
            cache_dir: Optional cache directory for dataset
        """
        print(f"Loading dataset from HuggingFace Hub: {dataset_name}")
        self.dataset = load_dataset(dataset_name, cache_dir=cache_dir)

        # Convert to dictionaries for easier access
        self.recaps = {r['video_id']: r for r in self.dataset['recaps']}
        self.segments = self._index_segments()
        self.questions = list(self.dataset['questions'])
        self.facts = {f['fact_id']: f for f in self.dataset['facts']}

        print(f"Loaded {len(self.recaps)} recaps, {len(self.segments)} segments, "
              f"{len(self.questions)} questions, {len(self.facts)} facts")

    def _index_segments(self) -> Dict:
        """Index segments by video_id and segment_id."""
        segments = {}
        for seg in self.dataset['segments']:
            video_id = seg['video_id']
            segment_id = seg['segment_id']
            if video_id not in segments:
                segments[video_id] = {}
            segments[video_id][segment_id] = seg
        return segments

    def get_question(self, idx: int) -> Dict:
        """Get a question by index."""
        return self.questions[idx]

    def get_facts_for_question(self, question: Dict) -> List[str]:
        """
        Get the ground truth facts for a question.

        Args:
            question: Question dictionary with 'aligned_fact_ids'

        Returns:
            List of fact strings
        """
        fact_ids = question.get('aligned_fact_ids', [])
        return [self.facts[fid]['fact'] for fid in fact_ids if fid in self.facts]

    def get_segment(self, video_id: str, segment_id: int) -> Optional[Dict]:
        """Get a segment by video_id and segment_id."""
        return self.segments.get(video_id, {}).get(segment_id)

    def get_recap(self, video_id: str) -> Optional[Dict]:
        """Get recap metadata by video_id."""
        return self.recaps.get(video_id)

    def get_evaluation_item(self, question_idx: int) -> Dict:
        """
        Get a complete evaluation item with question, facts, and metadata.

        Args:
            question_idx: Index of the question

        Returns:
            Dictionary with question, facts, segment, and recap info
        """
        question = self.get_question(question_idx)
        facts = self.get_facts_for_question(question)
        segment = self.get_segment(question['video_id'], question['segment_id'])
        recap = self.get_recap(question['video_id'])

        return {
            'question_idx': question_idx,
            'video_id': question['video_id'],
            'segment_id': question['segment_id'],
            'question_id': question['question_id'],
            'question': question['question'],
            'ground_truth_answer': question['answer'],
            'verbose_question': question.get('verbose_question'),
            'vague_answer': question.get('vague_answer'),
            'facts': facts,
            'segment': segment,
            'recap': recap,
        }

    def __len__(self) -> int:
        """Return number of questions in dataset."""
        return len(self.questions)


def load_model_responses(response_file: str) -> Dict:
    """
    Load model responses from a JSONL file.

    Expected format for each line:
    {
        "question_idx": 0,
        "question": "...",
        "model_response": "...",
        "metadata": {...}
    }

    Args:
        response_file: Path to JSONL file with model responses

    Returns:
        Dictionary mapping question_idx to response data
    """
    responses = {}
    with open(response_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            question_idx = data['question_idx']
            responses[question_idx] = data
    return responses
