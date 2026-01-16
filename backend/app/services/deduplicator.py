import hashlib
from difflib import SequenceMatcher
from typing import List
from app.models.message import Message
import uuid


class DeduplicationService:
    def __init__(self, similarity_threshold: float = 0.9):
        """
        Initialize deduplication service

        Args:
            similarity_threshold: Minimum similarity ratio (0-1) to consider messages as duplicates
        """
        self.similarity_threshold = similarity_threshold

    def calculate_hash(self, text: str) -> str:
        """Calculate MD5 hash of normalized text"""
        # Normalize text: lowercase, remove extra whitespace
        normalized = ' '.join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts using SequenceMatcher"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def find_duplicates(self, messages: List[Message]) -> dict:
        """
        Find duplicate messages and group them

        Returns:
            Dictionary mapping duplicate_group_id to list of message IDs
        """
        groups = {}
        hash_to_group = {}
        processed = set()

        for message in messages:
            if message.id in processed:
                continue

            text = message.original_text
            text_hash = self.calculate_hash(text)

            # Check for exact duplicates (same hash)
            if text_hash in hash_to_group:
                group_id = hash_to_group[text_hash]
                groups[group_id].append(message.id)
                processed.add(message.id)
                continue

            # Check for fuzzy duplicates
            is_duplicate = False
            for existing_hash, group_id in hash_to_group.items():
                # Get first message from the group to compare
                first_msg_id = groups[group_id][0]
                first_msg = next((m for m in messages if m.id == first_msg_id), None)

                if first_msg:
                    similarity = self.calculate_similarity(text, first_msg.original_text)

                    if similarity >= self.similarity_threshold:
                        # Add to existing group
                        groups[group_id].append(message.id)
                        processed.add(message.id)
                        is_duplicate = True
                        break

            # If not a duplicate, create new group
            if not is_duplicate:
                group_id = str(uuid.uuid4())
                groups[group_id] = [message.id]
                hash_to_group[text_hash] = group_id
                processed.add(message.id)

        return groups

    def mark_duplicates(self, messages: List[Message]) -> List[Message]:
        """
        Mark messages as duplicates and assign group IDs

        Returns:
            Updated list of messages
        """
        if len(messages) <= 1:
            return messages

        groups = self.find_duplicates(messages)

        # Mark messages
        for group_id, message_ids in groups.items():
            if len(message_ids) > 1:
                # This is a duplicate group
                for message in messages:
                    if message.id in message_ids:
                        message.is_duplicate = True
                        message.duplicate_group_id = group_id
            else:
                # Single message, not a duplicate
                for message in messages:
                    if message.id in message_ids:
                        message.is_duplicate = False
                        message.duplicate_group_id = None

        return messages


# Singleton instance
deduplicator = DeduplicationService()
