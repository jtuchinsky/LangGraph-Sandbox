import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


class FileSystemTools:
    """Инструменты для работы с файловой системой"""
    
    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Читать файл"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "content": None
                }
            
            with open(path, 'r', encoding=encoding) as file:
                content = file.read()
            
            return {
                "success": True,
                "content": content,
                "file_path": str(path.absolute()),
                "size": path.stat().st_size,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}",
                "content": None
            }
    
    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> Dict[str, Any]:
        """Создать или изменить файл"""
        try:
            path = Path(file_path)
            
            # Create directories if needed
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as file:
                file.write(content)
            
            return {
                "success": True,
                "file_path": str(path.absolute()),
                "size": path.stat().st_size,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}",
                "file_path": file_path
            }
    
    @staticmethod
    def append_file(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Добавить контент в файл"""
        try:
            path = Path(file_path)
            
            with open(path, 'a', encoding=encoding) as file:
                file.write(content)
            
            return {
                "success": True,
                "file_path": str(path.absolute()),
                "size": path.stat().st_size,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error appending to file: {str(e)}",
                "file_path": file_path
            }
    
    @staticmethod
    def delete_file(file_path: str) -> Dict[str, Any]:
        """Удалить файл"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "file_path": file_path
                }
            
            path.unlink()
            
            return {
                "success": True,
                "file_path": str(path.absolute()),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting file: {str(e)}",
                "file_path": file_path
            }
    
    @staticmethod
    def copy_file(source_path: str, destination_path: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Копировать файл"""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                return {
                    "success": False,
                    "error": f"Source file not found: {source_path}",
                    "source_path": source_path,
                    "destination_path": destination_path
                }
            
            if create_dirs and not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            
            return {
                "success": True,
                "source_path": str(source.absolute()),
                "destination_path": str(destination.absolute()),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error copying file: {str(e)}",
                "source_path": source_path,
                "destination_path": destination_path
            }
    
    @staticmethod
    def move_file(source_path: str, destination_path: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Переместить файл"""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                return {
                    "success": False,
                    "error": f"Source file not found: {source_path}",
                    "source_path": source_path,
                    "destination_path": destination_path
                }
            
            if create_dirs and not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            
            return {
                "success": True,
                "source_path": source_path,
                "destination_path": str(destination.absolute()),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error moving file: {str(e)}",
                "source_path": source_path,
                "destination_path": destination_path
            }
    
    @staticmethod
    def list_directory(directory_path: str) -> Dict[str, Any]:
        """Список файлов и папок в директории"""
        try:
            path = Path(directory_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}",
                    "items": []
                }
            
            if not path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory_path}",
                    "items": []
                }
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "path": str(item.absolute()),
                    "is_file": item.is_file(),
                    "is_directory": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "success": True,
                "directory_path": str(path.absolute()),
                "items": items,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing directory: {str(e)}",
                "items": []
            }
    
    @staticmethod
    def create_directory(directory_path: str, parents: bool = True) -> Dict[str, Any]:
        """Создать директорию"""
        try:
            path = Path(directory_path)
            path.mkdir(parents=parents, exist_ok=True)
            
            return {
                "success": True,
                "directory_path": str(path.absolute()),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating directory: {str(e)}",
                "directory_path": directory_path
            }
    
    @staticmethod
    def file_exists(file_path: str) -> Dict[str, Any]:
        """Проверить существование файла"""
        try:
            path = Path(file_path)
            exists = path.exists()
            is_file = path.is_file() if exists else False
            is_directory = path.is_dir() if exists else False
            
            return {
                "success": True,
                "file_path": file_path,
                "exists": exists,
                "is_file": is_file,
                "is_directory": is_directory,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error checking file existence: {str(e)}",
                "file_path": file_path,
                "exists": False
            }