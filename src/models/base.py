"""
Base models for common data structures
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any
import json


class OperationStatus(str, Enum):
    """Standard operation status"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


@dataclass
class BaseResponse:
    """Base response model for all operations"""
    status: OperationStatus
    message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        # Convert enum to string
        result["status"] = self.status.value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @property
    def is_success(self) -> bool:
        """Check if operation was successful"""
        return self.status == OperationStatus.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        """Check if operation failed"""
        return self.status == OperationStatus.FAILED


@dataclass
class BaseRequest:
    """Base request model"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) 