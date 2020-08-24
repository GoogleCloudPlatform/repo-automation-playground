# Copyright 2020 Google LLC. All Rights Reserved.
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


import ast
import constants
import os

from source_parsers import direct_invocation, webapp2_router, flask_router


def get_top_level_methods(source_path):
    def __get_method_children(expr):
        results = []

        if hasattr(expr, 'id'):
            results.append(expr.id)  # Base case

        if hasattr(expr, 'body') and isinstance(expr.body, list):
            for sub_expr in expr.body:
                results += __get_method_children(sub_expr)

        if hasattr(expr, 'value'):
            results += __get_method_children(expr.value)

        if hasattr(expr, 'func'):
            results += __get_method_children(expr.func)
            for a in expr.args:
                results += __get_method_children(a)

        return results

    with open(source_path, 'r') as f:
        content = "".join(f.readlines())
        nodes = ast.iter_child_nodes(ast.parse(content))
        nodes = [x for x in nodes]

        class_name = os.path.splitext(os.path.basename(source_path))[0]

        methods = []

        methods += webapp2_router.parse(nodes)
        methods += flask_router.parse(nodes, class_name)

        # run direct_invocation parser after flask_router to avoid duplicates
        methods += direct_invocation.parse(nodes, class_name)

        for method in methods:
            method.drift['source_path'] = source_path
            method.drift['children'] = __get_method_children(method)

            # Initialize array values
            method.drift['region_tags'] = []
            method.drift['test_methods'] = []

        return methods


# This method should be called once all other parsing is complete
def add_children_drift_data(source_methods):

    def __recursor__(method):
        for child in method.drift['children']:
            child_methods = [x for x in source_methods if 'name' in x.drift]
            child_methods = [x for x in child_methods
                             if child == x.drift['name']]

            # prevent infinite loops
            child_methods = [x for x in child_methods
                             if x.drift['name'] != method.drift['name']]

            if child_methods:
                child_method = child_methods[0]
                __recursor__(child_method)

                child_drift = child_method.drift
                method.drift['region_tags'] += child_drift['region_tags']
                method.drift['test_methods'] += child_drift['test_methods']

        method.drift['region_tags'] = list(set(method.drift['region_tags']))
        method.drift['test_methods'] = list(set(method.drift['test_methods']))

    for method in source_methods:
        __recursor__(method)


def get_region_tag_regions(source_path):
    def __extract_region_tag__(t):
        tag = t[1].split(" ")[-1]
        tag = tag.split(']')[0]
        return (t[0] + 1, tag)  # +1 = convert to 1-indexed

    with open(source_path, 'r') as file:
        content_lines = [(idx, ln) for idx, ln in enumerate(file.readlines())]

        start_tag_lines = [t for t in content_lines if "# [START" in t[1]]
        end_tag_lines = [t for t in content_lines if "# [END" in t[1]]

        # region tags can be repeated, so we can't use them as dict keys
        # for specific region blocks - so we use tuple arrays instead
        start_tags = [__extract_region_tag__(t) for t in start_tag_lines]
        end_tags = [__extract_region_tag__(t) for t in end_tag_lines]

        unique_tag_names = list(set([x[1] for x in start_tags]))

        # ignore "useless" region tags
        unique_tag_names = [x for x in unique_tag_names if
                            x not in constants.IGNORED_REGION_TAGS]

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

        return regions_and_tags


def add_region_tags_to_methods(methods, region_tags):
    def __overlaps__(method, tag):
        m_end_stmt = method
        not_at_end = True
        while not_at_end:
            if hasattr(m_end_stmt, 'body'):
                m_end_stmt = m_end_stmt.body[-1]
            elif hasattr(m_end_stmt, 'exc'):
                m_end_stmt = m_end_stmt.exc
            elif hasattr(m_end_stmt, 'args'):
                m_end_stmt = m_end_stmt.args[-1]
            else:
                not_at_end = False

        m_start = method.lineno
        m_end = m_end_stmt.lineno

        (_, r_start, r_end) = tag

        # add a fudge factor for region-tag boundary checks
        # (useful for multi-line statements)
        c = min(m_end - m_start + 1, constants.TAG_LINE_RANGE)

        return (r_start <= m_start + c and m_end <= r_end + c) \
            or (m_start <= r_start + c and r_end <= m_end + c)

    for method in methods:
        matching_tags = [t for t in region_tags if __overlaps__(method, t)]

        method.drift['region_tags'] = list(set([x[0] for x in matching_tags]))
