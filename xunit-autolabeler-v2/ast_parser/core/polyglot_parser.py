from .constants import IGNORED_REGION_TAGS, TAG_LINE_RANGE


# This method should be called once all other parsing is complete
def add_children_drift_data(source_methods):

    def __recursor__(method):
        for child in method['children']:
            child_methods = [x for x in source_methods if 'name' in x]
            child_methods = [x for x in child_methods
                             if child == x['name']]

            # prevent infinite loops
            child_methods = [x for x in child_methods
                             if x['name'] != method['name']]

            if child_methods:
                child_method = child_methods[0]
                __recursor__(child_method)

                method['region_tags'].extend(child_method['region_tags'])
                method['test_methods'].extend(child_method['test_methods'])

        method['region_tags'] = list(set(method['region_tags']))
        method['test_methods'] = list(set(method['test_methods']))

    for method in source_methods:
        __recursor__(method)


def get_region_tag_regions(source_path):
    def __extract_region_tag__(t):
        tag = t[1].split(" ")[-1]
        tag = tag.split(']')[0]
        return (t[0] + 1, tag)  # +1 = convert to 1-indexed

    with open(source_path, 'r') as file:
        content_lines = [(idx, ln) for idx, ln in enumerate(file.readlines())]

        start_tag_lines = [t for t in content_lines if " [START" in t[1]]
        end_tag_lines = [t for t in content_lines if " [END" in t[1]]

        # region tags can be repeated, so we can't use them as dict keys
        # for specific region blocks - so we use tuple arrays instead
        start_tags = [__extract_region_tag__(t) for t in start_tag_lines]
        end_tags = [__extract_region_tag__(t) for t in end_tag_lines]

        unique_tag_names = list(set([x[1] for x in start_tags]))

        # ignore "useless" region tags
        ignored_tag_names = [x for x in unique_tag_names if
                             x in IGNORED_REGION_TAGS]
        unique_tag_names = [x for x in unique_tag_names if
                            x not in ignored_tag_names]

        if len(start_tags) != len(end_tags):
            raise ValueError("Mismatched region tags: " + source_path)

        start_tags.sort()
        end_tags.sort()

        regions_and_tags = []
        for tag in unique_tag_names:
            matching_starts = [x for x in start_tags if x[1] == tag]
            matching_ends = [x for x in end_tags if x[1] == tag]

            if len(matching_starts) != len(matching_ends):
                raise ValueError(
                    f"Mismatched region tag [{tag}] in {source_path}")

            for i in range(len(matching_starts)):
                t = matching_starts[i]
                regions_and_tags.append((t[1], t[0], matching_ends[i][0]))

        return (regions_and_tags, ignored_tag_names)


def add_region_tags_to_methods(methods, region_tags):
    def __overlaps__(method, tag):
        (_, r_start, r_end) = tag

        m_start = method['start_line']
        m_end = method['end_line']

        # add a fudge factor for region-tag boundary checks
        # (useful for multi-line statements)
        c = min(m_end - m_start + 1, TAG_LINE_RANGE)

        return (r_start <= m_start + c and m_end <= r_end + c) \
            or (m_start <= r_start + c and r_end <= m_end + c)

    for method in methods:
        matching_tags = [t for t in region_tags if __overlaps__(method, t)]

        method['region_tags'] = list(set([x[0] for x in matching_tags]))
