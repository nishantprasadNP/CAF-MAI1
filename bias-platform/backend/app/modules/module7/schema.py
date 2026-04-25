from pydantic import BaseModel


class ProbabilitiesRequest(BaseModel):
    probabilities: list[float]


class ContextSchema:
    FIXED_FIELDS = ["region", "hospital_type", "resource_level", "time_of_day"]

    @staticmethod
    def validate(context: dict) -> dict:
        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")

        validated = {}
        missing = [field for field in ContextSchema.FIXED_FIELDS if field not in context]
        if missing:
            raise ValueError(f"Missing context fields: {missing}")
        for field in ContextSchema.FIXED_FIELDS:
            value = context[field]
            if not isinstance(value, (str, int, float)):
                raise ValueError(f"{field} must be string/int/float")
            validated[field] = value
        return validated
