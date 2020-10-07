# Copyright 2020 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import Any, Dict, List, Tuple

from .constants import IGNORED_REGION_TAGS, TAG_LINE_RANGE


def add_children_drift_data(source_methods: List) -> None:
    """Add DRIFT data of a method's 'children' to its DRIFT data object

    This function "merges" a snippet method's children (i.e. other methods
    the snippet calls) with their top-level "root" ancestors. Since some
    snippets are invoked by *other* snippets, capturing these relationships
    is helpful when determining snippet test coverage.

    Args:
        source_methods (List[ast.AST]): a list of snippet methods; these
                                        methods are then modified 'in-place'

    Note:
        This method should be called once all other parsing is complete
    """

    def __recursor__(method: Any) -> None:
        """Recursively traverses through a snippet method's child methods

        Args:
            method (ast.AST): Python expression to recurse over
        """
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


def get_region_tag_regions(
    source_path: str
) -> Tuple[List[Tuple[str, int, int]], List[str]]:
    """Get the region tag data from a given file (of any language)

    Args:
        source_path: path to the target file

    Returns:
        A tuple of the form (regions_and_tags, ignored_tag_names), where:
          - regions_and_tags: a list of tuples of the form
                            (region tag value, start line, end line)
          - ignored_tag_names: a list of region tags (as strings) ignored
                               due to cross-parser constants
    """
    def _get_region_tag_from_line(line: str) -> Tuple[int, str]:
        """Extract line numbers and region tags
           from a given (line number, text) 2-tuple.

        Args:
            line: a 2-tuple of the form (1-indexed line number, line text)

        Returns:
            a 2-tuple of the form (0-indexed line number, region tag)
        """
        (line_num, line_text) = line

        tag = line_text.split(' ')[-1]
        tag = tag.split(']')[0]
        return (line_num + 1, tag)  # +1 = convert to 0-indexed

    with open(source_path, 'r') as file:
        content_lines = [(idx, ln) for idx, ln in enumerate(file.readlines())]

        start_tag_lines = [t for t in content_lines if ' [START' in t[1]]
        end_tag_lines = [t for t in content_lines if ' [END' in t[1]]

        # region tags can be repeated, so we can't use them as dict keys
        # for specific region blocks - so we use tuple arrays instead
        start_regions = [_get_region_tag_from_line(t) for t in start_tag_lines]
        end_regions = [_get_region_tag_from_line(t) for t in end_tag_lines]

        unique_tag_names = list(set([region[1] for region in start_regions]))

        # ignore "useless" region tags
        ignored_tag_names = [tag for tag in unique_tag_names if
                             tag in IGNORED_REGION_TAGS]
        unique_tag_names = [tag for tag in unique_tag_names if
                            tag not in ignored_tag_names]

        if len(start_regions) != len(end_regions):
            raise ValueError('Mismatched region tags: ' + source_path)

        start_regions.sort()
        end_regions.sort()

        regions_and_tags = []
        for tag in unique_tag_names:
            matching_starts = [region for region in start_regions
                               if region[1] == tag]
            matching_ends = [region for region in end_regions
                             if region[1] == tag]

            if len(matching_starts) != len(matching_ends):
                raise ValueError(
                    f'Mismatched region tag [{tag}] in {source_path}')

            for i in range(len(matching_starts)):
                start_region = matching_starts[i]
                regions_and_tags.append(
                    (start_region[1], start_region[0], matching_ends[i][0])
                )

        return (regions_and_tags, ignored_tag_names)


def add_region_tags_to_methods(
    methods: List[Any],
    regions_and_tags: List[Tuple[str, int, int]]
) -> None:
    """Matches + adds appropriate region tags to a method's DRIFT data

    Args:
        methods (List[ast.AST]): a list of methods to add region tag data to
        region_tags: a list of regions and tags, encoded as tuples
                     of the form (region tag, start line, end line)
    """
    def _overlaps(method: Dict, region_and_tag: Tuple[str, int, int]):
        """Helper function to determine if a method and a given region overlap

        Args:
            method: language-agnostic DRIFT data for a snippet method
            region: language-agnostic representation of a region and its tag

        Returns:
            True if the specified method and region overlap, False otherwise
        """
        (_, tag_start, tag_end) = region_and_tag

        method_start = method['start_line']
        method_end = method['end_line']

        # add a fudge factor for region-tag boundary checks
        # (useful for multi-line statements)
        tolerance = min(method_end - method_start + 1, TAG_LINE_RANGE)

        if tag_start <= method_start + tolerance and \
           method_end <= tag_end + tolerance:
            # region tag encloses method
            return True
        if method_start <= tag_start + tolerance and \
           tag_end <= method_end + tolerance:
            # method encloses region tag
            return True

        return False

    for method in methods:
        matching_regions = [region for region in regions_and_tags
                            if _overlaps(method, region)]

        method['region_tags'] = list(set([region[0] for region
                                          in matching_regions]))
