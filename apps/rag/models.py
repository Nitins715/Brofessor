from django.db import models
from apps.core.models import BaseModel


class Conversation(BaseModel):
    """Chat session for interactive learning and knowledge exploration."""
    title = models.CharField(max_length=255, default="New Conversation")
    domain = models.ForeignKey(
        "roadmap.Domain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    skill = models.ForeignKey(
        "roadmap.Skill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conversation parameters (e.g. temperature, prompt template, active mode).",
    )

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Message(BaseModel):
    """Individual message exchange in a Conversation."""
    class SenderRole(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Brofessor Assistant"
        SYSTEM = "system", "System"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=32, choices=SenderRole.choices, default=SenderRole.USER)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Model name, generation latency, citations, prompt parameters.",
    )

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_role_display()}] {self.content[:60]}"


class RetrievedChunk(BaseModel):
    """Grounding context: links document chunks retrieved via vector similarity to a Message."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="retrieved_chunks")
    chunk = models.ForeignKey(
        "sources.DocumentChunk",
        on_delete=models.CASCADE,
        related_name="rag_retrievals",
    )
    similarity_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Cosine similarity score (0.0 to 1.0).",
    )
    rank = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Retrieved Chunk"
        verbose_name_plural = "Retrieved Chunks"
        ordering = ["message", "rank"]
        indexes = [
            models.Index(fields=["message", "rank"]),
        ]

    def __str__(self):
        return f"Msg {self.message_id} -> Chunk #{self.chunk_id} (Score: {self.similarity_score})"
