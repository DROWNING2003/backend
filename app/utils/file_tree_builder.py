"""
文件树构建工具
"""

import os
from typing import Dict, List, Optional
from app.schemas.level import FileTreeNode


def build_file_tree_from_files(files: Dict[str, str], base_uri: str = "file:///github") -> FileTreeNode:
    """
    从文件字典构建文件树结构
    
    Args:
        files: 文件字典，key为相对路径，value为文件内容
        base_uri: 基础URI前缀
        
    Returns:
        FileTreeNode: 根节点
    """
    # 创建根节点
    root = FileTreeNode(
        type="directory",
        uri=base_uri,
        children=[]
    )
    
    # 按路径排序，确保目录在文件前面
    sorted_paths = sorted(files.keys())
    
    # 构建树结构
    for file_path in sorted_paths:
        file_content = files[file_path]
        _add_file_to_tree(root, file_path, file_content, base_uri)
    
    return root


def _add_file_to_tree(root: FileTreeNode, file_path: str, file_content: str, base_uri: str):
    """
    将文件添加到树结构中
    
    Args:
        root: 根节点
        file_path: 文件相对路径
        file_content: 文件内容
        base_uri: 基础URI前缀
    """
    # 标准化路径分隔符
    file_path = file_path.replace('\\', '/')
    path_parts = file_path.split('/')
    
    current_node = root
    current_path = ""
    
    # 遍历路径的每一部分
    for i, part in enumerate(path_parts):
        if not part:  # 跳过空字符串
            continue
            
        current_path = current_path + "/" + part if current_path else part
        full_uri = f"{base_uri}/{current_path}"
        
        # 检查当前节点的子节点中是否已存在该路径
        existing_child = None
        if current_node.children:
            for child in current_node.children:
                if child.uri == full_uri:
                    existing_child = child
                    break
        
        if existing_child:
            # 如果已存在，继续使用该节点
            current_node = existing_child
        else:
            # 创建新节点
            is_file = (i == len(path_parts) - 1)  # 最后一个部分是文件
            
            new_node = FileTreeNode(
                type="file" if is_file else "directory",
                uri=full_uri,
                children=[] if not is_file else None,
                content=file_content if is_file else None
            )
            
            # 添加到父节点
            if current_node.children is None:
                current_node.children = []
            current_node.children.append(new_node)
            
            current_node = new_node


def sort_file_tree(node: FileTreeNode) -> FileTreeNode:
    """
    对文件树进行排序（目录在前，文件在后，同类型按名称排序）
    
    Args:
        node: 文件树节点
        
    Returns:
        FileTreeNode: 排序后的节点
    """
    if node.children:
        # 递归排序子节点
        for child in node.children:
            sort_file_tree(child)
        
        # 对当前节点的子节点排序
        node.children.sort(key=lambda x: (
            x.type == "file",  # 目录在前（False < True）
            x.uri.split('/')[-1].lower()  # 按名称排序
        ))
    
    return node


def filter_file_tree_by_patterns(node: FileTreeNode, include_patterns: List[str] = None, 
                                exclude_patterns: List[str] = None) -> Optional[FileTreeNode]:
    """
    根据模式过滤文件树
    
    Args:
        node: 文件树节点
        include_patterns: 包含模式列表
        exclude_patterns: 排除模式列表
        
    Returns:
        Optional[FileTreeNode]: 过滤后的节点，如果被完全过滤则返回None
    """
    import fnmatch
    
    if node.type == "file":
        # 对文件进行模式匹配
        filename = node.uri.split('/')[-1]
        
        # 检查排除模式
        if exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(node.uri, pattern):
                    return None
        
        # 检查包含模式
        if include_patterns:
            included = False
            for pattern in include_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    included = True
                    break
            if not included:
                return None
        
        return node
    
    else:
        # 对目录递归处理
        if node.children:
            filtered_children = []
            for child in node.children:
                filtered_child = filter_file_tree_by_patterns(child, include_patterns, exclude_patterns)
                if filtered_child:
                    filtered_children.append(filtered_child)
            
            if filtered_children:
                # 创建新的目录节点
                return FileTreeNode(
                    type="directory",
                    uri=node.uri,
                    children=filtered_children
                )
        
        return None


def get_file_tree_stats(node: FileTreeNode) -> Dict[str, int]:
    """
    获取文件树统计信息
    
    Args:
        node: 文件树根节点
        
    Returns:
        Dict[str, int]: 统计信息
    """
    stats = {"files": 0, "directories": 0, "total_size": 0}
    
    def _count_recursive(n: FileTreeNode):
        if n.type == "file":
            stats["files"] += 1
            if n.content:
                stats["total_size"] += len(n.content)
        else:
            stats["directories"] += 1
            if n.children:
                for child in n.children:
                    _count_recursive(child)
    
    _count_recursive(node)
    return stats