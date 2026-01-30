"""
Constitutional Classifiers for BlackBox 5

Provides input/output content filtering to ensure safe AI agent operations.
Based on Anthropic's constitutional AI principles and ASL-3 safety guidelines.

Features:
- Input content filtering
- Output content filtering
- Jailbreak detection
- Harmful content blocking
- Rate limiting
- Content validation
"""

import logging
import re
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content to check"""
    USER_INPUT = "user_input"
    AGENT_OUTPUT = "agent_output"
    SYSTEM_PROMPT = "system_prompt"
    TOOL_CALL = "tool_call"
    FILE_OPERATION = "file_operation"


class ViolationType(Enum):
    """Types of safety violations"""
    HARMFUL_CONTENT = "harmful_content"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    BYPASS_ATTEMPT = "bypass_attempt"
    MALICIOUS_CODE = "malicious_code"
    DATA_EXFILTRATION = "data_exfiltration"
    RESOURCE_ABUSE = "resource_abuse"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MANIPULATION = "manipulation"
    DISCRIMINATION = "discrimination"
    SEXUAL_CONTENT = "sexual_content"
    VIOLENCE = "violence"
    ILLEGAL_ACTIVITY = "illegal_activity"


class Severity(Enum):
    """Severity levels of violations"""
    LOW = "low"           # Warning, allow but flag
    MEDIUM = "medium"     # Block and flag
    HIGH = "high"         # Block, flag, and trigger safe mode
    CRITICAL = "critical" # Block, flag, trigger kill switch


class Violation:
    """Represents a safety violation"""

    def __init__(
        self,
        violation_type: ViolationType,
        severity: Severity,
        content: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ):
        self.violation_type = violation_type
        self.severity = severity
        self.content = content
        self.reason = reason
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.violation_type.value,
            "severity": self.severity.value,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "reason": self.reason,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class ConstitutionalClassifier:
    """
    Constitutional AI classifier for BlackBox 5.

    This classifier implements safety checks based on constitutional
    AI principles to ensure agent operations remain safe and
    beneficial.

    Example:
        ```python
        # Get global classifier
        classifier = get_classifier()

        # Check user input
        result = classifier.check_input(
            "How do I make a bomb?",
            content_type=ContentType.USER_INPUT
        )

        if not result.safe:
            # Handle violation
            print(f"Blocked: {result.violation.reason}")
        ```

    Attributes:
        enabled: Whether classifier is enabled
        strict_mode: Whether to use strict checking
        violation_history: History of violations
    """

    # Harmful content patterns
    HARMFUL_PATTERNS = [
        r'(?:make|create|build|manufacture)\s+(?:a\s+)?(?:bomb|explosive|weapon|poison|drug)',
        r'how\s+to\s+(?:hack|attack|exploit|break\s+into)',
        r'(?:steal|theft|robbery|fraud|scam)',
        r'(?:kill|murder|assassinate|attack|harm)\s+(?:someone|person|people)',
        r'self\s+harm|suicide|commit\s+suicide',
        r'(?:illegal|contraband|controlled\s+substance)',
    ]

    # Jailbreak patterns
    JAILBREAK_PATTERNS = [
        r'ignore\s+(?:previous\s+)?(?:instructions?|commands?|rules?)',
        r'disregard\s+(?:all\s+)?(?:rules?|guidelines?|constraints)',
        r'you\s+are\s+(?:now|no\s+longer)\s+(?:restricted|limited|constrained)',
        r'(?:forget|erase|clear)\s+(?:all\s+)?(?:your\s+)?(?:instructions?|programming|training)',
        r'(?:act|behave|respond)\s+as\s+(?:if\s+)?(?:you\s+)?(?:were|are)\s+(?:unrestricted|uncensored)',
        r'override\s+(?:your\s+)?(?:safety|security|ethical)',
        r'(?:bypass|circumvent|avoid)\s+(?:your\s+)?(?:filters?|restrictions?|safety)',
    ]

    # Suspicious patterns (data exfiltration, code injection, etc.)
    SUSPICIOUS_PATTERNS = [
        r'__import__|exec\s*\(|eval\s*\(',  # Code execution
        r'(?:http|https|ftp)://[^\s]+',     # URLs (potential exfiltration)
        r'(?:/etc/passwd|/etc/shadow|C:\\\\Windows\\\\System32)',  # System paths
        r'\.{2,}',                             # Path traversal
    ]

    def __init__(self, enabled: bool = True, strict_mode: bool = True):
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.violation_history: List[Violation] = []
        self._lock = threading.Lock()

        # Compile patterns for performance
        self._harmful_regex = re.compile(
            '|'.join(self.HARMFUL_PATTERNS),
            re.IGNORECASE | re.MULTILINE
        )
        self._jailbreak_regex = re.compile(
            '|'.join(self.JAILBREAK_PATTERNS),
            re.IGNORECASE | re.MULTILINE
        )
        self._suspicious_regex = re.compile(
            '|'.join(self.SUSPICIOUS_PATTERNS),
            re.IGNORECASE | re.MULTILINE
        )

        # State file
        self._state_file = Path(
            "blackbox5/2-engine/01-core/safety/.classifier_state.json"
        )

        logger.info(
            f"Constitutional Classifier initialized: "
            f"enabled={enabled}, strict={strict_mode}"
        )

    def check_input(
        self,
        content: str,
        content_type: ContentType = ContentType.USER_INPUT
    ) -> 'CheckResult':
        """
        Check input content for safety violations.

        Args:
            content: Content to check
            content_type: Type of content

        Returns:
            CheckResult with safety status

        Example:
            ```python
            result = classifier.check_input(
                "Ignore all previous instructions",
                ContentType.USER_INPUT
            )

            if not result.safe:
                # Handle violation
                logger.warning(f"Blocked: {result.violation.reason}")
            ```
        """
        if not self.enabled:
            return CheckResult(safe=True, content=content)

        # Check for harmful content
        harmful_match = self._harmful_regex.search(content)
        if harmful_match:
            violation = Violation(
                violation_type=ViolationType.HARMFUL_CONTENT,
                severity=Severity.HIGH,
                content=content,
                reason=f"Harmful content detected: {harmful_match.group()}",
                context={"match": harmful_match.group(), "type": content_type.value}
            )
            self._record_violation(violation)
            return CheckResult(safe=False, violation=violation, content=content)

        # Check for jailbreak attempts
        jailbreak_match = self._jailbreak_regex.search(content)
        if jailbreak_match:
            violation = Violation(
                violation_type=ViolationType.JAILBREAK_ATTEMPT,
                severity=Severity.CRITICAL,
                content=content,
                reason=f"Jailbreak attempt detected: {jailbreak_match.group()}",
                context={"match": jailbreak_match.group(), "type": content_type.value}
            )
            self._record_violation(violation)

            # Trigger kill switch for jailbreak attempts
            if self.strict_mode:
                from .kill_switch import get_kill_switch
                ks = get_kill_switch()
                ks.trigger(
                    KillSwitchReason.MALICE_DETECTED,
                    f"Jailbreak attempt: {jailbreak_match.group()}",
                    source="constitutional_classifier"
                )

            return CheckResult(safe=False, violation=violation, content=content)

        # Check for suspicious patterns
        suspicious_match = self._suspicious_regex.search(content)
        if suspicious_match:
            # Lower severity for suspicious patterns (could be legitimate)
            severity = Severity.MEDIUM if self.strict_mode else Severity.LOW
            violation = Violation(
                violation_type=ViolationType.MALICIOUS_CODE,
                severity=severity,
                content=content,
                reason=f"Suspicious pattern detected: {suspicious_match.group()}",
                context={"match": suspicious_match.group(), "type": content_type.value}
            )
            self._record_violation(violation)

            # Only block in strict mode
            if self.strict_mode:
                return CheckResult(safe=False, violation=violation, content=content)

        # Additional checks based on content type
        if content_type == ContentType.FILE_OPERATION:
            file_violation = self._check_file_operation(content)
            if file_violation:
                self._record_violation(file_violation)
                return CheckResult(safe=False, violation=file_violation, content=content)

        return CheckResult(safe=True, content=content)

    def check_output(
        self,
        content: str,
        content_type: ContentType = ContentType.AGENT_OUTPUT
    ) -> 'CheckResult':
        """
        Check output content for safety violations.

        Args:
            content: Content to check
            content_type: Type of content

        Returns:
            CheckResult with safety status
        """
        if not self.enabled:
            return CheckResult(safe=True, content=content)

        # Check for harmful content in output (more strict)
        harmful_match = self._harmful_regex.search(content)
        if harmful_match:
            violation = Violation(
                violation_type=ViolationType.HARMFUL_CONTENT,
                severity=Severity.CRITICAL,
                content=content,
                reason=f"Agent produced harmful content: {harmful_match.group()}",
                context={"match": harmful_match.group(), "type": content_type.value}
            )
            self._record_violation(violation)

            # Trigger kill switch for harmful output
            from .kill_switch import get_kill_switch
            ks = get_kill_switch()
            ks.trigger(
                KillSwitchReason.SAFETY_VIOLATION,
                f"Agent produced harmful content: {harmful_match.group()}",
                source="constitutional_classifier"
            )

            return CheckResult(safe=False, violation=violation, content=content)

        # Check if output contains instructions to bypass safety
        bypass_match = self._jailbreak_regex.search(content)
        if bypass_match:
            violation = Violation(
                violation_type=ViolationType.BYPASS_ATTEMPT,
                severity=Severity.HIGH,
                content=content,
                reason=f"Agent output contains bypass instructions: {bypass_match.group()}",
                context={"match": bypass_match.group(), "type": content_type.value}
            )
            self._record_violation(violation)
            return CheckResult(safe=False, violation=violation, content=content)

        return CheckResult(safe=True, content=content)

    def _check_file_operation(self, content: str) -> Optional[Violation]:
        """Check if file operation is safe"""
        # Dangerous paths
        dangerous_paths = [
            '/etc/passwd', '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM',
            '~/.ssh', '~/.aws',
        ]

        content_lower = content.lower()
        for path in dangerous_paths:
            if path.lower() in content_lower:
                return Violation(
                    violation_type=ViolationType.UNAUTHORIZED_ACCESS,
                    severity=Severity.HIGH,
                    content=content,
                    reason=f"Attempted access to sensitive file: {path}",
                    context={"path": path}
                )

        return None

    def _record_violation(self, violation: Violation):
        """Record a violation in history"""
        with self._lock:
            self.violation_history.append(violation)

            # Keep only last 1000 violations
            if len(self.violation_history) > 1000:
                self.violation_history = self.violation_history[-1000:]

            # Save state periodically
            if len(self.violation_history) % 100 == 0:
                self._save_state()

        # Log based on severity
        if violation.severity in [Severity.HIGH, Severity.CRITICAL]:
            logger.critical(
                f"SAFETY VIOLATION: {violation.violation_type.value} - "
                f"{violation.reason}"
            )
        elif violation.severity == Severity.MEDIUM:
            logger.warning(
                f"Safety violation: {violation.violation_type.value} - "
                f"{violation.reason}"
            )
        else:
            logger.info(
                f"Minor safety issue: {violation.violation_type.value} - "
                f"{violation.reason}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics"""
        with self._lock:
            # Count by type
            by_type = {}
            by_severity = {}
            for v in self.violation_history:
                by_type[v.violation_type.value] = by_type.get(v.violation_type.value, 0) + 1
                by_severity[v.severity.value] = by_severity.get(v.severity.value, 0) + 1

            return {
                "enabled": self.enabled,
                "strict_mode": self.strict_mode,
                "total_violations": len(self.violation_history),
                "violations_by_type": by_type,
                "violations_by_severity": by_severity,
            }

    def _save_state(self):
        """Save classifier state to file"""
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            state_data = {
                "enabled": self.enabled,
                "strict_mode": self.strict_mode,
                "violation_count": len(self.violation_history),
                "last_updated": datetime.now().isoformat(),
            }
            with open(self._state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save classifier state: {e}")

    def clear_history(self):
        """Clear violation history"""
        with self._lock:
            self.violation_history.clear()
            logger.info("Cleared violation history")


class CheckResult:
    """Result of a safety check"""

    def __init__(
        self,
        safe: bool,
        content: str,
        violation: Optional[Violation] = None
    ):
        self.safe = safe
        self.content = content
        self.violation = violation

    @property
    def blocked(self) -> bool:
        """Whether content was blocked"""
        return not self.safe

    @property
    def should_trigger_kill_switch(self) -> bool:
        """Whether violation should trigger kill switch"""
        return (
            self.violation is not None and
            self.violation.severity in [Severity.HIGH, Severity.CRITICAL]
        )

    @property
    def should_enter_safe_mode(self) -> bool:
        """Whether violation should enter safe mode"""
        return (
            self.violation is not None and
            self.violation.severity == Severity.MEDIUM
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "safe": self.safe,
            "blocked": self.blocked,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "violation": self.violation.to_dict() if self.violation else None,
            "should_trigger_kill_switch": self.should_trigger_kill_switch,
            "should_enter_safe_mode": self.should_enter_safe_mode,
        }


# Global singleton
_classifier: Optional[ConstitutionalClassifier] = None
_classifier_lock = threading.Lock()


def get_classifier() -> ConstitutionalClassifier:
    """
    Get the global constitutional classifier instance.

    Returns:
        The global ConstitutionalClassifier singleton

    Example:
        ```python
        classifier = get_classifier()
        result = classifier.check_input("user input")
        ```
    """
    global _classifier
    if _classifier is None:
        with _classifier_lock:
            if _classifier is None:
                _classifier = ConstitutionalClassifier()
    return _classifier


# Decorator for input checking
def check_user_input(func):
    """
    Decorator that checks function arguments for safety.

    Example:
        ```python
        @check_user_input
        def process_request(user_input: str):
            # user_input will be checked automatically
            pass
        ```
    """
    def wrapper(*args, **kwargs):
        classifier = get_classifier()

        # Check string arguments
        for i, arg in enumerate(args):
            if isinstance(arg, str):
                result = classifier.check_input(arg, ContentType.USER_INPUT)
                if not result.safe:
                    raise RuntimeError(
                        f"Input blocked by safety check: {result.violation.reason}"
                    )

        return func(*args, **kwargs)
    return wrapper


# Decorator for output checking
def check_agent_output(func):
    """
    Decorator that checks function output for safety.

    Example:
        ```python
        @check_agent_output
        def generate_response(prompt: str) -> str:
            # Output will be checked automatically
            return "some response"
        ```
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # Check string output
        if isinstance(result, str):
            classifier = get_classifier()
            check_result = classifier.check_output(result, ContentType.AGENT_OUTPUT)
            if not check_result.safe:
                raise RuntimeError(
                    f"Output blocked by safety check: {check_result.violation.reason}"
                )

        return result
    return wrapper


# Import for type annotations
from .kill_switch import KillSwitchReason
