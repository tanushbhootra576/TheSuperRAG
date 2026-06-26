from typing import Dict, Any
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, DatetimeRange, IsEmptyCondition

class FilterBuilder:
    @staticmethod
    def build(filters_dict: Dict[str, Any]) -> Filter:
        if not filters_dict:
            return None
            
        must_conditions = []
        
        if "doc_ids" in filters_dict and filters_dict["doc_ids"]:
            doc_ids = filters_dict["doc_ids"]
            if isinstance(doc_ids, list):
                must_conditions.append(FieldCondition(key="metadata.source_file", match=MatchAny(any=doc_ids)))
            else:
                must_conditions.append(FieldCondition(key="metadata.source_file", match=MatchValue(value=doc_ids)))

        if "source_type" in filters_dict and filters_dict["source_type"]:
            source_types = filters_dict["source_type"]
            if isinstance(source_types, list):
                must_conditions.append(FieldCondition(key="metadata.file_type", match=MatchAny(any=source_types)))
            else:
                must_conditions.append(FieldCondition(key="metadata.file_type", match=MatchValue(value=source_types)))

        if "tags" in filters_dict and filters_dict["tags"]:
            tags = filters_dict["tags"]
            if isinstance(tags, list):
                must_conditions.append(FieldCondition(key="metadata.tags", match=MatchAny(any=tags)))
            else:
                must_conditions.append(FieldCondition(key="metadata.tags", match=MatchValue(value=tags)))

        if "author" in filters_dict and filters_dict["author"]:
            must_conditions.append(FieldCondition(key="metadata.author", match=MatchValue(value=filters_dict["author"])))

        if "date_range" in filters_dict and isinstance(filters_dict["date_range"], dict):
            date_range = filters_dict["date_range"]
            dt_range = {}
            if "from" in date_range:
                from_date = date_range["from"]
                if len(from_date) == 10:
                    from_date += "T00:00:00Z"
                dt_range["gte"] = from_date
            if "to" in date_range:
                to_date = date_range["to"]
                if len(to_date) == 10:
                    to_date += "T23:59:59Z"
                dt_range["lte"] = to_date
                
            if dt_range:
                must_conditions.append(FieldCondition(key="metadata.created_at", datetime_range=DatetimeRange(**dt_range)))

        if "session_id" in filters_dict and filters_dict["session_id"]:
            session_id = filters_dict["session_id"]
            must_conditions.append(
                Filter(
                    should=[
                        FieldCondition(key="metadata.session_id", match=MatchValue(value=session_id)),
                        IsEmptyCondition(key="metadata.session_id")
                    ]
                )
            )
        else:
            must_conditions.append(IsEmptyCondition(key="metadata.session_id"))

        if not must_conditions:
            return None
            
        return Filter(must=must_conditions)
