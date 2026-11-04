from typing import Any, Optional
from fastapi import HTTPException, status

class AppException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details

class InvalidFilenameError(AppException):
    def __init__(self, filename: str):
        super().__init__(
            f"Filename '{filename}' is not a valid 6-digit 'yymmdd' format.",
            code="INVALID_FILENAME",
            details={"filename": filename}
        )

class InvalidDateError(AppException):
    def __init__(self, date_str: str, reason: str = "Invalid calendar date"):
        super().__init__(
            f"Date '{date_str}' is invalid: {reason}.",
            code="INVALID_DATE",
            details={"date": date_str, "reason": reason}
        )

class DateOutOfRangeError(AppException):
    def __init__(self, date_str: str, reason: str):
        super().__init__(
            f"Date '{date_str}' is out of valid range: {reason}.",
            code="DATE_OUT_OF_RANGE",
            details={"date": date_str, "reason": reason}
        )

class DateConflictError(AppException):
    def __init__(self, date_str: str, existing_id: int, new_path: str):
        super().__init__(
            f"Date conflict: '{date_str}' already has an active photo (ID: {existing_id}).",
            code="DATE_CONFLICT",
            details={"date": date_str, "existing_id": existing_id, "new_path": new_path}
        )

class PathTraversalError(AppException):
    def __init__(self, path: str):
        super().__init__(
            f"Path traversal detected or access outside permitted root: '{path}'.",
            code="ACCESS_DENIED",
            details={"path": path}
        )

class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            f"{resource} '{identifier}' not found.",
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )
