from typing import Dict, Any
from pydantic import BaseModel, Field

class MessageTemplate(BaseModel):
    template: str = Field(..., description="The message template with placeholders")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of variables to fill in the template")
    highlight_fields: list[str] = Field(default_factory=list, description="List of fields to be highlighted in the UI")
    
    def generate_message(self) -> str:
        """Generate a message by filling the template with provided variables"""
        try:
            return self.template.format(**self.variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
        except Exception as e:
            raise ValueError(f"Error generating message: {e}")

    def get_highlight_fields(self) -> list[str]:
        """Get the list of fields that should be highlighted in the UI"""
        return self.highlight_fields

# Example usage:
# template = MessageTemplate(
#     template="Vehicle {id} {status_desc} at coordinates ({lat}, {lon}). "
#             "It's traveling at {speed} km/h with {battery}% battery remaining.",
#     variables={
#         "id": "V1",
#         "status_desc": "is currently in motion",
#         "lat": 40.7128,
#         "lon": -74.0060,
#         "speed": 65.5,
#         "battery": 80.0
#     }
# )
# message = template.generate_message() 