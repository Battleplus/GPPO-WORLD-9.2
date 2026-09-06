# S5 测试结果

- 受影响脚本：`tools/run_s5_minimal_reproduction.py`；`python -m py_compile` 通过。
- 工作区全套本地测试：`python -m pytest -q --basetemp <workspace>/.pytest-tmp-s5`，`98 passed in 5.19s`。
- 首次无 `--basetemp` 运行得到 `91 passed / 7 errors`，7 项均因系统临时目录 `C:\Users\ASUS\AppData\Local\Temp\pytest-of-ASUS` 权限拒绝，非测试断言失败；改用工作区隔离临时目录后全绿。
- S5 服务器新源归档 A 最小复现退出码 0；B 历史 EAWM 复现退出码 0。
- PPTX finalizer：10 页、包完整性 pass、首方导入 pass、布局 warning 0；PDF：10 页，Poppler 页面渲染可读。
