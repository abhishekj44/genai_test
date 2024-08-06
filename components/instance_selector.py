from datetime import datetime, timedelta
import json
from typing import List, Tuple
from components import INSTANCE_SELECTOR_KEY
from src.messages import Instance
import streamlit as st

from src.util import cache_resource


def _instance_name_format_func(instance: Instance) -> str:
    dt = ""
    if instance.creation_datetime:
        dt = instance.creation_datetime.strftime("%Y-%m-%d %H:%M:%S")
    shared_explainer = " (SHARED)" if instance.shared else ""
    return dt + " " + instance.name + shared_explainer


def _get_range_for_date_filter(instances: List[Instance]) -> Tuple[datetime, datetime]:
    """
    Gets earliest and latest time of instance creations.
    """
    instance_creation_times = [
        i.creation_datetime for i in instances if i.creation_datetime is not None
    ]
    assert instance_creation_times, f"No chat instances with creation datetimes"
    start = min(instance_creation_times) - timedelta(days=1)
    end = max(instance_creation_times) + timedelta(days=1)
    return start, end


def _filter_instances_within_range(
    instances: List[Instance], min_date_filter: datetime, max_date_filter: datetime
) -> List[Instance]:
    """
    Filters instances that creation time sits between min and max time.
    """
    return [
        i
        for i in instances
        if i.creation_datetime is not None
        and i.creation_datetime.date() >= min_date_filter.date()
        and i.creation_datetime.date() <= max_date_filter.date()
    ]


def _filter_instances_by_date_range(instances: List[Instance]) -> List[Instance]:
    """
    Filter historical chat instances by creation date time
    """
    if instances:
        start, end = _get_range_for_date_filter(instances)
        min_date_filter, max_date_filter = st.slider(
            "Select a date range",
            min_value=start,
            max_value=end,
            value=(start, end),
            step=timedelta(days=1),
        )
        instances = _filter_instances_within_range(
            instances, min_date_filter=min_date_filter, max_date_filter=max_date_filter
        )

    return instances


def _filter_instances_by_key_words(
    instances: List[Instance], filter_text: str
) -> List[Instance]:
    """
    Filter chat instances by key words in their
    """

    filtered_instances = set()
    if filter_text != "":
        key_words = set(filter_text.split())
        for key_word in key_words:
            for inst in instances:
                stripped_key_word = key_word.strip().lower()
                stripped_content = (
                    "".join([m.content for m in inst.messages]).strip().lower()
                )
                if (
                    stripped_key_word in inst.name.lower()
                    or key_word.strip().lower() in stripped_content
                ):
                    filtered_instances.add(inst)

    return list(filtered_instances)


def _get_instance_index(all_instance_options: List[Instance], current_instance_id: int):
    # Handle case where search changes where current instance is no longer there
    index_search = [
        i for i, ins in enumerate(all_instance_options) if current_instance_id == ins.id
    ]
    if index_search:
        return index_search[0]
    else:
        # Default to create new chat
        return 0


def instance_selector(
    default_instances: List[Instance],
    historical_instances: List[Instance],
    current_instance: int,
):
    """
    Streamlit element to control filtering and selection of chat instances.
    """
    st.header("Select Chat")
    with st.expander("Filter"):
        # Date sorting
        descending = st.toggle("Sort newest -> oldest", value=True)
        historical_instances = sorted(
            historical_instances, key=lambda x: x.creation_datetime, reverse=descending
        )

        # Date filter
        historical_instances = _filter_instances_by_date_range(historical_instances)
        # Key word filter
        filter_name = st.text_input("Search")
        if filter_name != "":
            historical_instances = _filter_instances_by_key_words(
                historical_instances, filter_name
            )
    all_options = default_instances + historical_instances

    height = 400 if len(all_options) > 6 else None

    index = _get_instance_index(
        all_instance_options=all_options, current_instance_id=current_instance
    )

    with st.container(height=height, border=True):
        selected_instance = st.radio(
            "Instance",
            all_options,
            index=index,
            format_func=_instance_name_format_func,
            label_visibility="collapsed",
            key=INSTANCE_SELECTOR_KEY,
        )
        return selected_instance
