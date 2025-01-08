def build_hierarchy(folders, parent=None, level=0):
    hierarchy = []
    for folder in folders:
        if folder.parent == parent:
            hierarchy.append((folder, level))
            hierarchy.extend(build_hierarchy(folders, folder, level + 1))
    return hierarchy
