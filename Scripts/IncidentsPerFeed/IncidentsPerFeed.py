from typing import List, Dict, Union

FEED = "feed"
ACTIVE = "active"
FROM_DATE = demisto.args().get('from', '30 days ago')


def get_incidents_count_by_feed(feed, query=None) -> int:
    """Counts the incidents amount that fits the query and has indicators that came from the given feed.
        Args:
                feed: Feed from which the incidents indicator should be from
                query: Additional filters for the 'getIncidents' command
        @return:
            total amount of incidents returned.
    """
    query_string = f'indicator.sourceBrands:{feed}'
    if query:
        query_string += f' and {query}'
    res = demisto.executeCommand("getIncidents", {"query": query_string, "fromdate": FROM_DATE})
    severe_incidents_count = res[0]["Contents"]["total"]
    return severe_incidents_count


def get_feeds() -> set:
    """￿Return all enabled modules
            @return:
                A set with feed names
    """
    modules = demisto.getModules()
    return {module_details["brand"] for instance_name, module_details in modules.items() if active_feed(module_details)}


def active_feed(module) -> bool:
    """Checks if module is active and if it's a feed and return a boolean accordingly
            Args:
                    module: Module to check if is active feed
            @return:
                True if the module's brand has 'feed' in it and if module 'state is 'active' else False
    """
    return FEED in module["brand"].lower() and module["state"] == ACTIVE


def main():
    feed_types = get_feeds()
    distinct_incidents_query = demisto.args().get("query")
    distinct_incidents = demisto.args().get("incidents_distinction_name")
    groups = generate_groups(feed_types, distinct_incidents_query, distinct_incidents)
    human_readable = tableToMarkdown('Incidents count by feed', groups)
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': groups,
        'ContentsFormat': formats['text'],
        'ReadableContentsFormat': formats['markdown'],
        'HumanReadable': human_readable
    })


def generate_groups(feed_types,
                    distinct_incidents_query=None,
                    distinction_name=None) -> List[Dict[str, Union[List[Dict[str, Union[str, List[int]]]], str]]]:
    """If distinct_incidents_query is given- return the amount of incidents that match the query and the amount of
    the remaining incidents that has indicators from those feeds.
    If distinct_incidents_query is not given- will only return the amount
        Args:
               feed_types :A dict Containing feed names
               distinct_incidents_query: A string with additional incidents query
               distinct_incidents_name: A string with the distinction name to display in the widget
        @return:
            Chart widget require list of 'group' as response
       where group has "name": string, "data" [int], "groups": [group]
        """
    data = {}
    for feed in feed_types:
        incidents_count_by_feed = get_incidents_count_by_feed(feed)
        distinct_incidents_count = get_incidents_count_by_feed(feed,
                                                               distinct_incidents_query) if distinct_incidents_query else 0
        data[feed] = [{"name": "Incidents", "data": [incidents_count_by_feed - distinct_incidents_count]}]
        if distinction_name:
            data[feed].append({"name": distinction_name, "data": [distinct_incidents_count]})

    groups = []
    for key, value in data.items():
        groups.append({"name": key,
                       "groups": value
                       })
    return groups


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
