from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class ModelUnavailableError(RuntimeError):
    """Raised when a real local Hugging Face model is required but missing."""


def is_emoji_or_symbol_only(text: str) -> bool:
    """
    Check whether a comment contains only emojis/symbols
    and no letters or numbers.

    Examples:
        "🔥🔥🔥"       -> True
        "❤️"          -> True
        "👏👏"        -> True
        "Wow 🔥"      -> False
        "Puli 🔥"     -> False
        "Love you ❤️" -> False
    """

    text = str(text).strip()

    # Remove non-word characters.
    # Unicode letters/numbers are preserved.
    cleaned = re.sub(r"[\W_]+", "", text, flags=re.UNICODE)

    return len(cleaned) == 0


class ClassifierService:
    """
    Loads the local Hugging Face model once
    and exposes batch classification.
    """

    # Toxic probability required before a comment
    # is classified as TOXIC.
    TOXIC_THRESHOLD = 0.63

    def __init__(
        self,
        model_path: str,
        batch_size: int = 16,
        max_length: int = 256,
    ):
        self.model_path = Path(model_path)
        self.batch_size = batch_size
        self.max_length = max_length

        self._tokenizer: Any = None
        self._model: Any = None
        self._torch: Any = None
        self._device: Any = None
        self._load_error: str | None = None

    @property
    def model_available(self) -> bool:
        return (self.model_path / "config.json").exists()

    @property
    def status(self) -> str:
        if self._model is not None:
            return f"Local Hugging Face model loaded on {self._device}"

        if self._load_error:
            return "Local model unavailable; demo classifier is active"

        return "Local model not configured; demo classifier is active"

    def _load(self) -> None:

        # Don't load the model again if already loaded.
        if self._model is not None:
            return

        if not self.model_available:
            raise ModelUnavailableError(
                f"No Hugging Face model was found at {self.model_path}. "
                "Set MODEL_PATH to the trained model directory."
            )

        try:

            import torch

            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )

            self._torch = torch

            # Use GPU if available.
            self._device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )

            # Load tokenizer.
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )

            # Load trained XLM-R model.
            self._model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )

            self._model.to(self._device)

            # Evaluation mode.
            self._model.eval()

        except Exception as exc:

            self._load_error = str(exc)

            raise ModelUnavailableError(
                "The configured local model could not be loaded. "
                "Check that its tokenizer and model files are complete."
            ) from exc

    def classify_batch(
        self,
        texts: list[str],
        allow_demo_fallback: bool = True,
    ) -> list[dict[str, Any]]:

        if not texts:
            return []

        # =====================================================
        # STEP 1
        # Prepare result list.
        #
        # We use the original indexes so that the predictions
        # always stay aligned with the original comments.
        # =====================================================

        predictions: list[dict[str, Any] | None] = [
            None for _ in texts
        ]

        # These comments will actually be sent to XLM-R.
        model_indices: list[int] = []
        model_texts: list[str] = []

        # =====================================================
        # STEP 2
        # Handle emoji/symbol-only comments.
        #
        # Examples:
        # 🔥🔥🔥
        # ❤️
        # 👏👏👏
        #
        # These are NOT sent to the model.
        # =====================================================

        for index, text in enumerate(texts):

            if is_emoji_or_symbol_only(text):

                predictions[index] = {
                    "label": "NON TOXIC",
                    "confidence": 0.99,
                    "probabilities": {
                        "NON TOXIC": 0.99,
                        "TOXIC": 0.01,
                    },
                }

            else:

                # Normal comments are sent to XLM-R.
                model_indices.append(index)
                model_texts.append(text)

        # =====================================================
        # STEP 3
        # If every comment contained only emojis/symbols,
        # return the results immediately.
        # =====================================================

        if not model_texts:
            return predictions  # type: ignore

        # =====================================================
        # STEP 4
        # Load the real model.
        # =====================================================

        try:

            self._load()

        except ModelUnavailableError:

            if not allow_demo_fallback:
                raise

            # Use demo classifier only if the real model
            # cannot be loaded.
            for index, text in zip(
                model_indices,
                model_texts,
            ):

                predictions[index] = self._demo_prediction(text)

            return predictions  # type: ignore

        # =====================================================
        # STEP 5
        # Run XLM-R in batches.
        # =====================================================

        for start in range(
            0,
            len(model_texts),
            self.batch_size,
        ):

            batch = model_texts[
                start : start + self.batch_size
            ]

            # Tokenization.
            encoded = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )

            # Move tensors to CPU/GPU.
            encoded = {
                key: value.to(self._device)
                for key, value in encoded.items()
            }

            # =================================================
            # STEP 6
            # Model prediction.
            # =================================================

            with self._torch.inference_mode():

                logits = self._model(
                    **encoded
                ).logits

                probabilities = (
                    self._torch.softmax(
                        logits,
                        dim=-1,
                    )
                    .cpu()
                    .tolist()
                )

            # =================================================
            # STEP 7
            # Convert probabilities into labels.
            # =================================================

            for local_index, row in enumerate(
                probabilities
            ):

                # Find the original position of this comment.
                original_index = model_indices[
                    start + local_index
                ]

                # ---------------------------------------------
                # IMPORTANT:
                #
                # class 0 = NON TOXIC
                # class 1 = TOXIC
                # ---------------------------------------------

                non_toxic_probability = float(row[0])

                toxic_probability = float(row[1])

                # ---------------------------------------------
                # Apply threshold.
                # ---------------------------------------------

                if (
                    toxic_probability
                    >= self.TOXIC_THRESHOLD
                ):

                    label = "TOXIC"
                    confidence = toxic_probability

                else:

                    label = "NON TOXIC"
                    confidence = non_toxic_probability

                # ---------------------------------------------
                # Store prediction in original position.
                # ---------------------------------------------

                predictions[original_index] = {

                    "label": label,

                    "confidence": confidence,

                    "probabilities": {

                        "NON TOXIC":
                            non_toxic_probability,

                        "TOXIC":
                            toxic_probability,
                    },
                }

        # =====================================================
        # STEP 8
        # Return predictions in EXACT same order as input.
        # =====================================================

        return predictions  # type: ignore

    @staticmethod
    def _demo_prediction(
        text: str,
    ) -> dict[str, Any]:
        """
        Transparent fallback classifier used only when
        the trained Hugging Face model is unavailable.
        """

        toxic_terms = {
            "idiot",
            "stupid",
            "hate",
            "ugly",
            "trash",
            "shut up",
            "loser",
            "dumb",
            "moron",
        }

        normalized = str(text).lower()

        matches = sum(
            1
            for term in toxic_terms
            if re.search(
                rf"\b{re.escape(term)}\b",
                normalized,
            )
        )

        toxic_probability = min(
            0.96,
            0.18 + (matches * 0.42),
        )

        if matches == 0:
            toxic_probability = 0.06

        # Apply same project threshold.
        label = (
            "TOXIC"
            if toxic_probability
            >= ClassifierService.TOXIC_THRESHOLD
            else "NON TOXIC"
        )

        confidence = (
            toxic_probability
            if label == "TOXIC"
            else 1 - toxic_probability
        )

        return {

            "label": label,

            "confidence": confidence,

            "probabilities": {

                "NON TOXIC":
                    1 - toxic_probability,

                "TOXIC":
                    toxic_probability,
            },
        }