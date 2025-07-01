from pathlib import Path
from prompt_toolkit import PromptSession
from utils.workspace import WorkspaceManager
from utils.file_utils import convert_pdf_to_md, convert_docx_to_md

def handle_file_command(session: PromptSession, ws: WorkspaceManager):
    """处理文件管理命令"""
    RED = '\033[31m'
    RESET = '\033[0m'
    
    while True:
        workspace_files = ws.list_files()
        print(f"\n{RED}文件管理操作（当前工作区文件：{len(workspace_files)}个）{RESET}")
        print("1. 扫描并添加文件 - 从workdir目录添加文件到工作区")
        print("2. 列出工作区文件 - 显示已添加的文件及其类型")
        print("3. 移除工作区文件 - 从工作区删除指定文件")
        print(f"{RED}0. 返回主菜单{RESET}")
        print(f"{RED}提示：支持的文件类型：PDF/DOCX/MD/TXT{RESET}")
        
        try:
            print(f"{RED}{'-'*50}{RESET}")
            if workspace_files:
                print(f"{RED}工作区文件：" + ", ".join([f for f in workspace_files]) + f"{RESET}")
            choice = session.prompt('file> ')
            if not choice:
                print("请问您需要我做什么？")
                continue
            if choice.startswith('/'):
                return choice  # 将命令传递回主循环
            if choice == '0':
                return ''

            if choice == '1':
                work_dir = Path("workdir")
                work_dir.mkdir(exist_ok=True)
                file_list = list(work_dir.glob("*.pdf")) + list(work_dir.glob("*.docx")) + \
                          list(work_dir.glob("*.md")) + list(work_dir.glob("*.txt"))
                          
                if not file_list:
                    print("workdir目录中没有可用的文件（支持pdf/docx/md/txt格式）")
                    continue
                    
                print("\nworkdir目录中的可用文件：")
                for i, f in enumerate(file_list, 1):
                    print(f"{i}. {f.name}")
                    
                file_nums = session.prompt("请输入要添加的文件编号（多个用空格分隔）: ")
                if not file_nums.strip():
                    print("操作已取消")
                    continue
                    
                added = []
                try:
                    indexes = [int(n)-1 for n in file_nums.split()]
                    selected_files = [file_list[i] for i in indexes]
                except (ValueError, IndexError):
                    print("错误：请输入有效的文件编号")
                    continue
                    
                for file_path in selected_files:
                    if not file_path.exists():
                        print(f"文件不存在：{file_path}")
                        continue
                        
                    if file_path.suffix.lower() in ('.pdf', '.docx'):
                        md_path = file_path.with_suffix('.md')
                        try:
                            if file_path.suffix.lower() == '.pdf':
                                convert_pdf_to_md(str(file_path), str(md_path))
                            else:
                                convert_docx_to_md(str(file_path), str(md_path))
                            ws.add_file(str(md_path.resolve()), 'auto')
                            added.append(str(md_path))
                        except Exception as e:
                            print(f"转换文件 {file_path} 失败：{str(e)}")
                    elif file_path.suffix.lower() in ('.txt', '.md'):
                        file_type = session.prompt(
                            f"请为文件 {file_path.name} 选择类型：\n"
                            "1. 简历\n2. 职位描述(JD)\n请输入编号: "
                        ).strip()
                        file_type = 'resume' if file_type == '1' else 'jd'
                        ws.add_file(str(file_path.resolve()), file_type)
                        added.append(file_path.name)
                    else:
                        print(f"跳过不支持的文件类型：{file_path.suffix}")
                
                if added:
                    print(f"已添加文件：{', '.join(added)}")
                    continue

            elif choice == '3':
                all_files = [f['path'] for f in ws.config['workspace_files']]
                if not all_files:
                    print("工作区中没有文件可移除")
                    continue
                    
                print("\n当前工作区文件：")
                for i, path in enumerate(all_files, 1):
                    print(f"{i}. {Path(path).name}")
                    
                to_remove = session.prompt("请输入要移除的文件编号（多个用空格分隔）: ")
                if not to_remove.strip():
                    print("操作已取消")
                    continue
                    
                try:
                    indexes = [int(i) for i in to_remove.split()]
                    if any(i < 1 or i > len(all_files) for i in indexes):
                        raise ValueError("编号超出范围")
                        
                    selected_paths = [all_files[i-1] for i in indexes]
                    removed_files = [Path(p).name for p in selected_paths]
                    ws.remove_files(selected_paths)
                    print(f"\n✅ 已移除文件：{', '.join(removed_files)}")
                except (ValueError, IndexError):
                    print("错误：请输入有效的文件编号")
                    
            else:
                print("错误：无效选项，请输入 0-3 的数字")
                
        except (KeyboardInterrupt, EOFError):
            return ''
