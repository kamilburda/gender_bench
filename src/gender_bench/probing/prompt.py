import uuid
from typing import Any, Optional


class Prompt:
    """`Prompt` is a single input for a `generator`.

    Args:
        text (str): The text input for a `generator`.
        metadata (Optional[dict[str, Any]], optional): Metadata related to
            `Prompt` that can be used during evaluation of metric calculation
            process.
    Attributes:
        uuid (uuid.UUID): UUID identifier.
    """

    def __init__(self, text: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self.text = text
        self.metadata = metadata
        self.uuid: uuid.UUID = uuid.uuid4()

    def to_json_dict(self) -> dict:
        """Prepare a JSON-serializable dictionary representation. Used for
        logging.

        Returns:
            dict: JSON-serializable dictionary.
        """
        parameters = ["uuid", "text", "metadata"]
        d = {parameter: getattr(self, parameter) for parameter in parameters}
        return d

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "Prompt":
        """Create a new `Prompt` object from a JSON-serializable dictionary
        representation.

        Args:
            json_dict (dict): JSON-serializable dictionary. Generated by
                ``to_json_dict``.

        Returns:
            Attempt: Restored `Prompt` object.
        """
        prompt = cls(text=json_dict["text"], metadata=json_dict["metadata"])
        prompt.uuid = uuid.UUID(json_dict["uuid"])
        return prompt
