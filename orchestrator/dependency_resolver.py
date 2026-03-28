from collections import deque


class DependencyResolverError(Exception):
    pass


def topological_sort(pipelines):
    graph = {pipeline["pipeline_name"]: [] for pipeline in pipelines}
    indegree = {pipeline["pipeline_name"]: 0 for pipeline in pipelines}
    pipeline_map = {pipeline["pipeline_name"]: pipeline for pipeline in pipelines}

    for pipeline in pipelines:
        pipeline_name = pipeline["pipeline_name"]
        for dependency_name in pipeline.get("dependencies") or []:
            if dependency_name not in pipeline_map:
                raise DependencyResolverError(
                    f"Pipeline '{pipeline_name}' depends on missing pipeline '{dependency_name}'"
                )
            graph[dependency_name].append(pipeline_name)
            indegree[pipeline_name] += 1

    queue = deque(name for name, count in indegree.items() if count == 0)
    ordered_names = []

    while queue:
        current = queue.popleft()
        ordered_names.append(current)
        for child in graph[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    if len(ordered_names) != len(pipelines):
        raise DependencyResolverError("Cycle detected in dependency graph")

    return [pipeline_map[name] for name in ordered_names]
