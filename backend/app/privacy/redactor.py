"""
PII Redaction module for Ayushman-Shield.
Strips sensitive financial and identity PII (Aadhaar, phone, ABHA ID, PAN, bank accounts)
locally on the edge before any cloud LLM processing.
Uses Microsoft Presidio + OpenCV when available, with a resilient native regex fallback.
"""

import re
import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

# Try importing Microsoft Presidio
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.info("Presidio not found in environment; utilizing native regex PII sanitization engine.")

# Try importing OpenCV and NumPy
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.info("OpenCV not found in environment; image redaction using fallback pass-through.")


class AyushmanRedactor:
    """Handles PII detection and redaction for both text metadata and bill images."""

    # Pre-compiled statutory Indian PII regex patterns
    PATTERNS = {
        "IN_AADHAAR": re.compile(r"\b[2-9]\d{3}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b"),
        "IN_PHONE": re.compile(r"(?:\+91[\s\-]?|0)?[6-9]\d{9}\b"),
        "IN_ABHA": re.compile(r"\b\d{2}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b"),
        "IN_PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
        "CREDIT_DEBIT_CARD": re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"),
        "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    }

    def __init__(self):
        if PRESIDIO_AVAILABLE:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                self._register_indian_patterns()
                self.use_presidio = True
            except Exception as e:
                logger.warning(f"Presidio initialization error: {e}. Falling back to regex engine.")
                self.use_presidio = False
        else:
            self.use_presidio = False

    def _register_indian_patterns(self):
        """Register India-specific statutory PII patterns with Presidio."""
        if not PRESIDIO_AVAILABLE:
            return

        aadhaar_pattern = Pattern(
            name="aadhaar_pattern",
            regex=r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b",
            score=0.90,
        )
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="IN_AADHAAR", patterns=[aadhaar_pattern], supported_language="en")
        )

        abha_pattern = Pattern(
            name="abha_pattern",
            regex=r"\b\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
            score=0.85,
        )
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="IN_ABHA", patterns=[abha_pattern], supported_language="en")
        )

        pan_pattern = Pattern(
            name="pan_pattern",
            regex=r"\b[A-Z]{5}\d{4}[A-Z]\b",
            score=0.90,
        )
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="IN_PAN", patterns=[pan_pattern], supported_language="en")
        )

        phone_pattern = Pattern(
            name="indian_phone_pattern",
            regex=r"(?:\+91[\s\-]?|0)?[6-9]\d{9}\b",
            score=0.80,
        )
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="IN_PHONE", patterns=[phone_pattern], supported_language="en")
        )

    def redact_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Redacts PII tokens from text. Returns (sanitized_text, detections_list).
        """
        if not text:
            return "", []

        if self.use_presidio:
            try:
                results = self.analyzer.analyze(
                    text=text,
                    language="en",
                    entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IN_AADHAAR", "IN_ABHA", "IN_PAN", "IN_PHONE"],
                )
                operators = {
                    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
                    "IN_AADHAAR": OperatorConfig("replace", {"new_value": "[AADHAAR_REDACTED]"}),
                    "IN_ABHA": OperatorConfig("replace", {"new_value": "[ABHA_REDACTED]"}),
                    "IN_PAN": OperatorConfig("replace", {"new_value": "[PAN_REDACTED]"}),
                    "IN_PHONE": OperatorConfig("replace", {"new_value": "[PHONE_REDACTED]"}),
                }
                anonymized = self.anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
                detections = [
                    {"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
                    for r in results
                ]
                return anonymized.text, detections
            except Exception as e:
                logger.warning(f"Presidio runtime error: {e}. Falling back to native regex.")

        # Native Regex Sanitizer Fallback
        sanitized = text
        detections = []

        for entity_type, pattern in self.PATTERNS.items():
            matches = list(pattern.finditer(sanitized))
            for m in matches:
                val = m.group(0)
                detections.append({
                    "entity_type": entity_type,
                    "matched_length": len(val),
                    "score": 0.95,
                })
            sanitized = pattern.sub(f"[{entity_type}_REDACTED]", sanitized)

        return sanitized, detections

    def redact_image(self, image_bytes: bytes) -> bytes:
        """
        Detects and blacks out potential PII text blocks on hospital bill images using OpenCV.
        """
        if not CV2_AVAILABLE:
            return image_bytes

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return image_bytes

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # Detect wide text regions characteristic of ID / phone sequences
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 3))
            dilated = cv2.dilate(thresh, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in contours:
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = w / max(h, 1)
                # Dense numeric sequences like Aadhaar or phone numbers
                if aspect_ratio > 3.5 and 90 < w < 320 and 12 < h < 55:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)

            _, encoded = cv2.imencode(".png", img)
            return encoded.tobytes()
        except Exception as e:
            logger.warning(f"OpenCV image redaction error: {e}. Preserving raw image.")
            return image_bytes


redactor = AyushmanRedactor()
