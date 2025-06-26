from pathlib import Path
import json
from config import load_config, save_config

class WorkspaceManager:
    def __init__(self):
        self.config = load_config()
    
    def add_file(self, path: str, file_type: str):
        """添加文件到工作区并存储内容"""
        # 去重处理
        self.config['workspace_files'] = [
            f for f in self.config['workspace_files']
            if f['path'] != path
        ]
        
        self.config['workspace_files'].append({
            'path': path,
            'type': file_type,
        })
        save_config(self.config)
    
    def remove_files(self, paths: list):
        """从工作区移除指定路径的文件"""
        # 保留不在移除列表中的文件
        self.config['workspace_files'] = [
            f for f in self.config['workspace_files']
            if f['path'] not in paths
        ]
        save_config(self.config)
    
    def get_resumes(self):
        """获取所有简历内容"""
        # print("get_resumes files:",self.config['workspace_files'])
        content = {}
        for f in self.config['workspace_files']:
            if f['type'] == 'resume':
                with open(f['path'], 'r', encoding='utf-8') as file:
                    content = file.read()
                    break;  """暂时只读第一份简历文件"""
        return content
    
    def get_jds(self):
        """获取所有职位描述内容"""
        for f in self.config['workspace_files']:
            if f['type'] == 'jd':
                with open(f['path'], 'r', encoding='utf-8') as file:
                    content = file.read()
                    break; """暂时只读第一份jd文件"""
        return content
    
    def get_file_types(self):
        """返回文件类型统计"""
        types = {'resume': 0, 'jd': 0}
        for f in self.config['workspace_files']:
            types[f['type']] += 1
        return types
    
    def list_files(self):
        """返回带类型标记的文件列表"""
        return [
            f"{Path(f['path']).name} [{f['type'].upper()}]" 
            for f in self.config['workspace_files']
        ]
    
    def get_raw_files(self):
        """返回原始文件路径列表"""
        return [f['path'] for f in self.config['workspace_files']]
