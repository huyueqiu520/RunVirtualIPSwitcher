# 虚拟IP切换器 VirtualIPSwitcher

一个简单易用的IP地址切换工具，可以帮助用户快速切换网络配置。

## 功能特点

- 图形化界面，操作简单
- 支持多个IP配置方案
- 一键切换IP配置
- 自动检测IP冲突
- 支持DNS设置
- 网络诊断功能
- 获取当前网络IP信息
- 配置导入导出
- 自动备份配置

## 使用方法

1. 双击 `RunVirtualIPSwitcher.bat` 以管理员身份运行
2. 在网络适配器中选择要配置的网卡
3. 添加或编辑IP配置方案
4. 选择需要的配置方案并点击"应用IP配置"

## 系统要求

- Windows 7/8/10/11
- Python 3.6 或更高版本
- 管理员权限

## 文件说明

- `VirtualIPSwitcher.py` - 主程序文件
- `RunVirtualIPSwitcher.bat` - 以管理员身份运行的批处理文件
- `virtual_ip_config.json` - 配置文件
- `logs/` - 日志文件目录

## 注意事项

- 需要管理员权限才能修改网络配置
- 使用前请确保网络配置参数正确
- 建议在切换IP前备份当前网络配置

## 开发

此项目使用Python的tkinter库开发图形界面，使用subprocess执行系统命令。

## 许可证

MIT License
