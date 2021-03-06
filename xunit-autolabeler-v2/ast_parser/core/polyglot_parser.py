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

from typing import List, Tuple

from . import constants
from . import polyglot_drift_data as pdd


def add_children_drift_data(
    source_methods: List[pdd.PolyglotDriftData]
) -> None:
    """Add DRIFT data of a method's 'children' to its DRIFT data object

    This function "merges" a snippet method's children (i.e. other methods
    the snippet calls) with their top-level "root" ancestors. Since some
    snippets are invoked by *other* snippets, capturing these relationships
    is helpful when determining snippet test coverage.

    Args:
        source_methods: a list of snippet methods; these
                        methods are then modified 'in-place'

    Note:
        This method should be called once all other parsing is complete
    """
    recursed_nodes = set()

    def _recursor(method: pdd.PolyglotDriftData) -> None:
        """Recursively traverses through a snippet method's child methods

        Args:
            method: Python expression to recurse over

        Returns:
            An updated PolyglotDriftData object
        """

        # Prevent infinite loops
        method_key = (method.name, method.class_name, method.source_path)
        if method_key in recursed_nodes:
            return
        recursed_nodes.add(method_key)

        for child in method.children:
            child_methods = [
                child_method for child_method in source_methods if
                child == child_method.name and
                method.source_path == child_method.source_path
            ]

            if child_methods:
                child_method = child_methods[0]
                _recursor(child_method)

                method.region_tags.extend(child_method.region_tags)
                method.test_methods.extend(child_method.test_methods)

        method.region_tags = list(set(method.region_tags))
        method.test_methods = list(set(method.test_methods))

    """
    EDGE CASE:
        Some snippets (e.g. Python talent solution API) are wrapped in a
        separate "snippet invocation method" (e.g. "run_sample"), that itself
        is invoked within the tests.

    SOLUTION:
        Move snippet-invocation method tests to their invoked [child] methods
        (This *cannot* be done with the child-labeling system, as that looks
         for tests in the child methods - *not* the parent ones!)
    """
    for method in source_methods:
        if method.name not in constants.SNIPPET_INVOCATION_METHODS:
            continue

        for child_name in method.children:
            child_methods = [
                child_method for child_method in source_methods
                if child_method.name == child_name and
                method.source_path == child_method.source_path
            ]

            if child_methods:
                child_methods[0].test_methods.extend(method.test_methods)

        # Remove direct children of snippet invocation methods
        # (Since the invocation method's test data was propagated to them)
        method.children = []
        method.test_methods = []

    for method in source_methods:
        _recursor(method)


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
    def _get_region_tag_from_line(line: Tuple[int, str]) -> Tuple[int, str]:
        """Extract line numbers and region tags
           from a given (line number, text) 2-tuple.

        Args:
            line: a 2-tuple of the form (1-indexed line number, line text)

        Returns:
            a 2-tuple of the form (0-indexed line number, region tag)
        """
        line_num: int = line[0]
        line_text: str = line[1]

        tag = constants.REGION_TAG_ONLY_REGEX.search(line_text).group(0)

        return (line_num + 1, tag)  # +1 = convert to 0-indexed

    with open(source_path, 'r') as file:
        file_lines = file.readlines()

        # Remove _EXCLUDE tags
        file_lines = [line for line in file_lines
                      if '[START_EXCLUDE' not in line
                      and '[END_EXCLUDE' not in line]

        content_lines = [(idx, line_text) for idx, line_text in
                         enumerate(file_lines)]

        start_tag_lines = [line_tuple for line_tuple in content_lines
                           if ' [START' in line_tuple[1]]
        end_tag_lines = [line_tuple for line_tuple in content_lines
                         if ' [END' in line_tuple[1]]

        # region tags can be repeated, so we can't use them as dict keys
        # for specific region blocks - so we use tuple arrays instead
        start_regions = [_get_region_tag_from_line(line_tuple)
                         for line_tuple in start_tag_lines]
        end_regions = [_get_region_tag_from_line(line_tuple)
                       for line_tuple in end_tag_lines]

        unique_tag_names = \
            list(set([region_tag for _, region_tag in start_regions]))

        # ignore "useless" region tags
        ignored_tag_names = [tag for tag in unique_tag_names if
                             tag in constants.IGNORED_REGION_TAGS]
        unique_tag_names = [tag for tag in unique_tag_names if
                            tag not in ignored_tag_names]

        if len(start_regions) != len(end_regions):
            raise ValueError('Mismatched region tags: ' + source_path)

        start_regions.sort()
        end_regions.sort()

        regions_and_tags = []
        for tag in unique_tag_names:
            matching_starts = [(line_num, line_tag) for line_num, line_tag
                               in start_regions if line_tag == tag]
            matching_ends = [(line_num, line_tag) for line_num, line_tag
                             in end_regions if line_tag == tag]

            if len(matching_starts) != len(matching_ends):
                raise ValueError(
                    f'Mismatched region tag [{tag}] in {source_path}')

            # Create regions_and_tags list
            matching_tags = [region[1] for region in matching_starts]
            matching_start_linenos = [region[0] for region in matching_starts]
            matching_end_linenos = [region[0] for region in matching_ends]

            matching_regions_and_tags = list(zip(
                matching_tags, matching_start_linenos, matching_end_linenos))
            regions_and_tags += matching_regions_and_tags

        return (regions_and_tags, ignored_tag_names)


def add_region_tags_to_method(
    method: pdd.PolyglotDriftData,
    regions_and_tags: List[Tuple[str, int, int]]
) -> pdd.PolyglotDriftData:
    """Matches + adds appropriate region tags to a method's DRIFT data

    Args:
        method: a method to add region tag data to
        region_tags: a list of regions and tags, encoded as tuples
                     of the form (region tag, start line, end line)

    Returns:
        Updated method
    """
    def _overlaps(
        method: pdd.PolyglotDriftData,
        region_and_tag: Tuple[str, int, int]
    ) -> bool:
        """Helper function to determine if a method and a given region overlap

        Args:
            method: language-agnostic DRIFT data for a snippet method
            region: language-agnostic representation of a region and its tag

        Returns:
            True if the specified method and region overlap, False otherwise
        """
        _, tag_start, tag_end = region_and_tag

        method_start = method.start_line
        method_end = method.end_line

        # add a fudge factor for region-tag boundary checks
        # (useful for multi-line statements)
        tolerance = min(
            method_end - method_start + 1,
            constants.TAG_LINE_RANGE
        )

        if tag_start <= method_start + tolerance and \
           method_end <= tag_end + tolerance:
            # region tag encloses method
            return True
        if method_start <= tag_start + tolerance and \
           tag_end <= method_end + tolerance:
            # method encloses region tag
            return True

        return False

    matching_regions = [region for region in regions_and_tags
                        if _overlaps(method, region)]

    new_region_tags = list(set([
        region[0] for region in matching_regions
    ]))

    return method._replace(region_tags=new_region_tags)
