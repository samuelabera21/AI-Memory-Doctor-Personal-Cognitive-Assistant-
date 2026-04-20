from app.services.temporal_service import parse_query_time_filters


def extract_time_context(query: str):
    filters = parse_query_time_filters(query)
    result = {}

    if filters.get("start_date") and filters.get("start_date") == filters.get("end_date"):
        result["date"] = filters["start_date"]
    else:
        result["start_date"] = filters.get("start_date")
        result["end_date"] = filters.get("end_date")

    if filters.get("start_time"):
        result["start_time"] = filters["start_time"]
        result["end_time"] = filters["end_time"]

    return {k: v for k, v in result.items() if v is not None}