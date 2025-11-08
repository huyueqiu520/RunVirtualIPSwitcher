import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import json
import socket
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

class VirtualIPSwitcher:
    def __init__(self):
        self.setup_logging()  # 初始化日志系统
        self.config_file = "virtual_ip_config.json"
        self.config = self.load_config()
        self.setup_gui()
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            # 创建logs目录
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            # 创建日志器
            self.logger = logging.getLogger('VirtualIPSwitcher')
            self.logger.setLevel(logging.INFO)
            
            # 创建文件处理器（最多保存5个日志文件，每个最大1MB）
            file_handler = RotatingFileHandler(
                'logs/virtual_ip_switcher.log', 
                maxBytes=1024*1024, 
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 创建格式器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理器到日志器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            self.logger.info("日志系统初始化成功")
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.logger = None
    
    def log_error(self, error_msg):
        """记录错误信息"""
        if self.logger:
            self.logger.error(error_msg)
    
    def log_info(self, info_msg):
        """记录信息"""
        if self.logger:
            self.logger.info(info_msg)

    def load_config(self):
        """加载配置文件"""
        default_config = {
            "virtual_ips": [
                {"name": "IP配置1", "ip": "192.168.1.100", "subnet": "255.255.255.0", "gateway": "192.168.1.1"},
                {"name": "IP配置2", "ip": "192.168.1.101", "subnet": "255.255.255.0", "gateway": "192.168.1.1"},
                {"name": "IP配置3", "ip": "10.0.0.100", "subnet": "255.0.0.0", "gateway": "10.0.0.1"}
            ],
            "adapter_name": "以太网"  # 默认网卡名称
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                self.log_error("加载配置文件失败，使用默认配置")
                return default_config
        else:
            # 创建默认配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            self.log_info("创建默认配置文件")
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        # 在保存前创建备份
        self.backup_config()
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.log_info("配置已保存")
    
    def backup_config(self):
        """备份配置文件"""
        import shutil
        from datetime import datetime
        if os.path.exists(self.config_file):
            try:
                # 创建备份文件名（带时间戳）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{self.config_file}.backup_{timestamp}.json"
                shutil.copy2(self.config_file, backup_file)
                
                # 只保留最近5个备份文件
                self.cleanup_old_backups()
                self.log_info(f"配置文件已备份: {backup_file}")
            except Exception as e:
                self.log_error(f"创建备份时发生错误: {e}")
    
    def cleanup_old_backups(self):
        """清理旧的备份文件"""
        import glob
        backup_files = glob.glob(f"{self.config_file}.backup_*.json")
        if len(backup_files) > 5:  # 只保留最近5个备份
            # 按时间排序并删除最旧的
            backup_files.sort(key=os.path.getmtime)
            for old_backup in backup_files[:-5]:
                try:
                    os.remove(old_backup)
                except:
                    pass  # 如果无法删除旧备份，继续执行

    def setup_gui(self):
        """设置图形用户界面"""
        self.root = tk.Tk()
        self.root.title("虚拟IP切换器 - v2.1")
        self.root.geometry("550x500")
        self.root.resizable(False, False)
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="虚拟IP切换器", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 网卡选择
        ttk.Label(main_frame, text="网络适配器:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.adapter_var = tk.StringVar(value=self.config.get("adapter_name", "以太网"))
        self.adapter_entry = ttk.Entry(main_frame, textvariable=self.adapter_var, width=25)
        self.adapter_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 5))
        
        # 刷新网卡列表按钮
        ttk.Button(main_frame, text="刷新", command=self.refresh_adapters, width=8).grid(row=1, column=2, pady=5, padx=(0, 10))
        
        # IP配置列表
        ttk.Label(main_frame, text="IP配置:").grid(row=2, column=0, sticky=(tk.W, tk.N), pady=5)
        
        # 创建IP配置列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(10, 0))
        
        self.ip_listbox = tk.Listbox(list_frame, height=8, width=35)
        self.ip_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ip_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.ip_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 更新列表显示
        self.update_ip_list()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=15)
        
        # 按钮
        ttk.Button(button_frame, text="应用IP配置", command=self.apply_ip_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="添加IP配置", command=self.add_ip_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑IP配置", command=self.edit_ip_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除IP配置", command=self.delete_ip_config).pack(side=tk.LEFT, padx=5)
        
        # 高级功能按钮框架
        advanced_frame = ttk.Frame(main_frame)
        advanced_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(advanced_frame, text="导出配置", command=self.export_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(advanced_frame, text="导入配置", command=self.import_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(advanced_frame, text="获取当前IP", command=self.get_current_ip).pack(side=tk.LEFT, padx=5)
        ttk.Button(advanced_frame, text="网络诊断", command=self.network_diagnosis).pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="就绪", foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=10)
        
        # 配置列权重
        main_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 绑定键盘事件
        self.root.bind('<Delete>', lambda event: self.delete_ip_config())
        self.root.bind('<F5>', lambda event: self.refresh_adapters())
        
        self.log_info("GUI界面初始化完成")
        
    def update_ip_list(self):
        """更新IP配置列表显示"""
        self.ip_listbox.delete(0, tk.END)
        for ip_config in self.config["virtual_ips"]:
            display_text = f"{ip_config['name']} - {ip_config['ip']}"
            self.ip_listbox.insert(tk.END, display_text)
    
    def apply_ip_config(self):
        """应用选定的IP配置"""
        selection = self.ip_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个IP配置！")
            return
        
        ip_config = self.config["virtual_ips"][selection[0]]
        adapter_name = self.adapter_var.get()
        
        # 检查IP是否已被其他适配器使用
        if self.is_ip_in_use(ip_config["ip"]):
            if not messagebox.askyesno("IP冲突警告", f"IP地址 {ip_config['ip']} 可能已被其他适配器使用，是否继续应用此配置？"):
                self.log_info(f"用户取消应用IP配置: {ip_config['name']}")
                return
        
        try:
            # 使用管理员权限执行IP配置命令
            cmd = f'netsh interface ip set address "{adapter_name}" static {ip_config["ip"]} {ip_config["subnet"]} {ip_config["gateway"]} 1'
            self.log_info(f"正在应用IP配置: {ip_config['name']} - {ip_config['ip']}")
            
            # 在Windows中，通常需要管理员权限才能修改IP配置
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # 设置DNS（如果配置中有DNS信息）
                if "dns" in ip_config and ip_config["dns"]:
                    dns_result = subprocess.run(
                        f'netsh interface ip set dns "{adapter_name}" static {ip_config["dns"]} primary', 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if dns_result.returncode != 0:
                        self.log_error(f"设置DNS时出现警告: {dns_result.stderr}")
                
                self.status_label.config(text=f"IP配置已应用: {ip_config['name']} - {ip_config['ip']}", foreground="green")
                messagebox.showinfo("成功", f"IP配置已成功应用:\n{ip_config['name']}\n{ip_config['ip']}")
                
                # 刷新网络连接
                self.refresh_network_connection()
                self.log_info(f"IP配置应用成功: {ip_config['name']}")
            else:
                self.status_label.config(text="应用失败", foreground="red")
                error_msg = f"应用IP配置失败:\n{result.stderr}"
                self.log_error(error_msg)
                messagebox.showerror("错误", error_msg)
                
        except Exception as e:
            error_msg = f"应用IP配置时发生错误:\n{str(e)}"
            self.log_error(error_msg)
            self.status_label.config(text="应用失败", foreground="red")
            messagebox.showerror("错误", error_msg)
    
    def refresh_network_connection(self):
        """刷新网络连接"""
        try:
            # 尝试释放并重新获取IP
            subprocess.run(
                'ipconfig /release && ipconfig /renew', 
                shell=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.log_info("网络连接已刷新")
        except Exception as e:
            self.log_error(f"刷新网络连接时发生错误: {e}")
    
    def is_ip_in_use(self, ip):
        """检查IP是否已被其他适配器使用"""
        try:
            # 使用ping命令检查IP是否可达
            result = subprocess.run(
                f'ping -n 1 -w 1000 {ip}', 
                shell=True, 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # 如果ping成功，说明IP可能正在使用中
            is_in_use = result.returncode == 0
            if is_in_use:
                self.log_info(f"检测到IP {ip} 可能正在被使用")
            return is_in_use
        except:
            # 出现异常时，默认不提示冲突
            return False
    
    def add_ip_config(self):
        """添加新的IP配置"""
        self.log_info("启动添加IP配置对话框")
        AddEditIPConfigDialog(self.root, self, "添加IP配置")
    
    def edit_ip_config(self):
        """编辑选中的IP配置"""
        selection = self.ip_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个IP配置！")
            return
        
        self.log_info("启动编辑IP配置对话框")
        AddEditIPConfigDialog(self.root, self, "编辑IP配置", self.config["virtual_ips"][selection[0]], selection[0])
    
    def delete_ip_config(self):
        """删除选中的IP配置"""
        selection = self.ip_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个IP配置！")
            return
        
        if messagebox.askyesno("确认", "确定要删除选定的IP配置吗？"):
            del self.config["virtual_ips"][selection[0]]
            self.save_config()
            self.update_ip_list()
            self.status_label.config(text="IP配置已删除", foreground="green")
            self.log_info("IP配置已删除")
    
    def update_ip_config_list(self, ip_config, index=None):
        """更新IP配置列表（从子对话框）"""
        if index is not None:
            # 编辑现有配置
            self.config["virtual_ips"][index] = ip_config
        else:
            # 添加新配置
            self.config["virtual_ips"].append(ip_config)
        
        self.save_config()
        self.update_ip_list()
        self.status_label.config(text="IP配置已更新", foreground="green")
        self.log_info(f"IP配置已{'更新' if index is not None else '添加'}: {ip_config['name']}")
    
    def refresh_adapters(self):
        """刷新网卡列表"""
        try:
            result = subprocess.run(
                'netsh interface show interface', 
                shell=True, 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                # 提取活动的网卡名称
                lines = result.stdout.split('\n')
                adapters = []
                for line in lines:
                    if '已连接' in line or '已断开' in line:
                        # 提取网卡名称
                        parts = line.split()
                        if len(parts) >= 4:
                            adapters.append(' '.join(parts[3:]))
                
                if adapters:
                    # 显示可用网卡的简单选择对话框
                    adapter = self.select_adapter_dialog(adapters)
                    if adapter:
                        self.adapter_var.set(adapter)
                        self.config["adapter_name"] = adapter
                        self.save_config()
                        self.status_label.config(text=f"已选择网卡: {adapter}", foreground="green")
                        self.log_info(f"已选择网卡: {adapter}")
                else:
                    messagebox.showinfo("信息", "未找到网络适配器")
                    self.log_info("未找到网络适配器")
            else:
                error_msg = "无法获取网络适配器列表"
                self.log_error(error_msg)
                messagebox.showerror("错误", error_msg)
        except Exception as e:
            error_msg = f"获取网络适配器时发生错误:\n{str(e)}"
            self.log_error(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def select_adapter_dialog(self, adapters):
        """显示网卡选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("选择网络适配器")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        ttk.Label(dialog, text="请选择网络适配器:").pack(pady=10)
        
        # 创建列表框
        listbox = tk.Listbox(dialog, height=6)
        for adapter in adapters:
            listbox.insert(tk.END, adapter)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        selected_adapter = {"value": None}
        
        def select():
            selection = listbox.curselection()
            if selection:
                selected_adapter["value"] = adapters[selection[0]]
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "请选择一个网络适配器")
        
        ttk.Button(dialog, text="选择", command=select).pack(pady=10)
        
        # 等待对话框关闭
        dialog.wait_window()
        return selected_adapter["value"]
    
    def export_config(self):
        """导出配置到文件"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="导出配置"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                self.status_label.config(text="配置已导出", foreground="green")
                messagebox.showinfo("成功", f"配置已成功导出到:\n{file_path}")
                self.log_info(f"配置已导出到: {file_path}")
            except Exception as e:
                error_msg = f"导出配置时发生错误:\n{str(e)}"
                self.log_error(error_msg)
                self.status_label.config(text="导出失败", foreground="red")
                messagebox.showerror("错误", error_msg)
    
    def import_config(self):
        """从文件导入配置"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="导入配置"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # 验证导入的配置格式
                if "virtual_ips" in imported_config and "adapter_name" in imported_config:
                    self.config = imported_config
                    self.save_config()
                    self.update_ip_list()
                    self.status_label.config(text="配置已导入", foreground="green")
                    messagebox.showinfo("成功", f"配置已成功导入自:\n{file_path}")
                    self.log_info(f"配置已从 {file_path} 导入")
                else:
                    error_msg = "配置文件格式不正确"
                    messagebox.showerror("错误", error_msg)
                    self.log_error(error_msg)
            except Exception as e:
                error_msg = f"导入配置时发生错误:\n{str(e)}"
                self.log_error(error_msg)
                self.status_label.config(text="导入失败", foreground="red")
                messagebox.showerror("错误", error_msg)
    
    def network_diagnosis(self):
        """执行网络诊断"""
        try:
            # 创建网络诊断对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("网络诊断")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中显示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 创建文本框显示诊断结果
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            # 显示加载信息
            text_widget.insert(tk.END, "正在执行网络诊断...\n\n")
            text_widget.update()
            
            # 执行各种网络检查
            import platform
            
            # 1. 基本网络信息
            text_widget.insert(tk.END, "=== 基本网络信息 ===\n")
            import socket
            hostname = socket.gethostname()
            text_widget.insert(tk.END, f"主机名: {hostname}\n")
            
            try:
                local_ip = socket.gethostbyname(hostname)
                text_widget.insert(tk.END, f"本地IP: {local_ip}\n")
            except:
                text_widget.insert(tk.END, "本地IP: 无法获取\n")
            
            # 2. 网络连通性测试
            text_widget.insert(tk.END, "\n=== 网络连通性测试 ===\n")
            
            # 测试到网关的连通性
            gateway = self.config.get("adapter_name", "以太网")
            # 尝试获取当前网关
            try:
                result = subprocess.run('ipconfig', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                lines = result.stdout.split('\n')
                current_gateway = None
                for line in lines:
                    if 'Default Gateway' in line and ':' in line:
                        current_gateway = line.split(':')[-1].strip()
                        break
                
                if current_gateway:
                    text_widget.insert(tk.END, f"默认网关: {current_gateway}\n")
                    # ping网关
                    ping_result = subprocess.run(f'ping -n 1 -w 1000 {current_gateway}', 
                                                shell=True, capture_output=True, text=True, 
                                                creationflags=subprocess.CREATE_NO_WINDOW)
                    if ping_result.returncode == 0:
                        text_widget.insert(tk.END, "网关连通性: 正常\n")
                    else:
                        text_widget.insert(tk.END, "网关连通性: 异常\n")
                else:
                    text_widget.insert(tk.END, "默认网关: 未找到\n")
            except:
                text_widget.insert(tk.END, "默认网关: 无法获取\n")
            
            # 3. DNS解析测试
            text_widget.insert(tk.END, "\n=== DNS解析测试 ===\n")
            try:
                import urllib.request
                with urllib.request.urlopen('https://www.baidu.com', timeout=5) as response:
                    text_widget.insert(tk.END, "DNS解析: 正常 (www.baidu.com)\n")
            except:
                text_widget.insert(tk.END, "DNS解析: 异常\n")
            
            # 4. 外网连通性测试
            text_widget.insert(tk.END, "\n=== 外网连通性测试 ===\n")
            external_sites = ["www.baidu.com", "www.google.com", "www.github.com"]
            for site in external_sites:
                try:
                    result = subprocess.run(f'ping -n 1 -w 1000 {site}', 
                                           shell=True, capture_output=True, text=True, 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        text_widget.insert(tk.END, f"{site}: 连通正常\n")
                    else:
                        text_widget.insert(tk.END, f"{site}: 连通异常\n")
                except:
                    text_widget.insert(tk.END, f"{site}: 测试失败\n")
            
            # 5. 网络适配器状态
            text_widget.insert(tk.END, "\n=== 网络适配器状态 ===\n")
            try:
                result = subprocess.run('netsh interface show interface', 
                                       shell=True, capture_output=True, text=True, 
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    text_widget.insert(tk.END, result.stdout)
                else:
                    text_widget.insert(tk.END, "无法获取网络适配器状态\n")
            except:
                text_widget.insert(tk.END, "无法获取网络适配器状态\n")
            
            # 设置文本框为只读
            text_widget.config(state=tk.DISABLED)
            
            # 添加关闭按钮
            ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
            
            self.log_info("网络诊断完成")
            
        except Exception as e:
            error_msg = f"执行网络诊断时发生错误:\n{str(e)}"
            self.log_error(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def get_current_ip(self):
        """获取当前网络IP信息"""
        try:
            import socket
            # 获取本地IP
            hostname = socket.gethostname()
            
            # 获取本地IP - 通过连接到一个远程服务器来确定本地IP
            local_ip = self.get_local_ip()
            
            # 通过多个服务获取公网IP，增加成功率
            external_ip = self.get_external_ip()
            
            messagebox.showinfo("当前IP信息", f"主机名: {hostname}\n本地IP: {local_ip}\n公网IP: {external_ip}")
            self.log_info(f"获取IP信息完成 - 本地IP: {local_ip}, 公网IP: {external_ip}")
        except Exception as e:
            error_msg = f"获取IP信息时发生错误:\n{str(e)}"
            self.log_error(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def get_local_ip(self):
        """获取本地IP地址"""
        try:
            import socket
            # 创建一个socket连接到远程服务器（不会发送数据），以确定本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            try:
                # 备选方案：使用hostname获取本地IP
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                return local_ip
            except:
                return "无法获取本地IP"
    
    def get_external_ip(self):
        """通过多个服务获取公网IP"""
        try:
            import urllib.request
            import urllib.error
            import json
            
            # 多个IP查询服务，按优先级排列
            ip_services = [
                # 简单返回IP的服务
                {'url': 'https://api.ipify.org', 'type': 'simple'},
                {'url': 'https://icanhazip.com', 'type': 'simple'},
                {'url': 'https://ident.me', 'type': 'simple'},
                {'url': 'https://ipecho.net/plain', 'type': 'simple'},
                {'url': 'https://myexternalip.com/raw', 'type': 'simple'},
                {'url': 'https://checkip.amazonaws.com', 'type': 'simple'},
                
                # 返回JSON的服务
                {'url': 'https://httpbin.org/ip', 'type': 'json', 'field': 'origin'},
                {'url': 'https://ipapi.co/json/', 'type': 'json', 'field': 'ip'},
                {'url': 'https://jsonip.com', 'type': 'json', 'field': 'ip'},
                {'url': 'https://api.my-ip.io/ip.json', 'type': 'json', 'field': 'ip'},
                
                # HTTPS服务
                {'url': 'https://ip.seeip.org', 'type': 'simple'},
                {'url': 'https://ip.tyk.nu', 'type': 'simple'}
            ]
            
            for service in ip_services:
                try:
                    # 添加请求头，模拟浏览器访问
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                    
                    req = urllib.request.Request(service['url'], headers=headers)
                    with urllib.request.urlopen(req, timeout=15) as response:
                        content = response.read().decode('utf-8').strip()
                        
                        if service['type'] == 'simple':
                            # 简单服务直接返回IP
                            if self.is_valid_ip(content):
                                self.log_info(f"获取公网IP成功: {content}")
                                return content
                        elif service['type'] == 'json':
                            # JSON服务需要解析
                            try:
                                data = json.loads(content)
                                ip = data.get(service['field'], '')
                                if self.is_valid_ip(ip):
                                    self.log_info(f"获取公网IP成功: {ip}")
                                    return ip
                            except:
                                continue  # JSON解析失败，尝试下一个服务
                except urllib.error.URLError as e:
                    continue  # 如果当前服务失败，尝试下一个
                except Exception as e:
                    continue  # 其他异常也继续尝试下一个服务
            
            error_msg = "无法获取公网IP"
            self.log_error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"获取公网IP时发生错误: {str(e)}"
            self.log_error(error_msg)
            return error_msg

    def run(self):
        """运行GUI应用程序"""
        self.log_info("应用程序启动")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """关闭应用程序时的处理"""
        self.log_info("应用程序关闭")
        self.save_config()
        self.root.destroy()

class AddEditIPConfigDialog:
    def __init__(self, parent, app, title, ip_config=None, index=None):
        self.parent = parent
        self.app = app
        self.ip_config = ip_config or {"name": "", "ip": "", "subnet": "255.255.255.0", "gateway": "", "dns": "8.8.8.8"}
        self.index = index
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x240")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_dialog()
        
    def setup_dialog(self):
        """设置对话框界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建一个画布和滚动条来支持垂直滚动
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 名称
        ttk.Label(scrollable_frame, text="配置名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.ip_config["name"])
        ttk.Entry(scrollable_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # IP地址
        ttk.Label(scrollable_frame, text="IP地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ip_var = tk.StringVar(value=self.ip_config["ip"])
        ttk.Entry(scrollable_frame, textvariable=self.ip_var, width=30).grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # 子网掩码
        ttk.Label(scrollable_frame, text="子网掩码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.subnet_var = tk.StringVar(value=self.ip_config["subnet"])
        ttk.Entry(scrollable_frame, textvariable=self.subnet_var, width=30).grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # 网关
        ttk.Label(scrollable_frame, text="网关:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.gateway_var = tk.StringVar(value=self.ip_config["gateway"])
        ttk.Entry(scrollable_frame, textvariable=self.gateway_var, width=30).grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # DNS服务器
        ttk.Label(scrollable_frame, text="DNS服务器:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.dns_var = tk.StringVar(value=self.ip_config.get("dns", "8.8.8.8"))
        ttk.Entry(scrollable_frame, textvariable=self.dns_var, width=30).grid(row=4, column=1, pady=5, padx=(10, 0))
        
        # 常用DNS服务器说明
        dns_info = ttk.Label(scrollable_frame, text="常用DNS: 8.8.8.8 (Google) 或 114.114.114.114", font=("Arial", 8))
        dns_info.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        # 按钮
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # 将画布和滚动条放置到主框架中
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定回车键
        self.dialog.bind('<Return>', lambda event: self.ok())
        self.dialog.bind('<Escape>', lambda event: self.cancel())
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.dialog.bind_all("<MouseWheel>", _on_mousewheel)
        
    def ok(self):
        """确定按钮处理"""
        name = self.name_var.get().strip()
        ip = self.ip_var.get().strip()
        subnet = self.subnet_var.get().strip()
        gateway = self.gateway_var.get().strip()
        dns = self.dns_var.get().strip()
        
        if not name or not ip or not subnet or not gateway:
            messagebox.showwarning("警告", "请填写所有必需字段！")
            return
        
        # 验证IP地址格式
        if not self.is_valid_ip(ip):
            messagebox.showerror("错误", "IP地址格式不正确！\n请输入有效的IPv4地址，如192.168.1.100")
            return
        
        if not self.is_valid_ip(subnet):
            messagebox.showerror("错误", "子网掩码格式不正确！\n请输入有效的子网掩码，如255.255.255.0")
            return
            
        # 验证子网掩码是否为有效值
        if not self.is_valid_subnet(subnet):
            messagebox.showerror("错误", "子网掩码值无效！\n请输入标准的子网掩码值")
            return
        
        if not self.is_valid_ip(gateway):
            messagebox.showerror("错误", "网关地址格式不正确！\n请输入有效的网关地址，如192.168.1.1")
            return
            
        # 如果提供了DNS，验证其格式
        if dns and not self.is_valid_ip(dns):
            messagebox.showerror("错误", "DNS服务器地址格式不正确！\n请输入有效的DNS地址，如8.8.8.8")
            return
        
        # 验证网关是否在子网内
        if not self.is_gateway_in_subnet(ip, subnet, gateway):
            messagebox.showerror("错误", "网关地址不在当前子网内！\n请检查IP地址和网关设置")
            return
        
        # 检查配置名称是否已存在
        if self.index is None:  # 添加新配置时检查
            for config in self.app.config["virtual_ips"]:
                if config["name"] == name:
                    messagebox.showwarning("警告", f"配置名称 '{name}' 已存在！\n请使用不同的名称")
                    return
        
        # 更新配置
        new_config = {
            "name": name,
            "ip": ip,
            "subnet": subnet,
            "gateway": gateway,
            "dns": dns  # 添加DNS设置
        }
        
        self.app.update_ip_config_list(new_config, self.index)
        self.dialog.destroy()
    
    def cancel(self):
        """取消按钮处理"""
        self.dialog.destroy()
    
    def is_valid_ip(self, ip):
        """验证IP地址格式"""
        try:
            # 使用更严格的IP地址验证
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                # 检查每部分是否为数字且在0-255范围内
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    return False
            # 不允许以0开头的非零数字（如01, 001等）
            if any(part != '0' and part.startswith('0') for part in parts):
                return False
            return True
        except:
            return False
    
    def is_valid_subnet(self, subnet):
        """验证子网掩码是否有效"""
        try:
            parts = subnet.split('.')
            if len(parts) != 4:
                return False
            # 常见的子网掩码值
            valid_masks = [
                "255.255.255.255", "255.255.255.254", "255.255.255.252", "255.255.255.248",
                "255.255.255.240", "255.255.255.224", "255.255.255.192", "255.255.255.128",
                "255.255.255.0", "255.255.254.0", "255.255.252.0", "255.255.248.0",
                "255.255.240.0", "255.255.224.0", "255.255.192.0", "255.255.128.0",
                "255.255.0.0", "255.254.0.0", "255.252.0.0", "255.248.0.0",
                "255.240.0.0", "255.224.0.0", "255.192.0.0", "255.128.0.0",
                "255.0.0.0", "254.0.0.0", "252.0.0.0", "248.0.0.0",
                "240.0.0.0", "224.0.0.0", "192.0.0.0", "128.0.0.0", "0.0.0.0"
            ]
            return subnet in valid_masks
        except:
            return False
    
    def is_gateway_valid(self, ip, gateway):
        """验证网关是否在IP的子网内"""
        try:
            ip_parts = [int(x) for x in ip.split('.')]
            gateway_parts = [int(x) for x in gateway.split('.')]
            
            # 检查IP和网关是否在同一子网内（基本检查）
            for i in range(4):
                if ip_parts[i] != gateway_parts[i]:
                    # 如果IP和网关的某一位不同，检查是否在同一子网内
                    break
            return True  # 简单检查，实际应用中可能需要更复杂的逻辑
        except:
            return False
    
    def is_gateway_in_subnet(self, ip, subnet, gateway):
        """检查网关是否在IP和子网掩码定义的子网内"""
        try:
            # 将IP、子网掩码和网关转换为整数
            def ip_to_int(ip_str):
                parts = ip_str.split('.')
                return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
            
            ip_int = ip_to_int(ip)
            subnet_int = ip_to_int(subnet)
            gateway_int = ip_to_int(gateway)
            
            # 计算网络地址
            network_address = ip_int & subnet_int
            broadcast_address = ip_int | (0xFFFFFFFF ^ subnet_int)
            
            # 检查网关是否在网络范围内
            return network_address <= gateway_int <= broadcast_address
        except:
            return False

if __name__ == "__main__":
    app = VirtualIPSwitcher()
    app.run()