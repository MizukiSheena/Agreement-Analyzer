#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit Community Cloud 启动器（公开仓库）

作用：在运行时克隆你的“私有核心仓库”，安装依赖后导入并启动真正的应用。
这样可在公开仓库部署，同时保护私有仓库中的核心代码与提示词。

需要在 Streamlit Cloud 的 App Secrets 中配置：
  GH_PAT = <GitHub 只读 PAT，scope 至少 repo:read>
"""

import os
import sys
import subprocess
import tempfile
import pathlib
import streamlit as st


PRIVATE_REPO = "MizukiSheena/Agreement_Analyzer.git"  # 私有核心仓库（下划线版本）


def prepare_private_repo() -> str:
    token = st.secrets.get("GH_PAT", "")
    if not token:
        st.error("未检测到 GH_PAT。请在 Streamlit Secrets 中设置 GH_PAT（只读 PAT）。")
        st.stop()

    # 目标目录
    workdir = tempfile.mkdtemp(prefix="app_core_")

    # 克隆私有仓库
    repo_url = f"https://{token}@github.com/{PRIVATE_REPO}"
    with st.spinner("正在克隆核心仓库……"):
        subprocess.check_call(["git", "clone", "--depth", "1", repo_url, workdir])

    # 安装依赖
    # 可选：仅当你在 Secrets 中设置 INSTALL_PRIVATE_REQS="1" 时，才尝试安装私库 requirements
    if st.secrets.get("INSTALL_PRIVATE_REQS", "0") == "1":
        req = pathlib.Path(workdir, "requirements.txt")
        if req.exists():
            with st.spinner("正在安装依赖（可通过 Secrets 关闭）……"):
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--no-cache-dir",
                        "-r",
                        str(req),
                    ],
                    text=True,
                    capture_output=True,
                )
            if proc.returncode != 0:
                st.error("依赖安装失败：\n" + (proc.stderr or proc.stdout)[-4000:])
                raise subprocess.CalledProcessError(proc.returncode, proc.args)

    # 将私有仓库加入模块搜索路径，并切换目录（兼容相对路径）
    sys.path.insert(0, workdir)
    os.chdir(workdir)
    return workdir


def run_app():
    _ = prepare_private_repo()
    # 延迟导入核心应用
    from batch_web_interface import main, show_sidebar_info
    main()
    show_sidebar_info()


if __name__ == "__main__":
    st.set_page_config(page_title="Agreement Analyzer", page_icon="📚", layout="wide")
    try:
        run_app()
    except subprocess.CalledProcessError as e:
        st.error(f"启动失败：依赖安装或克隆仓库时出错。\n{e}")
        st.info("请确认 GH_PAT 有效且具备私有仓库读取权限（repo:read）。")
    except Exception as e:
        st.error(f"应用启动异常：{e}")


